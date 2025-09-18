from fastapi import APIRouter, status, Body
from ms_alertas.app.schemas.alerts_schema import LocationCoordinates, AlertResponse
from ms_alertas.app.services.alerts_services import create_alert

router = APIRouter()

@router.post("/", 
    status_code=status.HTTP_201_CREATED,
    response_model=AlertResponse,
    summary="Crear alerta SOS",
    description="Crea una nueva alerta de emergencia con la ubicación proporcionada.",
    response_description="La alerta ha sido creada y enviada exitosamente"
)
async def create_alert_endpoint(
    location: LocationCoordinates = Body(
        ...,
        description="Coordenadas de la ubicación donde se genera la alerta",
        example={
            "latitude": 4.7110,
            "longitude": -74.0721
        }
    )
):
    """
    Crea una alerta SOS con las coordenadas proporcionadas:

    - **latitude**: Latitud de la ubicación (número decimal)
    - **longitude**: Longitud de la ubicación (número decimal)

    La alerta será:
    1. Registrada en la base de datos
    2. Enviada a servicios de emergencia
    3. Notificada a contactos de emergencia configurados
    """
    return await create_alert(location)