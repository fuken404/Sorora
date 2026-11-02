"""Aviso de alertas por Telegram. El token va en la URL, así que nunca se registran URLs ni excepciones crudas."""

import logging
import time
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)  # httpx registra la URL completa en INFO


class Notifier(Protocol):
    def send(self, latitude: float, longitude: float) -> tuple[bool, int]:
        """Devuelve si el aviso llegó y cuántos intentos hizo."""
        ...


def alert_text(latitude: float, longitude: float) -> str:
    return f'¡ALERTA SOS!\nUbicación: https://www.google.com/maps?q={latitude},{longitude}'


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str, attempts: int = 3, timeout: float = 8, backoff: float = 1):
        self._url = f'https://api.telegram.org/bot{token}/sendMessage'
        self._chat_id = chat_id
        self._attempts = attempts
        self._timeout = timeout
        self._backoff = backoff

    def send(self, latitude, longitude):
        payload = {'chat_id': self._chat_id, 'text': alert_text(latitude, longitude)}
        for attempt in range(1, self._attempts + 1):
            try:
                response = httpx.post(self._url, json=payload, timeout=self._timeout)
                if response.is_success:
                    return True, attempt
                logger.warning('Telegram respondió %s (intento %s)', response.status_code, attempt)
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    return False, attempt  # Reintentar no arregla un token o un chat incorrectos.
            except httpx.HTTPError as error:
                logger.warning('Error de red con Telegram: %s (intento %s)', type(error).__name__, attempt)
            if attempt < self._attempts:
                time.sleep(self._backoff * attempt)
        return False, self._attempts
