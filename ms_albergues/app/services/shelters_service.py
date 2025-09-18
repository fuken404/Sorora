from bson import ObjectId
from fastapi import HTTPException
from ms_albergues.app.schemas.shelters_schema import Shelter, ShelterUpdate
from ms_albergues.app.db.database import shelters_colection

def serialize_shelter(shelter) -> dict:
    shelter["id"] = str(shelter["_id"])
    del shelter["_id"]
    return shelter
  
async def create_shelter(shelter: Shelter) -> dict:
    shelter_dict = shelter.model_dump()
    result = shelters_colection.insert_one(shelter_dict)
    new_shelter = shelters_colection.find_one({"_id": result.inserted_id})
    if new_shelter:
        return serialize_shelter(new_shelter)
    else:
        raise HTTPException(status_code=500, detail="Error al crear el albergue")
  
def get_shelter(shelter_id: str) -> dict:
    shelter = shelters_colection.find_one({"_id": ObjectId(shelter_id)})
    if shelter:
        return serialize_shelter(shelter)
    else:
        raise HTTPException(status_code=404, detail="Albergue no encontrado")

def get_all_shelters():
  return [serialize_shelter(shelter) for shelter in shelters_colection.find()]

async def update_shelter(shelter_id: str, shelter_update: ShelterUpdate):
  update_data = {k: v for k, v in shelter_update.model_dump().items() if v is not None}
  result = shelters_colection.update_one(
        {"_id": ObjectId(shelter_id)},
        {"$set": update_data}
    )
  if result.matched_count:
    return get_shelter(shelter_id)
  raise HTTPException(status_code=404, detail="Albergue no encontrado")

async def delete_shelter(shelter_id: str):
  result = shelters_colection.delete_one({"_id": ObjectId(shelter_id)})
  if result.deleted_count:
    return {"detail": "Albergue eliminado"}
  raise HTTPException(status_code=404, detail="Albergue no encontrado")