"""Almacenamiento de albergues y alertas: MongoDB en despliegue, memoria en desarrollo y pruebas."""

from typing import Protocol
from uuid import uuid4

from .schemas import Alert, Shelter, ShelterIn

# Datos inventados a propósito: la ubicación de un albergue real es información protegida.
DEMO_SHELTERS = [
    Shelter(id='casa-alba', name='Casa Alba', latitude=4.6486, longitude=-74.0628,
            occupancy=9, capacity=14, purpose='emergency'),
    Shelter(id='casa-lucia', name='Casa Lucía', latitude=4.7110, longitude=-74.0721,
            occupancy=20, capacity=24, purpose='transition'),
    Shelter(id='casa-violeta', name='Casa Violeta', latitude=4.5981, longitude=-74.0760,
            occupancy=12, capacity=12, purpose='emergency'),
    Shelter(id='red-candelaria', name='Red Candelaria', latitude=4.5700, longitude=-74.0920,
            occupancy=3, capacity=8, purpose='legal'),
    Shelter(id='casa-aurora', name='Casa Aurora', latitude=4.6300, longitude=-74.1500,
            occupancy=6, capacity=18, purpose='transition'),
]


def new_id() -> str:
    return uuid4().hex


class Store(Protocol):
    def list_shelters(self) -> list[Shelter]: ...
    def get_shelter(self, shelter_id: str) -> Shelter | None: ...
    def create_shelter(self, data: ShelterIn) -> Shelter: ...
    def replace_shelter(self, shelter: Shelter) -> None: ...
    def delete_shelter(self, shelter_id: str) -> bool: ...
    def add_alert(self, alert: Alert) -> None: ...


class MemoryStore:
    def __init__(self, shelters: list[Shelter] | None = None):
        self._shelters = {s.id: s.model_copy() for s in (DEMO_SHELTERS if shelters is None else shelters)}
        self.alerts: list[Alert] = []

    def list_shelters(self):
        return list(self._shelters.values())

    def get_shelter(self, shelter_id):
        return self._shelters.get(shelter_id)

    def create_shelter(self, data):
        shelter = Shelter(id=new_id(), **data.model_dump())
        self._shelters[shelter.id] = shelter
        return shelter

    def replace_shelter(self, shelter):
        self._shelters[shelter.id] = shelter

    def delete_shelter(self, shelter_id):
        return self._shelters.pop(shelter_id, None) is not None

    def add_alert(self, alert):
        self.alerts.append(alert)


class MongoStore:
    """Los _id son cadenas propias: un id con formato inválido es un 404 y no un error."""

    def __init__(self, database):
        self._shelters = database['shelters']
        self._alerts = database['alerts']

    @classmethod
    def connect(cls, uri: str, database: str) -> 'MongoStore':
        from pymongo import MongoClient

        # Un plazo corto: una base caída debe dar un error rápido, no colgar la función.
        return cls(MongoClient(uri, serverSelectionTimeoutMS=5000)[database])

    @staticmethod
    def _to_shelter(doc: dict) -> Shelter:
        return Shelter(id=doc['_id'], **{k: v for k, v in doc.items() if k != '_id'})

    def seed(self, shelters: list[Shelter]) -> None:
        """Carga los albergues de ejemplo solo si la colección está vacía."""
        if self._shelters.estimated_document_count():
            return
        for shelter in shelters:
            self._shelters.update_one(
                {'_id': shelter.id}, {'$setOnInsert': shelter.model_dump(exclude={'id'})}, upsert=True,
            )

    def list_shelters(self):
        return [self._to_shelter(d) for d in self._shelters.find().sort('name', 1)]

    def get_shelter(self, shelter_id):
        doc = self._shelters.find_one({'_id': shelter_id})
        return self._to_shelter(doc) if doc else None

    def create_shelter(self, data):
        shelter = Shelter(id=new_id(), **data.model_dump())
        self._shelters.insert_one({'_id': shelter.id, **data.model_dump()})
        return shelter

    def replace_shelter(self, shelter):
        self._shelters.replace_one({'_id': shelter.id}, shelter.model_dump(exclude={'id'}))

    def delete_shelter(self, shelter_id):
        return self._shelters.delete_one({'_id': shelter_id}).deleted_count > 0

    def add_alert(self, alert):
        self._alerts.insert_one({'_id': alert.id, **alert.model_dump(exclude={'id'})})
