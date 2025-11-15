import logging
import sys
from typing import Any, Dict, List, Tuple
from loguru import logger
from pydantic import PostgresDsn, SecretStr
from app.core.log import InterceptHandler
from app.core.settings.base import BaseAppSettings
from pydantic_settings import SettingsConfigDict

class AppSettings(BaseAppSettings):
    debug: bool = False
    docs_url: str = "/docs"
    openapi_prefix: str = ""
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    title: str = "ShipTracker API"
    version: str = "0.1.0"
    description: str = "API para rastreamento e gestão de encomendas"

    # PostgreSQL
    database_hostname: str
    database_port: str
    database_name: str
    database_password: str
    database_username: str

    # MongoDB
    mongo_hostname: str = "localhost"
    mongo_port: int = 27017
    mongo_database: str = "shiptracker_dev"
    mongo_username: str = ""
    mongo_password: str = ""

    # Redis
    redis_hostname: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    # Initial user (optional)
    first_login: str = ""
    first_password: str = ""
    first_email: str = ""

    database_url: PostgresDsn | None = None
    max_connection_count: int = 10
    min_connection_count: int = 10

    secret_key: SecretStr
    
    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    api_prefix: str = "/api"
    jwt_token_prefix: str = "Bearer"

    allowed_hosts: List[str] = ["*"]

    logging_level: int = logging.INFO
    loggers: Tuple[str, str] = ("uvicorn.asgi", "uvicorn.access")

    model_config = SettingsConfigDict(validate_assignment=True)

    @property
    def fastapi_kwargs(self) -> Dict[str, Any]:
        return {
            "debug": self.debug,
            "docs_url": self.docs_url,
            "openapi_prefix": self.openapi_prefix,
            "openapi_url": self.openapi_url,
            "redoc_url": self.redoc_url,
            "title": self.title,
            "version": self.version,
            "description": self.description,
        }

    def configure_logging(self) -> None:
        logging.getLogger().handlers = [InterceptHandler()]
        for logger_name in self.loggers:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers = [InterceptHandler(level=self.logging_level)]

        logger.configure(handlers=[{"sink": sys.stderr, "level": self.logging_level}])

