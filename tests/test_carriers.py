"""Tests for carriers API endpoints"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestCarriers:
    """Test suite for carrier endpoints"""

    @pytest.mark.asyncio
    async def test_list_carriers(self, client: AsyncClient, auth_headers: dict):
        """Test listing all carriers"""
        response = await client.get("/api/carriers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the default carriers from migration
        assert len(data) >= 5

    @pytest.mark.asyncio
    async def test_list_active_carriers_only(self, client: AsyncClient, auth_headers: dict):
        """Test listing only active carriers"""
        response = await client.get("/api/carriers/?active_only=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned carriers should be active
        for carrier in data:
            assert carrier["active"] is True

    @pytest.mark.asyncio
    async def test_get_carrier_by_id(self, client: AsyncClient, auth_headers: dict):
        """Test getting a specific carrier by ID"""
        # First get list of carriers
        list_response = await client.get("/api/carriers/", headers=auth_headers)
        carriers = list_response.json()
        assert len(carriers) > 0
        
        carrier_id = carriers[0]["id"]
        
        # Get specific carrier
        response = await client.get(f"/api/carriers/{carrier_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == carrier_id
        assert "name" in data
        assert "code" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_carrier(self, client: AsyncClient, auth_headers: dict):
        """Test getting a carrier that doesn't exist"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/carriers/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_carrier_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test creating a new carrier as admin"""
        new_carrier = {
            "name": "Test Carrier",
            "code": "test-carrier",
            "color": "#FF5733",
            "active": True,
            "is_default": False
        }
        
        response = await client.post("/api/carriers/", json=new_carrier, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == new_carrier["name"]
        assert data["code"] == new_carrier["code"]
        assert data["color"] == new_carrier["color"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_carrier_duplicate_code(self, client: AsyncClient, admin_headers: dict):
        """Test creating carrier with duplicate code fails"""
        # First get existing carrier code
        list_response = await client.get("/api/carriers/", headers=admin_headers)
        carriers = list_response.json()
        existing_code = carriers[0]["code"]
        
        new_carrier = {
            "name": "Duplicate Test",
            "code": existing_code,  # Use existing code
            "color": "#FF5733",
            "active": True,
            "is_default": False
        }
        
        response = await client.post("/api/carriers/", json=new_carrier, headers=admin_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_carrier_as_non_admin(self, client: AsyncClient, auth_headers: dict):
        """Test that non-admin users cannot create carriers"""
        new_carrier = {
            "name": "Unauthorized Carrier",
            "code": "unauthorized",
            "color": "#FF5733",
            "active": True,
            "is_default": False
        }
        
        response = await client.post("/api/carriers/", json=new_carrier, headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_carrier_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test updating a carrier as admin"""
        # First create a carrier
        new_carrier = {
            "name": "Update Test",
            "code": "update-test",
            "color": "#FF5733",
            "active": True,
            "is_default": False
        }
        
        create_response = await client.post("/api/carriers/", json=new_carrier, headers=admin_headers)
        carrier_id = create_response.json()["id"]
        
        # Update the carrier
        update_data = {
            "name": "Updated Name",
            "color": "#00FF00"
        }
        
        response = await client.patch(f"/api/carriers/{carrier_id}", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["color"] == "#00FF00"

    @pytest.mark.asyncio
    async def test_cannot_deactivate_default_carrier(self, client: AsyncClient, admin_headers: dict):
        """Test that default carriers cannot be deactivated"""
        # Get a default carrier
        list_response = await client.get("/api/carriers/", headers=admin_headers)
        carriers = list_response.json()
        default_carrier = next((c for c in carriers if c["is_default"]), None)
        
        if default_carrier:
            carrier_id = default_carrier["id"]
            
            # Try to deactivate
            update_data = {"active": False}
            response = await client.patch(f"/api/carriers/{carrier_id}", json=update_data, headers=admin_headers)
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_carrier_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test deleting a carrier as admin"""
        # First create a carrier
        new_carrier = {
            "name": "Delete Test",
            "code": "delete-test",
            "color": "#FF5733",
            "active": True,
            "is_default": False
        }
        
        create_response = await client.post("/api/carriers/", json=new_carrier, headers=admin_headers)
        carrier_id = create_response.json()["id"]
        
        # Delete the carrier
        response = await client.delete(f"/api/carriers/{carrier_id}", headers=admin_headers)
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = await client.get(f"/api/carriers/{carrier_id}", headers=admin_headers)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_cannot_delete_default_carrier(self, client: AsyncClient, admin_headers: dict):
        """Test that default carriers cannot be deleted"""
        # Get a default carrier
        list_response = await client.get("/api/carriers/", headers=admin_headers)
        carriers = list_response.json()
        default_carrier = next((c for c in carriers if c["is_default"]), None)
        
        if default_carrier:
            carrier_id = default_carrier["id"]
            
            # Try to delete
            response = await client.delete(f"/api/carriers/{carrier_id}", headers=admin_headers)
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_carrier_as_non_admin(self, client: AsyncClient, auth_headers: dict):
        """Test that non-admin users cannot delete carriers"""
        # Get any carrier
        list_response = await client.get("/api/carriers/", headers=auth_headers)
        carriers = list_response.json()
        carrier_id = carriers[0]["id"]
        
        response = await client.delete(f"/api/carriers/{carrier_id}", headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test that endpoints require authentication"""
        response = await client.get("/api/carriers/")
        assert response.status_code == 401
