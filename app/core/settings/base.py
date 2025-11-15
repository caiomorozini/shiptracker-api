from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvTypes(Enum):
    prod = "prod"
    dev = "dev"
    test = "test"


class BaseAppSettings(BaseSettings):
    app_env: AppEnvTypes = AppEnvTypes.prod

    model_config = SettingsConfigDict(env_file=".env")
