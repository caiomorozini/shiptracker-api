from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvTypes(Enum):
    prod = "prod"
    dev = "dev"
    test = "test"


class BaseAppSettings(BaseSettings):
    app_env: AppEnvTypes = AppEnvTypes.prod
    
    # Security: Control public user registration
    # Set to False in production to disable /api/auth/register endpoint
    allow_public_registration: bool = False

    model_config = SettingsConfigDict(env_file=".env")
