import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env en la raíz
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')

if not MONGO_URI:
  raise ValueError("MONGO_URI no está definido en el archivo .env")

client = MongoClient(MONGO_URI)
db = client["Sorora"] # Usa la base de datos por defecto del URI
shelters_colection = db["Shelters"]