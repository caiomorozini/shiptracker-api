from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_app_settings
from app.core import lifespan

def get_application() -> FastAPI:

    settings = get_app_settings()
    settings.configure_logging()

    application = FastAPI(
        on_startup=[lifespan.startup],
        on_shutdown=[lifespan.shutdown],
        **settings.fastapi_kwargs
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application


app = get_application()
