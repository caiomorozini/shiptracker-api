"""
Tests for tracking updates endpoint and status logic
Run with: pytest tests/test_tracking_updates.py -v
"""
import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.shipment import Shipment, ShipmentTrackingEvent
from app.models.occurrence_code import OccurrenceCode


@pytest.mark.asyncio
async def test_occurrence_codes_endpoint(client: AsyncClient, test_db, api_key_headers):
    """Test occurrence codes endpoint"""
    # Seed some occurrence codes
    async with test_db() as session:
        codes = [
            OccurrenceCode(
                code="1",
                description="mercadoria entregue",
                type="entrega",
                process="entrega"
            ),
            OccurrenceCode(
                code="85",
                description="saida para entrega",
                type="informativa",
                process="operacional"
            ),
        ]
        session.add_all(codes)
        await session.commit()
    
    # Get occurrence codes
    response = await client.get(
        "/api/v1/tracking-updates/occurrence-codes",
        headers=api_key_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    
    # Validate structure
    for code in data:
        assert "code" in code
        assert "description" in code
        assert "type" in code
        assert "process" in code


@pytest.mark.asyncio
async def test_create_shipment_with_tracking_events(client: AsyncClient, test_db, api_key_headers):
    """Test creating shipment with tracking events"""
    payload = {
        "tracking_code": None,
        "invoice_number": "NF-12345",
        "document": "12345678000199",
        "carrier": "SSW",
        "current_status": "in_transit",
        "events": [
            {
                "occurrence_code": "80",
                "status": "in_transit",
                "description": "mercadoria recebida para transporte",
                "location": "RIO DE JANEIRO RJ",
                "unit": "1234",
                "occurred_at": "2025-11-20T10:30:00"
            }
        ],
        "last_update": datetime.now().isoformat()
    }
    
    response = await client.post(
        "/api/v1/tracking-updates/shipment",
        json=payload,
        headers=api_key_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["events_created"] == 1
    assert data["shipment_id"] is not None
    
    # Verify in database
    async with test_db() as session:
        query = select(Shipment).where(Shipment.invoice_number == "NF-12345")
        result = await session.execute(query)
        shipment = result.scalar_one_or_none()
        
        assert shipment is not None
        assert shipment.status == "in_transit"
        assert shipment.carrier == "SSW"


@pytest.mark.asyncio
async def test_finalization_with_entrega_type(client: AsyncClient, test_db, api_key_headers):
    """Test that shipment is marked as delivered when event has type='entrega'"""
    # Seed occurrence code
    async with test_db() as session:
        code = OccurrenceCode(
            code="1",
            description="mercadoria entregue",
            type="entrega",
            process="entrega"
        )
        session.add(code)
        await session.commit()
    
    payload = {
        "invoice_number": "NF-DELIVERED",
        "document": "12345678000199",
        "carrier": "SSW",
        "current_status": "in_transit",
        "events": [
            {
                "occurrence_code": "1",
                "status": "delivered",
                "description": "mercadoria entregue",
                "location": "SAO PAULO SP",
                "unit": "5678",
                "occurred_at": "2025-11-21T16:30:00"
            }
        ]
    }
    
    response = await client.post(
        "/api/v1/tracking-updates/shipment",
        json=payload,
        headers=api_key_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify shipment status is delivered
    async with test_db() as session:
        query = select(Shipment).where(Shipment.invoice_number == "NF-DELIVERED")
        result = await session.execute(query)
        shipment = result.scalar_one_or_none()
        
        assert shipment is not None
        assert shipment.status == "delivered", "Shipment should be marked as delivered"


@pytest.mark.asyncio
async def test_finalization_with_baixa_type(client: AsyncClient, test_db, api_key_headers):
    """Test that shipment is finalized when event has type='baixa'"""
    # Seed occurrence code
    async with test_db() as session:
        code = OccurrenceCode(
            code="99",
            description="ctrc baixado/cancelado",
            type="baixa",
            process="geral"
        )
        session.add(code)
        await session.commit()
    
    payload = {
        "invoice_number": "NF-CANCELLED",
        "document": "12345678000199",
        "carrier": "SSW",
        "current_status": "in_transit",
        "events": [
            {
                "occurrence_code": "99",
                "status": "cancelled",
                "description": "ctrc baixado/cancelado",
                "location": "RIO DE JANEIRO RJ",
                "unit": "1234",
                "occurred_at": "2025-11-20T10:30:00"
            }
        ]
    }
    
    response = await client.post(
        "/api/v1/tracking-updates/shipment",
        json=payload,
        headers=api_key_headers
    )
    
    assert response.status_code == 200
    
    # Verify shipment status is delivered (finalized)
    async with test_db() as session:
        query = select(Shipment).where(Shipment.invoice_number == "NF-CANCELLED")
        result = await session.execute(query)
        shipment = result.scalar_one_or_none()
        
        assert shipment is not None
        assert shipment.status == "delivered", "Shipment with 'baixa' type should be marked as delivered"


@pytest.mark.asyncio
async def test_no_finalization_with_informativa_type(client: AsyncClient, test_db, api_key_headers):
    """Test that shipment is NOT finalized with type='informativa'"""
    # Seed occurrence code
    async with test_db() as session:
        code = OccurrenceCode(
            code="85",
            description="saida para entrega",
            type="informativa",
            process="operacional"
        )
        session.add(code)
        await session.commit()
    
    payload = {
        "invoice_number": "NF-INFORMATIVE",
        "document": "12345678000199",
        "carrier": "SSW",
        "current_status": "in_transit",
        "events": [
            {
                "occurrence_code": "85",
                "status": "in_transit",
                "description": "saida para entrega",
                "location": "RIO DE JANEIRO RJ",
                "unit": "1234",
                "occurred_at": "2025-11-20T10:30:00"
            }
        ]
    }
    
    response = await client.post(
        "/api/v1/tracking-updates/shipment",
        json=payload,
        headers=api_key_headers
    )
    
    assert response.status_code == 200
    
    # Verify shipment status is NOT delivered
    async with test_db() as session:
        query = select(Shipment).where(Shipment.invoice_number == "NF-INFORMATIVE")
        result = await session.execute(query)
        shipment = result.scalar_one_or_none()
        
        assert shipment is not None
        assert shipment.status == "in_transit", "Shipment with 'informativa' should NOT be marked as delivered"


@pytest.mark.asyncio
async def test_update_existing_shipment(client: AsyncClient, test_db, api_key_headers):
    """Test updating existing shipment with new events"""
    # Create initial shipment
    payload1 = {
        "invoice_number": "NF-UPDATE",
        "document": "12345678000199",
        "carrier": "SSW",
        "current_status": "pending",
        "events": [
            {
                "occurrence_code": "80",
                "status": "in_transit",
                "description": "mercadoria recebida",
                "location": "RIO DE JANEIRO RJ",
                "unit": "1234",
                "occurred_at": "2025-11-20T10:00:00"
            }
        ]
    }
    
    response1 = await client.post(
        "/api/v1/tracking-updates/shipment",
        json=payload1,
        headers=api_key_headers
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["events_created"] == 1
    
    # Update with new event
    payload2 = {
        "invoice_number": "NF-UPDATE",
        "document": "12345678000199",
        "carrier": "SSW",
        "current_status": "in_transit",
        "events": [
            {
                "occurrence_code": "80",
                "status": "in_transit",
                "description": "mercadoria recebida",
                "location": "RIO DE JANEIRO RJ",
                "unit": "1234",
                "occurred_at": "2025-11-20T10:00:00"
            },
            {
                "occurrence_code": "85",
                "status": "in_transit",
                "description": "saida para entrega",
                "location": "SAO PAULO SP",
                "unit": "5678",
                "occurred_at": "2025-11-21T14:00:00"
            }
        ]
    }
    
    response2 = await client.post(
        "/api/v1/tracking-updates/shipment",
        json=payload2,
        headers=api_key_headers
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["events_created"] == 1  # Only 1 new event
    assert data2["events_updated"] == 1  # 1 existing event updated
    
    # Verify in database
    async with test_db() as session:
        query = select(Shipment).where(Shipment.invoice_number == "NF-UPDATE")
        result = await session.execute(query)
        shipment = result.scalar_one_or_none()
        
        assert shipment is not None
        assert len(shipment.tracking_events) == 2


@pytest.mark.asyncio
async def test_get_pending_shipments(client: AsyncClient, test_db, api_key_headers):
    """Test getting pending shipments for sync"""
    # Create shipments with different statuses
    async with test_db() as session:
        shipments = [
            Shipment(
                invoice_number="NF-PENDING-1",
                document="11111111111111",
                carrier="SSW",
                status="pending"
            ),
            Shipment(
                invoice_number="NF-TRANSIT-1",
                document="22222222222222",
                carrier="SSW",
                status="in_transit"
            ),
            Shipment(
                invoice_number="NF-DELIVERED-1",
                document="33333333333333",
                carrier="SSW",
                status="delivered"
            ),
        ]
        session.add_all(shipments)
        await session.commit()
    
    # Get pending shipments
    response = await client.get(
        "/api/v1/tracking-updates/pending-shipments",
        headers=api_key_headers,
        params={"limit": 100}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Should only return pending and in_transit (not delivered)
    invoice_numbers = [s["invoice_number"] for s in data]
    assert "NF-PENDING-1" in invoice_numbers
    assert "NF-TRANSIT-1" in invoice_numbers
    assert "NF-DELIVERED-1" not in invoice_numbers


@pytest.mark.asyncio
async def test_duplicate_event_handling(client: AsyncClient, test_db, api_key_headers):
    """Test that duplicate events are updated, not duplicated"""
    payload = {
        "invoice_number": "NF-DUPLICATE",
        "document": "12345678000199",
        "carrier": "SSW",
        "current_status": "in_transit",
        "events": [
            {
                "occurrence_code": "80",
                "status": "in_transit",
                "description": "mercadoria recebida",
                "location": "RIO DE JANEIRO RJ",
                "unit": "1234",
                "occurred_at": "2025-11-20T10:00:00"
            }
        ]
    }
    
    # Send same event twice
    response1 = await client.post(
        "/api/v1/tracking-updates/shipment",
        json=payload,
        headers=api_key_headers
    )
    assert response1.status_code == 200
    
    response2 = await client.post(
        "/api/v1/tracking-updates/shipment",
        json=payload,
        headers=api_key_headers
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["events_created"] == 0
    assert data2["events_updated"] == 1
    
    # Verify only 1 event exists
    async with test_db() as session:
        query = select(Shipment).where(Shipment.invoice_number == "NF-DUPLICATE")
        result = await session.execute(query)
        shipment = result.scalar_one_or_none()
        
        assert shipment is not None
        assert len(shipment.tracking_events) == 1
