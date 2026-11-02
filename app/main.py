import math
import os
import secrets
from datetime import datetime, timezone
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .config import Settings, get_settings
from .notifier import Notifier, TelegramNotifier
from .schemas import Alert, AlertIn, AlertResult, NearbyShelter, Shelter, ShelterIn, ShelterUpdate
from .store import DEMO_SHELTERS, MemoryStore, MongoStore, Store, new_id

NEAREST_LIMIT = 3

app = FastAPI(
    title='Sorora',
    description='Directorio de refugios y alerta SOS. En modo demo el SOS es una simulación: no avisa a nadie.',
    version='2.0.0',
    docs_url='/api/docs',
    redoc_url=None,
    openapi_url='/api/openapi.json',
)


@lru_cache
def get_store() -> Store:
    settings = get_settings()
    if settings.storage == 'memory':
        return MemoryStore()
    if not settings.mongo_uri:
        raise RuntimeError('Falta MONGO_URI (o usa STORAGE=memory para desarrollo).')
    store = MongoStore.connect(settings.mongo_uri, settings.mongo_db)
    store.seed(DEMO_SHELTERS)
    return store


def get_notifier(settings: Annotated[Settings, Depends(get_settings)]) -> Notifier | None:
    if not (settings.telegram_bot_token and settings.telegram_chat_id):
        return None
    return TelegramNotifier(
        settings.telegram_bot_token, settings.telegram_chat_id,
        settings.telegram_attempts, settings.telegram_timeout_seconds,
    )


StoreDep = Annotated[Store, Depends(get_store)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def check_key(given: str | None, expected: str) -> None:
    if not expected:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'Esta operación no está configurada.')
    if not given or not secrets.compare_digest(given, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Llave inválida.')


def require_admin(settings: SettingsDep, x_admin_key: Annotated[str | None, Header()] = None) -> None:
    check_key(x_admin_key, settings.admin_api_key)


def distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia sobre la superficie terrestre (fórmula del semiverseno)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def by_distance(shelters: list[Shelter], latitude: float, longitude: float) -> list[NearbyShelter]:
    nearby = [
        NearbyShelter(**s.model_dump(), distance_km=round(distance_km(latitude, longitude, s.latitude, s.longitude), 1))
        for s in shelters
    ]
    return sorted(nearby, key=lambda s: s.distance_km)


def nearest_with_room(store: Store, latitude: float, longitude: float) -> list[NearbyShelter]:
    ordered = by_distance(store.list_shelters(), latitude, longitude)
    return [s for s in ordered if s.occupancy < s.capacity][:NEAREST_LIMIT]


@app.get('/api/health', tags=['sistema'])
def health():
    return {'status': 'ok'}


@app.get('/api/config', tags=['sistema'])
def config(settings: SettingsDep):
    return {'mode': settings.mode}


@app.get('/api/shelters', response_model=list[Shelter] | list[NearbyShelter], tags=['albergues'])
def list_shelters(
    store: StoreDep,
    lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    lng: Annotated[float | None, Query(ge=-180, le=180)] = None,
):
    shelters = store.list_shelters()
    if lat is None or lng is None:
        return shelters
    return by_distance(shelters, lat, lng)


@app.get('/api/shelters/{shelter_id}', response_model=Shelter, tags=['albergues'])
def get_shelter(shelter_id: str, store: StoreDep):
    shelter = store.get_shelter(shelter_id)
    if shelter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Albergue no encontrado.')
    return shelter


@app.post('/api/shelters', status_code=status.HTTP_201_CREATED, response_model=Shelter,
          dependencies=[Depends(require_admin)], tags=['albergues'])
def create_shelter(data: ShelterIn, store: StoreDep):
    return store.create_shelter(data)


@app.patch('/api/shelters/{shelter_id}', response_model=Shelter,
           dependencies=[Depends(require_admin)], tags=['albergues'])
def update_shelter(shelter_id: str, changes: ShelterUpdate, store: StoreDep):
    shelter = store.get_shelter(shelter_id)
    if shelter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Albergue no encontrado.')
    merged = {**shelter.model_dump(), **changes.model_dump(exclude_none=True)}
    try:
        updated = Shelter(**merged)
    except ValidationError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, error.errors()[0]['msg']) from error
    store.replace_shelter(updated)
    return updated


@app.delete('/api/shelters/{shelter_id}', status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[Depends(require_admin)], tags=['albergues'])
def delete_shelter(shelter_id: str, store: StoreDep):
    if not store.delete_shelter(shelter_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Albergue no encontrado.')
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post('/api/alerts', status_code=status.HTTP_201_CREATED, response_model=AlertResult,
          responses={502: {'model': AlertResult}}, tags=['alertas'])
def create_alert(
    data: AlertIn,
    store: StoreDep,
    settings: SettingsDep,
    notifier: Annotated[Notifier | None, Depends(get_notifier)],
    x_alert_key: Annotated[str | None, Header()] = None,
):
    """En modo demo no guarda nada ni avisa a nadie. En modo live, el estado dice si el aviso llegó."""
    if settings.mode == 'demo':
        return AlertResult(
            status='simulated', notified=False,
            message='Simulación: no se guardó la ubicación ni se avisó a nadie.',
            nearest=nearest_with_room(store, data.latitude, data.longitude),
        )

    check_key(x_alert_key, settings.alert_api_key)
    if notifier is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'El aviso por Telegram no está configurado.')

    delivered, attempts = notifier.send(data.latitude, data.longitude)
    store.add_alert(Alert(
        id=new_id(), latitude=data.latitude, longitude=data.longitude,
        created_at=datetime.now(timezone.utc), status='sent' if delivered else 'failed', attempts=attempts,
    ))
    nearest = nearest_with_room(store, data.latitude, data.longitude)
    if delivered:
        return AlertResult(status='sent', notified=True, message='Aviso entregado.', nearest=nearest)
    result = AlertResult(status='failed', notified=False, message='No se pudo avisar. Llama al 123.', nearest=nearest)
    return JSONResponse(result.model_dump(), status_code=status.HTTP_502_BAD_GATEWAY)


# En Vercel el panel (public/) se sirve desde la CDN. En local lo servimos aquí.
if not os.getenv('VERCEL'):
    from fastapi.staticfiles import StaticFiles

    app.mount('/', StaticFiles(directory='public', html=True), name='panel')
