from typing import Callable
from app.api.dependencies.s3 import get_s3_resource

from fastapi import FastAPI
from loguru import logger
from sqlalchemy import text
from app.core.settings.app import AppSettings
from app.db.conn import engine
from app.db import mongo
from app.models.base import Base
import boto3
from app.core.config import get_app_settings
settings = get_app_settings()

SCHEMAS = ["data"]
async def startup():
    # Inicializa PostgreSQL
    async with engine.begin() as conn:
        for schema in SCHEMAS:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))
        await conn.run_sync(Base.metadata.create_all)

async def shutdown():
    await engine.dispose()
    await mongo.close_mongo_connection()
