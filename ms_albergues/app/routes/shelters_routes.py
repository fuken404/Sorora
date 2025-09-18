from fastapi import APIRouter, status, Path, Query
from typing import List
from ms_albergues.app.schemas.shelters_schema import Shelter, ShelterUpdate
from ms_albergues.app.services.shelters_service import (
    create_shelter,
    get_shelter,
    get_all_shelters,
    update_shelter,
    delete_shelter
)

router = APIRouter()

@router.post("/", 
    status_code=status.HTTP_201_CREATED,
    response_model=Shelter,
    summary="Crear nuevo albergue",
    description="Crea un nuevo albergue en el sistema con la información proporcionada.",
    response_description="El albergue ha sido creado exitosamente"
)
async def create_shelter_endpoint(
    shelter: Shelter = Path(
        ...,
        description="Datos del albergue a crear"
    )
):
    """
    Crea un nuevo albergue con la siguiente información:

    - **name**: Nombre del albergue
    - **address**: Dirección física
    - **capacity**: Capacidad máxima de personas
    - **phone**: Teléfono de contacto
    - **latitude**: Coordenada de latitud
    - **longitude**: Coordenada de longitud
    """
    return await create_shelter(shelter)

@router.get("/{shelter_id}",
    response_model=Shelter,
    summary="Obtener albergue por ID",
    description="Busca y retorna un albergue específico por su ID."
)
def get_shelter_endpoint(
    shelter_id: str = Path(
        ..., 
        description="ID único del albergue a buscar",
        example="507f1f77bcf86cd799439011"
    )
):
    """
    Busca un albergue por su ID y retorna sus detalles completos.

    - **shelter_id**: ID único del albergue (ObjectId de MongoDB)
    """
    return get_shelter(shelter_id)

@router.get("/",
    response_model=List[Shelter],
    summary="Listar todos los albergues",
    description="Obtiene una lista de todos los albergues disponibles en el sistema."
)
def get_all_shelters_endpoint():
    """
    Retorna una lista de todos los albergues registrados.
    Los resultados incluyen toda la información de cada albergue.
    """
    return get_all_shelters()

@router.put("/{shelter_id}")
async def update_shelter_endpoint(shelter_id: str, shelter: ShelterUpdate):
    return await update_shelter(shelter_id, shelter) 
  
@router.delete("/{shelter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shelter_endpoint(shelter_id: str):
    return await delete_shelter(shelter_id)
