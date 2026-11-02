from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Latitude = Field(ge=-90, le=90)
Longitude = Field(ge=-180, le=180)
Purpose = Literal['emergency', 'transition', 'legal']


class ShelterIn(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str = Field(min_length=1, max_length=120)
    latitude: float = Latitude
    longitude: float = Longitude
    occupancy: int = Field(ge=0)
    capacity: int = Field(gt=0)
    purpose: Purpose

    @model_validator(mode='after')
    def occupancy_fits(self) -> Self:
        if self.occupancy > self.capacity:
            raise ValueError('La ocupación no puede superar la capacidad.')
        return self


class ShelterUpdate(BaseModel):
    """Cambios parciales. La regla de ocupación se valida al combinarlos con el albergue."""

    model_config = ConfigDict(extra='forbid')

    name: str | None = Field(None, min_length=1, max_length=120)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    occupancy: int | None = Field(None, ge=0)
    capacity: int | None = Field(None, gt=0)
    purpose: Purpose | None = None


class Shelter(ShelterIn):
    id: str


class NearbyShelter(Shelter):
    distance_km: float


class AlertIn(BaseModel):
    model_config = ConfigDict(extra='forbid')

    latitude: float = Latitude
    longitude: float = Longitude


class Alert(BaseModel):
    id: str
    latitude: float
    longitude: float
    created_at: datetime
    status: Literal['sent', 'failed']
    attempts: int


class AlertResult(BaseModel):
    """Respuesta del SOS. `status` dice siempre qué ocurrió de verdad."""

    status: Literal['simulated', 'sent', 'failed']
    notified: bool
    message: str
    nearest: list[NearbyShelter]
