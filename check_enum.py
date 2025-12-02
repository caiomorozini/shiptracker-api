import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT unnest(enum_range(NULL::userrole))::text"))
        values = [r[0] for r in result]
        print("UserRole enum values:", values)

asyncio.run(check())
