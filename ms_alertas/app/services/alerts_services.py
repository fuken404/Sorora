from ..schemas.alerts_schema import LocationCoordinates
from ..db.database import alerts_colection
from fastapi import HTTPException
from bson import ObjectId
import requests
from ..config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import json

def serialize_alert(alert) -> dict:
    """Convierte un documento de alerta de MongoDB a un diccionario serializable."""
    alert["id"] = str(alert["_id"])
    del alert["_id"]
    return alert

def send_telegram_alert(latitude: float, longitude: float):
    """Envía una alerta por Telegram con la ubicación."""
    try:
        # Validación de configuración
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print(f"Error: Token={TELEGRAM_BOT_TOKEN}, Chat ID={TELEGRAM_CHAT_ID}")
            return False

        # URL base de la API de Telegram
        base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        
        # Primero, verificar que el bot está funcionando
        print("Verificando estado del bot...")
        test_response = requests.get(f"{base_url}/getMe")
        if not test_response.ok:
            print(f"Error al verificar el bot: {test_response.text}")
            return False
        print(f"Bot verificado: {test_response.json()}")

        # Obtener actualizaciones del bot para verificar si el usuario ha interactuado
        print("Verificando actualizaciones del bot...")
        updates_response = requests.get(f"{base_url}/getUpdates")
        if not updates_response.ok:
            print(f"Error al obtener actualizaciones: {updates_response.text}")
            return False
            
        updates = updates_response.json()
        print(f"Actualizaciones: {updates}")
        
        if not updates.get('ok') or not updates.get('result'):
            print("No hay actualizaciones disponibles o el usuario no ha iniciado el bot")
            return False

        # Crear el mensaje con el enlace de Google Maps
        google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        message = f"¡ALERTA SOS!\nUbicación: {google_maps_link}"
        
        # Intentar enviar el mensaje usando el chat_id sin modificar
        user_id = TELEGRAM_CHAT_ID
        message_data = {
            "chat_id": user_id,
            "text": message
        }
        
        print(f"Intentando enviar mensaje a: {base_url}/sendMessage")
        print(f"Datos a enviar: {message_data}")
        
        response = requests.post(
            f"{base_url}/sendMessage",
            json=message_data,
            verify=False
        )
        
        # Si falla, intentar con formato alternativo
        if not response.ok:
            print("Primer intento fallido, probando formato alternativo...")
            message_data["chat_id"] = f"@{user_id}"
            response = requests.post(
                f"{base_url}/sendMessage",
                json=message_data,
                verify=False
            )
        
        # Verificar respuesta final
        print(f"Respuesta del servidor: {response.status_code} - {response.text}")
        if not response.ok:
            print(f"Error al enviar mensaje de texto: {response.text}")
            return False

        # Enviar ubicación
        response = requests.post(
            f"{base_url}/sendLocation",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "latitude": latitude,
                "longitude": longitude
            },
            verify=False
        )
        
        # Verificar respuesta de la ubicación
        if not response.ok:
            print(f"Error al enviar ubicación: {response.text}")
            return False
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error de red al enviar mensaje: {str(e)}")
        return False
    except Exception as e:
        print(f"Error inesperado al enviar mensaje: {str(e)}")
        return False

async def create_alert(alert: LocationCoordinates):
    """Crea una nueva alerta en la base de datos y envía mensaje por Telegram."""
    try:
        # Guardar en la base de datos
        alert_dict = alert.model_dump()
        result = alerts_colection.insert_one(alert_dict)
        new_alert = alerts_colection.find_one({"_id": result.inserted_id})
        
        if new_alert:
            # Enviar alerta por Telegram
            send_telegram_alert(alert.latitude, alert.longitude)
            return serialize_alert(new_alert)
            
        raise HTTPException(status_code=500, detail="Error al crear la alerta")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))