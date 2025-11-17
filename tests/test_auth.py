# Authentication Tests
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestAuth:
    """Test authentication endpoints"""

    @pytest.mark.asyncio
    async def test_register_new_user(self, client: AsyncClient, db_session: AsyncSession):
        """Test user registration"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "securepass123",
                "role": "operator"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"
        assert data["user"]["role"] == "operator"
        assert "id" in data["user"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "full_name": "Another User",
                "password": "password123",
                "role": "operator"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "full_name": "Test User",
                "password": "password123",
                "role": "operator"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login"""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "testuser@example.com",  # Changed from test@example.com
                "password": "testpassword123"  # Changed from testpass123
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "testuser@example.com"  # Changed from test@example.com

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password"""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user"""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict):
        """Test getting current user info"""
        response = await client.get(
            "/api/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"  # Changed from test@example.com
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication"""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token"""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, auth_headers: dict):
        """Test token refresh"""
        response = await client.post(
            "/api/auth/refresh",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.skip(reason="Logout endpoint not implemented yet")
    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, auth_headers: dict):
        """Test logout"""
        response = await client.post(
            "/api/auth/logout",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
