"""Check occurrence codes in database"""
import asyncio
from sqlalchemy import select, func
from app.db.conn import AsyncSessionLocal
from app.models.occurrence_code import OccurrenceCode


async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count()).select_from(OccurrenceCode))
        total = result.scalar()
        print(f"Total occurrence codes in database: {total}")
        
        if total > 0:
            # Show first 5
            result = await session.execute(select(OccurrenceCode).limit(5))
            codes = result.scalars().all()
            print("\nFirst 5 codes:")
            for code in codes:
                print(f"  {code.code}: {code.description}")


asyncio.run(check())
