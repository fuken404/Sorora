from pydantic import BaseModel, Field
from typing import Optional

class Shelter(BaseModel):
  name: str = Field(..., min_length=1, description="Name of the shelter")
  latitude: float = Field(..., description="Latitude of the location")
  longitude: float = Field(..., description="Longitude of the location")
  ocupancy: int = Field(..., description="Current occupancy of the shelter")
  capacity: int = Field(..., description="Maximum capacity of the shelter")
  purpose: str = Field(..., min_length=1, description="Type of shelter")
  
class ShelterUpdate(BaseModel):
  name: Optional[str] = Field(None, min_length=1, description="Name of the shelter")
  latitude: Optional[float] = Field(None, description="Latitude of the location")
  longitude: Optional[float] = Field(None, description="Longitude of the location")
  ocupancy: Optional[int] = Field(None, description="Current occupancy of the shelter")
  capacity: Optional[int] = Field(None, description="Maximum capacity of the shelter")
  purpose: Optional[str] = Field(None, min_length=1, description="Type of shelter")