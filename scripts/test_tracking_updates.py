"""
Test script for tracking updates API
"""
import asyncio
import json
from datetime import datetime
from sqlalchemy import select
from app.db.conn import AsyncSessionLocal
from app.models.shipment import Shipment, ShipmentTrackingEvent
from app.schemas.tracking_update import ShipmentTrackingUpdate, TrackingEventData


async def test_tracking_update():
    """Test creating/updating a shipment with tracking events"""
    
    # Sample data from HTML
    tracking_data = ShipmentTrackingUpdate(
        tracking_code="003504",
        invoice_number="1 003504",
        document="**.***.**9/0001-10",
        carrier="SSW",
        current_status="entregue",
        events=[
            TrackingEventData(
                occurrence_code="1",
                status="entregue",
                description="ENTREGA REALIZADA (SSWMOBILE) Comprovante registrado no SEFAZ-RJ - Protocolo: ********2205843 - 19/11/25 06:27 (cte.fazenda.gov.br)",
                location="RIO DE JANEIRO / RJ",
                unit="RIO DE JANEIRO / RJ",
                occurred_at=datetime(2025, 11, 18, 15, 53, 0),
                protocol="********2205843",
                raw_data='{"source": "SSW HTML"}'
            )
        ],
        last_update=datetime.now()
    )
    
    print("Testing tracking update...")
    print(f"Tracking Code: {tracking_data.tracking_code}")
    print(f"Invoice: {tracking_data.invoice_number}")
    print(f"Document: {tracking_data.document}")
    print(f"Events: {len(tracking_data.events)}")
    
    async with AsyncSessionLocal() as session:
        # Check if shipment exists
        query = select(Shipment).where(Shipment.invoice_number == tracking_data.invoice_number)
        result = await session.execute(query)
        shipment = result.scalar_one_or_none()
        
        if shipment:
            print(f"\n✓ Found existing shipment: {shipment.id}")
            print(f"  Status: {shipment.status}")
            print(f"  Tracking Code: {shipment.tracking_code}")
            
            # Get tracking events
            query = select(ShipmentTrackingEvent).where(
                ShipmentTrackingEvent.shipment_id == shipment.id
            ).order_by(ShipmentTrackingEvent.occurred_at.desc())
            result = await session.execute(query)
            events = result.scalars().all()
            
            print(f"\n  Tracking Events: {len(events)}")
            for event in events:
                print(f"    - {event.occurred_at}: {event.status}")
                print(f"      Code: {event.occurrence_code}")
                print(f"      Location: {event.location}")
                print(f"      Unit: {event.unit}")
                if event.protocol:
                    print(f"      Protocol: {event.protocol}")
        else:
            print("\n✗ Shipment not found")
            print("  You can create it via the API endpoint:")
            print(f"  POST /api/tracking-updates/shipment")
            print(f"\n  Payload:")
            print(json.dumps(tracking_data.model_dump(mode='json'), indent=2, default=str))


async def test_occurrence_codes():
    """Test occurrence codes are loaded"""
    from app.models.occurrence_code import OccurrenceCode
    
    async with AsyncSessionLocal() as session:
        query = select(OccurrenceCode).where(OccurrenceCode.code == "1")
        result = await session.execute(query)
        code = result.scalar_one_or_none()
        
        if code:
            print(f"\n✓ Occurrence code '1' found:")
            print(f"  Description: {code.description}")
            print(f"  Type: {code.type}")
            print(f"  Process: {code.process}")
        else:
            print("\n✗ Occurrence code '1' not found - run seed first!")


async def main():
    print("=" * 60)
    print("TRACKING UPDATES API TEST")
    print("=" * 60)
    
    await test_occurrence_codes()
    await test_tracking_update()
    
    print("\n" + "=" * 60)
    print("To test the API endpoints, use:")
    print("=" * 60)
    print("""
curl -X POST http://localhost:8000/api/tracking-updates/shipment \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "tracking_code": "003504",
    "invoice_number": "1 003504",
    "document": "**.***.**9/0001-10",
    "carrier": "SSW",
    "current_status": "entregue",
    "events": [{
      "occurrence_code": "1",
      "status": "entregue",
      "description": "MERCADORIA ENTREGUE",
      "location": "RIO DE JANEIRO / RJ",
      "unit": "RIO DE JANEIRO / RJ",
      "occurred_at": "2025-11-18T15:53:00",
      "protocol": "********2205843"
    }]
  }'
""")


if __name__ == "__main__":
    asyncio.run(main())
