import logging
from app.core.settings.app import AppSettings
from pydantic_settings import SettingsConfigDict

class DevAppSettings(AppSettings):
    debug: bool = True

    title: str = "Shiptracker API - Desenvolvimento"
    version: str = "0.1-dev"
    description: str = "Microserviço de gerenciamento de captura e processamento de dados. Ambiente de desenvolvimento."

    logging_level: int = logging.DEBUG

    model_config = SettingsConfigDict(env_file=".env.dev")
