from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class LocationCoordinates(BaseModel):
    latitude: float = Field(..., description="Latitud de la ubicación", example=4.7110)
    longitude: float = Field(..., description="Longitud de la ubicación", example=-74.0721)

class AlertResponse(BaseModel):
    id: str = Field(..., description="ID único de la alerta")
    latitude: float = Field(..., description="Latitud donde se generó la alerta")
    longitude: float = Field(..., description="Longitud donde se generó la alerta")
    created_at: datetime = Field(default_factory=datetime.now, description="Fecha y hora de la alerta")
    status: str = Field(default="active", description="Estado actual de la alerta")
    processed: bool = Field(default=False, description="Indica si la alerta ha sido procesada")
    emergency_contacts_notified: bool = Field(default=False, description="Indica si se notificó a contactos de emergencia")
    message: Optional[str] = Field(None, description="Mensaje adicional o detalles de la alerta")