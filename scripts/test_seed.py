"""
Test script to verify occurrence codes seeding
"""
import asyncio
from sqlalchemy import select, func
from app.db.conn import AsyncSessionLocal
from app.models.occurrence_code import OccurrenceCode
from app.core.seed import seed_occurrence_codes


async def test_seed():
    """Test the occurrence codes seeding"""
    async with AsyncSessionLocal() as session:
        # Check before seeding
        result = await session.execute(select(func.count()).select_from(OccurrenceCode))
        count_before = result.scalar()
        print(f"Occurrence codes before seeding: {count_before}")
        
        # Run seed
        await seed_occurrence_codes(session)
        
        # Check after seeding
        result = await session.execute(select(func.count()).select_from(OccurrenceCode))
        count_after = result.scalar()
        print(f"Occurrence codes after seeding: {count_after}")
        
        # List some codes
        result = await session.execute(select(OccurrenceCode).limit(5))
        codes = result.scalars().all()
        
        print("\nFirst 5 codes:")
        for code in codes:
            print(f"  {code.code}: {code.description} ({code.type} - {code.process})")


if __name__ == "__main__":
    asyncio.run(test_seed())
