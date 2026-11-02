import httpx
import mongomock
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app, get_notifier, get_store
from app.notifier import TelegramNotifier
from app.schemas import ShelterIn
from app.store import DEMO_SHELTERS, MemoryStore, MongoStore

ADMIN = {'X-Admin-Key': 'llave-admin'}
ALERT = {'X-Alert-Key': 'llave-alerta'}
POINT = {'latitude': 4.65, 'longitude': -74.06}
NEW = {'name': 'Casa Nueva', 'latitude': 4.6, 'longitude': -74.1, 'occupancy': 1, 'capacity': 5, 'purpose': 'legal'}


class FakeNotifier:
    def __init__(self, delivered=True):
        self.delivered = delivered
        self.calls = 0

    def send(self, latitude, longitude):
        self.calls += 1
        return self.delivered, 1


@pytest.fixture
def make_client():
    def build(mode='demo', notifier=None, **overrides):
        store = MemoryStore()
        settings = Settings(_env_file=None, mode=mode, storage='memory', admin_api_key='llave-admin',
                            alert_api_key='llave-alerta', **overrides)
        app.dependency_overrides[get_store] = lambda: store
        app.dependency_overrides[get_settings] = lambda: settings
        app.dependency_overrides[get_notifier] = lambda: notifier
        client = TestClient(app, raise_server_exceptions=False)
        client.store = store
        return client

    yield build
    app.dependency_overrides.clear()


def test_salud_y_modo_por_defecto_es_demo(make_client):
    assert Settings(_env_file=None).mode == 'demo'
    client = make_client()
    assert client.get('/api/health').json() == {'status': 'ok'}
    assert client.get('/api/config').json() == {'mode': 'demo'}


def test_demo_no_guarda_ni_avisa_y_lo_dice(make_client):
    notifier = FakeNotifier()
    client = make_client(notifier=notifier)
    response = client.post('/api/alerts', json=POINT, headers={})
    assert response.status_code == 201
    data = response.json()
    assert data['status'] == 'simulated' and data['notified'] is False
    assert client.store.alerts == [] and notifier.calls == 0


def test_cercanos_tienen_cupo_y_van_por_distancia(make_client):
    nearest = make_client().post('/api/alerts', json={'latitude': 4.598, 'longitude': -74.076}).json()['nearest']
    assert 'casa-violeta' not in [s['id'] for s in nearest]  # está llena
    assert nearest[0]['id'] == 'red-candelaria'
    assert [s['distance_km'] for s in nearest] == sorted(s['distance_km'] for s in nearest)


def test_coordenadas_invalidas(make_client):
    assert make_client().post('/api/alerts', json={'latitude': 200, 'longitude': 0}).status_code == 422


def test_live_exige_llave(make_client):
    client = make_client(mode='live', notifier=FakeNotifier())
    assert client.post('/api/alerts', json=POINT).status_code == 401
    assert client.store.alerts == []


def test_live_sin_telegram_no_finge_envio(make_client):
    client = make_client(mode='live', notifier=None)
    assert client.post('/api/alerts', json=POINT, headers=ALERT).status_code == 503


def test_live_entregada(make_client):
    client = make_client(mode='live', notifier=FakeNotifier())
    data = client.post('/api/alerts', json=POINT, headers=ALERT).json()
    assert data['status'] == 'sent' and data['notified'] is True
    assert client.store.alerts[0].status == 'sent'


def test_live_fallida_lo_reporta(make_client):
    client = make_client(mode='live', notifier=FakeNotifier(delivered=False))
    response = client.post('/api/alerts', json=POINT, headers=ALERT)
    assert response.status_code == 502
    assert response.json()['notified'] is False and response.json()['status'] == 'failed'
    assert client.store.alerts[0].status == 'failed'


def test_listar_albergues_con_distancia(make_client):
    client = make_client()
    assert 'distance_km' not in client.get('/api/shelters').json()[0]
    rows = client.get('/api/shelters', params={'lat': 4.65, 'lng': -74.06}).json()
    assert rows[0]['id'] == 'casa-alba' and rows[0]['distance_km'] < 1


def test_albergue_inexistente_es_404(make_client):
    assert make_client().get('/api/shelters/no-existe').status_code == 404


@pytest.mark.parametrize('method,path,body', [
    ('post', '/api/shelters', NEW),
    ('patch', '/api/shelters/casa-alba', {'name': 'X'}),
    ('delete', '/api/shelters/casa-alba', None),
])
def test_escribir_exige_llave(make_client, method, path, body):
    client = make_client()
    kwargs = {'json': body} if body else {}
    assert client.request(method, path, **kwargs).status_code == 401
    assert client.request(method, path, headers={'X-Admin-Key': 'mala'}, **kwargs).status_code == 401


def test_escribir_sin_llave_configurada_esta_cerrado(make_client):
    client = make_client()
    client.app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, storage='memory')
    assert client.post('/api/shelters', json=NEW, headers=ADMIN).status_code == 503


def test_crear_editar_y_borrar(make_client):
    client = make_client()
    created = client.post('/api/shelters', json=NEW, headers=ADMIN)
    assert created.status_code == 201
    shelter_id = created.json()['id']
    assert client.patch(f'/api/shelters/{shelter_id}', json={'occupancy': 4}, headers=ADMIN).json()['occupancy'] == 4
    assert client.delete(f'/api/shelters/{shelter_id}', headers=ADMIN).status_code == 204
    assert client.get(f'/api/shelters/{shelter_id}').status_code == 404
    assert client.delete(f'/api/shelters/{shelter_id}', headers=ADMIN).status_code == 404


def test_ocupacion_no_supera_capacidad(make_client):
    client = make_client()
    assert client.post('/api/shelters', json={**NEW, 'occupancy': 9}, headers=ADMIN).status_code == 422
    assert client.patch('/api/shelters/casa-alba', json={'occupancy': 999}, headers=ADMIN).status_code == 422
    assert client.get('/api/shelters/casa-alba').json()['occupancy'] == 9


# ── MongoStore ───────────────────────────────────────────

@pytest.fixture
def mongo():
    store = MongoStore(mongomock.MongoClient()['sorora'])
    store.seed(DEMO_SHELTERS)
    return store


def test_mongo_siembra_una_sola_vez_y_respeta_cambios(mongo):
    assert len(mongo.list_shelters()) == len(DEMO_SHELTERS)
    mongo.delete_shelter('casa-alba')
    mongo.seed(DEMO_SHELTERS)
    assert mongo.get_shelter('casa-alba') is None


def test_mongo_ciclo_completo(mongo):
    shelter = mongo.create_shelter(ShelterIn(**NEW))
    assert mongo.get_shelter(shelter.id) == shelter
    mongo.replace_shelter(shelter.model_copy(update={'occupancy': 2}))
    assert mongo.get_shelter(shelter.id).occupancy == 2
    assert mongo.delete_shelter(shelter.id) is True
    assert mongo.delete_shelter(shelter.id) is False
    assert mongo.get_shelter('formato-cualquiera') is None


# ── Telegram ─────────────────────────────────────────────

TOKEN = '123456:token-secreto'


def telegram(monkeypatch, outcomes):
    calls = []

    def fake_post(url, json, timeout):
        calls.append(json)
        outcome = outcomes[len(calls) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return httpx.Response(outcome, request=httpx.Request('POST', url))

    monkeypatch.setattr('app.notifier.httpx.post', fake_post)
    return TelegramNotifier(TOKEN, '42', attempts=3, backoff=0), calls


def test_telegram_reintenta_y_entrega(monkeypatch):
    notifier, calls = telegram(monkeypatch, [httpx.ConnectError('x'), 500, 200])
    assert notifier.send(4.65, -74.06) == (True, 3)
    assert calls[0]['chat_id'] == '42' and '4.65,-74.06' in calls[0]['text']


def test_telegram_no_reintenta_error_del_cliente(monkeypatch):
    notifier, calls = telegram(monkeypatch, [401])
    assert notifier.send(4.65, -74.06) == (False, 1)
    assert len(calls) == 1


def test_telegram_agota_intentos_sin_filtrar_el_token(monkeypatch, caplog):
    notifier, _ = telegram(monkeypatch, [httpx.ConnectError(f'bot{TOKEN}'), 429, 503])
    with caplog.at_level('DEBUG'):
        assert notifier.send(4.65, -74.06) == (False, 3)
    assert 'token-secreto' not in caplog.text
