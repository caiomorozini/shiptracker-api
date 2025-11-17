# User Management Tests
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class TestUsers:
    """Test user management endpoints"""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, client: AsyncClient, admin_headers: dict, test_user: User):
        """Test listing users as admin"""
        response = await client.get(
            "/api/users",
            headers=admin_headers
        )
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_list_users_as_viewer(self, client: AsyncClient, viewer_headers: dict):
        """Test listing users as viewer (should fail)"""
        response = await client.get(
            "/api/users",
            headers=viewer_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client: AsyncClient, admin_headers: dict, test_user: User):
        """Test getting specific user"""
        response = await client.get(
            f"/api/users/{test_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent user"""
        response = await client.get(
            "/api/users/00000000-0000-0000-0000-000000000000",
            headers=admin_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_user_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test creating new user as admin"""
        response = await client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "email": "newoperator@example.com",
                "full_name": "New Operator",
                "password": "securepass123",
                "role": "operator"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newoperator@example.com"
        assert data["role"] == "operator"

    @pytest.mark.asyncio
    async def test_create_user_as_non_admin(self, client: AsyncClient, auth_headers: dict):
        """Test creating user as non-admin (should fail)"""
        response = await client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "email": "another@example.com",
                "full_name": "Another User",
                "password": "password123",
                "role": "operator"
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, admin_headers: dict, test_user: User):
        """Test updating user"""
        response = await client.patch(
            f"/api/users/{test_user.id}",
            headers=admin_headers,
            json={
                "full_name": "Updated Name",
                "role": "manager"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["role"] == "manager"

    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient, admin_headers: dict, test_user: User):
        """Test soft deleting user"""
        response = await client.delete(
            f"/api/users/{test_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 204

    @pytest.mark.skip(reason="Change password endpoint not implemented yet")
    @pytest.mark.asyncio
    async def test_change_password(self, client: AsyncClient, auth_headers: dict):
        """Test changing own password"""
        response = await client.post(
            "/api/users/change-password",
            headers=auth_headers,
            json={
                "old_password": "testpassword123",
                "new_password": "newpass123456"
            }
        )
        assert response.status_code == 200

    @pytest.mark.skip(reason="Change password endpoint not implemented yet")
    @pytest.mark.asyncio
    async def test_change_password_wrong_old(self, client: AsyncClient, auth_headers: dict):
        """Test changing password with wrong old password"""
        response = await client.post(
            "/api/users/change-password",
            headers=auth_headers,
            json={
                "old_password": "wrongpassword",
                "new_password": "newpass123456"
            }
        )
        assert response.status_code == 400
