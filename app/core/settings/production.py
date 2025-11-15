from app.core.settings.app import AppSettings
from pydantic_settings import SettingsConfigDict

class ProdAppSettings(AppSettings):
    model_config = SettingsConfigDict(env_file=".env.production")
