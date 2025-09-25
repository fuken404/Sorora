
def serialize_alert(alert) -> dict:
    """Convierte un documento de alerta de MongoDB a un diccionario serializable."""
    alert["id"] = str(alert["_id"])