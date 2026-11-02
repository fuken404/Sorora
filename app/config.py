from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración por variables de entorno (ver .env.example)."""

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # 'demo' nunca guarda ubicaciones ni avisa a nadie: es el modo seguro por defecto.
    mode: Literal['demo', 'live'] = 'demo'

    storage: Literal['mongo', 'memory'] = 'mongo'
    mongo_uri: str = ''
    mongo_db: str = 'sorora'

    admin_api_key: str = ''

    alert_api_key: str = ''
    telegram_bot_token: str = ''
    telegram_chat_id: str = ''
    telegram_attempts: int = 3
    telegram_timeout_seconds: float = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
