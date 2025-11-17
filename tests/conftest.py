# Test Configuration and Fixtures
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import get_application
from app.db.conn import get_db
from app.models.base import Base
from app.models.user import User
from app.models.client import Client  
from app.models.shipment import Shipment, ShipmentTrackingEvent

# Usar SQLite in-memory com StaticPool para compartilhar entre conexões
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Crucial para compartilhar o banco in-memory
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """Setup database before each test."""
    # Create only compatible tables
    async with test_engine.begin() as conn:
        await conn.run_sync(User.__table__.create, checkfirst=True)
        await conn.run_sync(Client.__table__.create, checkfirst=True)
        await conn.run_sync(Shipment.__table__.create, checkfirst=True)
        await conn.run_sync(ShipmentTrackingEvent.__table__.create, checkfirst=True)
    
    yield
    
    # Cleanup after test
    async with test_engine.begin() as conn:
        await conn.run_sync(ShipmentTrackingEvent.__table__.drop, checkfirst=True)
        await conn.run_sync(Shipment.__table__.drop, checkfirst=True)
        await conn.run_sync(Client.__table__.drop, checkfirst=True)
        await conn.run_sync(User.__table__.drop, checkfirst=True)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database dependency."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.api.routes import auth, users, clients, shipments
    from app.core.config import get_app_settings
    
    settings = get_app_settings()
    
    # Create minimal app for testing
    app = FastAPI(title="ShipTracker API - Test")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(auth.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(clients.router, prefix="/api")
    app.include_router(shipments.router, prefix="/api")

    # Override get_db dependency
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# Helper fixtures for authenticated tests
@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    from app.api.routes.auth import hash_password
    
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("testpassword123"),
        full_name="Test User",
        role="operator"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user in the database."""
    from app.api.routes.auth import hash_password
    
    user = User(
        email="admin@example.com",
        password_hash=hash_password("adminpass123"),
        full_name="Admin User",
        role="admin"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def viewer_user(db_session: AsyncSession) -> User:
    """Create a viewer user in the database."""
    from app.api.routes.auth import hash_password
    
    user = User(
        email="viewer@example.com",
        password_hash=hash_password("viewerpass123"),
        full_name="Viewer User",
        role="viewer"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Get authorization headers for test user."""
    from app.api.routes.auth import create_access_token
    from datetime import timedelta
    
    access_token = create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def admin_headers(admin_user: User) -> dict:
    """Get authorization headers for admin user."""
    from app.api.routes.auth import create_access_token
    from datetime import timedelta
    
    access_token = create_access_token(
        data={"sub": str(admin_user.id)},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def viewer_headers(viewer_user: User) -> dict:
    """Get authorization headers for viewer user."""
    from app.api.routes.auth import create_access_token
    from datetime import timedelta
    
    access_token = create_access_token(
        data={"sub": str(viewer_user.id)},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def test_client_record(db_session: AsyncSession) -> Client:
    """Create a test client in the database."""
    client = Client(
        name="Test Company",
        email="company@test.com",
        phone="1234567890",
        address_line1="123 Test St",
        city="Test City",
        state="TS",
        postal_code="12345"
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    return client


@pytest_asyncio.fixture
async def test_shipment(db_session: AsyncSession, test_client_record: Client) -> Shipment:
    """Create a test shipment in the database."""
    shipment = Shipment(
        tracking_code="TEST123456",
        carrier="Test Carrier",
        status="in_transit",
        client_id=test_client_record.id,
        origin="Origin City",
        destination="Destination City"
    )
    db_session.add(shipment)
    await db_session.commit()
    await db_session.refresh(shipment)
    return shipment


# Helper function for auth headers
def get_auth_headers(token: str) -> dict:
    """Get authorization headers with token."""
    return {"Authorization": f"Bearer {token}"}
