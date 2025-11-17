# Shipment Management Tests
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import Shipment
from app.models.client import Client
from app.models.user import User


@pytest_asyncio.fixture
async def test_shipment(db_session: AsyncSession, test_user: User, test_client_record: Client) -> Shipment:
    """Create a test shipment"""
    shipment = Shipment(
        tracking_code="BR123456789BR",
        carrier="Correios",
        status="pending",
        client_id=test_client_record.id,
        created_by=test_user.id,
        origin_city="São Paulo",
        origin_state="SP",
        origin_country="BR",
        destination_city="Rio de Janeiro",
        destination_state="RJ",
        destination_country="BR",
        weight_kg=2.5,
        declared_value=100.00,
        description="Test package"
    )
    db_session.add(shipment)
    await db_session.commit()
    await db_session.refresh(shipment)
    return shipment


class TestShipments:
    """Test shipment management endpoints"""

    @pytest.mark.asyncio
    async def test_list_shipments(self, client: AsyncClient, auth_headers: dict, test_shipment: Shipment):
        """Test listing shipments"""
        response = await client.get(
            "/api/shipments",
            headers=auth_headers
        )
        assert response.status_code == 200
        shipments = response.json()
        assert isinstance(shipments, list)
        assert len(shipments) >= 1

    @pytest.mark.asyncio
    async def test_list_shipments_with_filters(self, client: AsyncClient, auth_headers: dict, test_shipment: Shipment):
        """Test listing shipments with filters"""
        response = await client.get(
            "/api/shipments?status=pending&carrier=Correios",
            headers=auth_headers
        )
        assert response.status_code == 200
        shipments = response.json()
        assert all(s["status"] == "pending" for s in shipments)

    @pytest.mark.asyncio
    async def test_search_shipments(self, client: AsyncClient, auth_headers: dict, test_shipment: Shipment):
        """Test searching shipments by tracking code"""
        response = await client.get(
            f"/api/shipments?search={test_shipment.tracking_code}",
            headers=auth_headers
        )
        assert response.status_code == 200
        shipments = response.json()
        assert len(shipments) >= 1
        assert shipments[0]["tracking_code"] == test_shipment.tracking_code

    @pytest.mark.asyncio
    async def test_get_shipment_by_id(self, client: AsyncClient, auth_headers: dict, test_shipment: Shipment):
        """Test getting specific shipment"""
        response = await client.get(
            f"/api/shipments/{test_shipment.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_shipment.id)
        assert data["tracking_code"] == test_shipment.tracking_code

    @pytest.mark.asyncio
    async def test_create_shipment(self, client: AsyncClient, auth_headers: dict, test_client_record: Client):
        """Test creating new shipment"""
        response = await client.post(
            "/api/shipments",
            headers=auth_headers,
            json={
                "tracking_code": "BR987654321BR",
                "carrier": "FedEx",
                "status": "pending",
                "client_id": str(test_client_record.id),
                "origin_city": "Brasília",
                "origin_state": "DF",
                "origin_country": "BR",
                "destination_city": "Salvador",
                "destination_state": "BA",
                "destination_country": "BR",
                "weight_kg": 1.5,
                "declared_value": 50.00
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["tracking_code"] == "BR987654321BR"
        assert data["carrier"] == "FedEx"

    @pytest.mark.asyncio
    async def test_create_shipment_duplicate_tracking(self, client: AsyncClient, auth_headers: dict, test_shipment: Shipment, test_client_record: Client):
        """Test creating shipment with duplicate tracking code"""
        response = await client.post(
            "/api/shipments",
            headers=auth_headers,
            json={
                "tracking_code": test_shipment.tracking_code,
                "carrier": "Correios",
                "status": "pending",
                "client_id": str(test_client_record.id),
                "origin_country": "BR",
                "destination_country": "BR"
            }
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_shipment(self, client: AsyncClient, auth_headers: dict, test_shipment: Shipment):
        """Test updating shipment"""
        response = await client.patch(
            f"/api/shipments/{test_shipment.id}",
            headers=auth_headers,
            json={
                "status": "in_transit",
                "description": "Updated description"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_transit"
        assert data["description"] == "Updated description"

    @pytest.mark.skip(reason="Update status endpoint not implemented yet")
    @pytest.mark.asyncio
    async def test_update_shipment_status(self, client: AsyncClient, auth_headers: dict, test_shipment: Shipment):
        """Test updating shipment status"""
        response = await client.patch(
            f"/api/shipments/{test_shipment.id}/status",
            headers=auth_headers,
            json={"status": "delivered"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "delivered"

    @pytest.mark.asyncio
    async def test_delete_shipment(self, client: AsyncClient, admin_headers: dict, test_shipment: Shipment):
        """Test soft deleting shipment"""
        response = await client.delete(
            f"/api/shipments/{test_shipment.id}",
            headers=admin_headers
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_get_shipment_stats(self, client: AsyncClient, auth_headers: dict):
        """Test getting shipment statistics"""
        response = await client.get(
            "/api/shipments/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_shipments" in data
        assert "in_transit" in data
        assert "delivered" in data

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test accessing shipments without authentication"""
        response = await client.get("/api/shipments")
        assert response.status_code == 401
