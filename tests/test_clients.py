# Client Management Tests
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.user import User


@pytest_asyncio.fixture
async def test_client_record(db_session: AsyncSession, test_user: User) -> Client:
    """Create a test client record"""
    client = Client(
        name="Test Company",
        email="contact@testcompany.com",
        phone="1234567890",
        document="12345678901234",
        address_line1="123 Test St",
        city="Test City",
        state="TS",
        postal_code="12345",
        country="BR",
        user_id=test_user.id
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    return client


class TestClients:
    """Test client management endpoints"""

    @pytest.mark.asyncio
    async def test_list_clients(self, client: AsyncClient, auth_headers: dict, test_client_record: Client):
        """Test listing clients"""
        response = await client.get(
            "/api/clients",
            headers=auth_headers
        )
        assert response.status_code == 200
        clients = response.json()
        assert isinstance(clients, list)
        assert len(clients) >= 1

    @pytest.mark.asyncio
    async def test_list_clients_with_search(self, client: AsyncClient, auth_headers: dict, test_client_record: Client):
        """Test searching clients"""
        response = await client.get(
            "/api/clients?search=Test Company",
            headers=auth_headers
        )
        assert response.status_code == 200
        clients = response.json()
        assert len(clients) >= 1
        assert "Test Company" in clients[0]["name"]

    @pytest.mark.asyncio
    async def test_get_client_by_id(self, client: AsyncClient, auth_headers: dict, test_client_record: Client):
        """Test getting specific client"""
        response = await client.get(
            f"/api/clients/{test_client_record.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_client_record.id)
        assert data["name"] == "Test Company"

    @pytest.mark.asyncio
    async def test_create_client(self, client: AsyncClient, auth_headers: dict):
        """Test creating new client"""
        response = await client.post(
            "/api/clients",
            headers=auth_headers,
            json={
                "name": "New Client",
                "email": "new@client.com",
                "phone": "9876543210",
                "document": "98765432109876",
                "address_line1": "456 New St",
                "city": "New City",
                "state": "NC",
                "postal_code": "54321",
                "country": "BR"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Client"
        assert data["email"] == "new@client.com"

    @pytest.mark.asyncio
    async def test_create_client_invalid_email(self, client: AsyncClient, auth_headers: dict):
        """Test creating client with invalid email"""
        response = await client.post(
            "/api/clients",
            headers=auth_headers,
            json={
                "name": "Client",
                "email": "invalid-email",
                "country": "BR"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_client(self, client: AsyncClient, auth_headers: dict, test_client_record: Client):
        """Test updating client"""
        response = await client.patch(
            f"/api/clients/{test_client_record.id}",
            headers=auth_headers,
            json={
                "name": "Updated Company",
                "email": "updated@company.com"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Company"

    @pytest.mark.asyncio
    async def test_delete_client(self, client: AsyncClient, admin_headers: dict, test_client_record: Client):
        """Test soft deleting client"""
        response = await client.delete(
            f"/api/clients/{test_client_record.id}",
            headers=admin_headers
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_get_client_stats(self, client: AsyncClient, auth_headers: dict):
        """Test getting client statistics"""
        response = await client.get(
            "/api/clients/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_clients" in data
        assert "active_clients" in data
        assert "vip_clients" in data
