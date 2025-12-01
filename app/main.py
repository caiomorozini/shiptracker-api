from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import get_app_settings
from app.core import lifespan
from app.api.routes import auth, users, clients, shipments, occurrence_codes, tracking_updates, carriers, feedback

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

    # Register routers
    application.include_router(auth.router, prefix="/api")
    application.include_router(users.router, prefix="/api")
    application.include_router(clients.router, prefix="/api")
    application.include_router(shipments.router, prefix="/api")
    application.include_router(occurrence_codes.router, prefix="/api")
    application.include_router(tracking_updates.router, prefix="/api")
    application.include_router(carriers.router, prefix="/api")
    application.include_router(feedback.router, prefix="/api")

    # Configure OpenAPI schema for Swagger authentication
    def custom_openapi():
        if application.openapi_schema:
            return application.openapi_schema

        openapi_schema = get_openapi(
            title=settings.title,
            version=settings.version,
            description=settings.description,
            routes=application.routes,
        )

        # Add security scheme
        openapi_schema["components"]["securitySchemes"] = {
            "OAuth2PasswordBearer": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": "/api/auth/login",
                        "scopes": {}
                    }
                }
            }
        }

        application.openapi_schema = openapi_schema
        return application.openapi_schema

    application.openapi = custom_openapi

    return application


app = get_application()
