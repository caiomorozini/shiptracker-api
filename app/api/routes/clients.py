"""
Client management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.conn import get_db
from app.models.client import Client
from app.models.user import User, UserRole
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=List[ClientResponse])
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    is_vip: Optional[bool] = None,
    user_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all clients with optional filters"""
    query = select(Client).options(
        selectinload(Client.responsible_user)
    ).where(Client.deleted_at.is_(None))

    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Client.name.ilike(search_filter),
                Client.email.ilike(search_filter),
                Client.document.ilike(search_filter)
            )
        )

    if is_favorite is not None:
        query = query.where(Client.is_favorite == is_favorite)

    if is_vip is not None:
        query = query.where(Client.is_vip == is_vip)

    if user_id:
        query = query.where(Client.user_id == user_id)

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Client.created_at.desc())

    result = await db.execute(query)
    clients = result.scalars().all()

    return clients


@router.get("/count")
async def count_clients(
    search: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    is_vip: Optional[bool] = None,
    user_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Count total clients with optional filters"""
    query = select(func.count(Client.id)).where(Client.deleted_at.is_(None))

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Client.name.ilike(search_filter),
                Client.email.ilike(search_filter),
                Client.document.ilike(search_filter)
            )
        )

    if is_favorite is not None:
        query = query.where(Client.is_favorite == is_favorite)

    if is_vip is not None:
        query = query.where(Client.is_vip == is_vip)

    if user_id:
        query = query.where(Client.user_id == user_id)

    result = await db.execute(query)
    count = result.scalar_one()

    return {"count": count}


@router.get("/stats")
async def get_client_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get client statistics"""
    total_query = select(func.count(Client.id)).where(Client.deleted_at.is_(None))
    total_result = await db.execute(total_query)
    total_clients = total_result.scalar_one()

    # Clients with shipments
    active_query = select(func.count(Client.id)).where(
        Client.deleted_at.is_(None),
        Client.total_shipments > 0
    )
    active_result = await db.execute(active_query)
    active_clients = active_result.scalar_one()

    # New clients this month
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    new_query = select(func.count(Client.id)).where(
        Client.deleted_at.is_(None),
        Client.created_at >= start_of_month
    )
    new_result = await db.execute(new_query)
    new_this_month = new_result.scalar_one()

    # VIP clients
    vip_query = select(func.count(Client.id)).where(
        Client.deleted_at.is_(None),
        Client.is_vip == True
    )
    vip_result = await db.execute(vip_query)
    vip_clients = vip_result.scalar_one()

    return {
        "total_clients": total_clients,
        "active_clients": active_clients,
        "new_this_month": new_this_month,
        "vip_clients": vip_clients
    }


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific client by ID"""
    result = await db.execute(
        select(Client).options(
            selectinload(Client.responsible_user)
        ).where(Client.id == client_id, Client.deleted_at.is_(None))
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    return client


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new client"""
    # Check if email already exists (if provided)
    if client_data.email:
        result = await db.execute(
            select(Client).where(
                Client.email == client_data.email,
                Client.deleted_at.is_(None)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Validate user_id if provided
    if client_data.user_id:
        user_result = await db.execute(
            select(User).where(
                User.id == client_data.user_id,
                User.deleted_at.is_(None)
            )
        )
        if not user_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

    # Create new client - assign to current user if not specified
    client_dict = client_data.model_dump()
    if not client_dict.get("user_id"):
        client_dict["user_id"] = current_user.id
    
    new_client = Client(**client_dict)

    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)

    return new_client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a client"""
    # Get client
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.deleted_at.is_(None))
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Update fields
    update_data = client_data.model_dump(exclude_unset=True)
    
    # Check if email is being changed and if it's available
    if "email" in update_data and update_data["email"] and update_data["email"] != client.email:
        email_result = await db.execute(
            select(Client).where(
                Client.email == update_data["email"],
                Client.deleted_at.is_(None)
            )
        )
        if email_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    # Validate user_id if being changed
    if "user_id" in update_data and update_data["user_id"]:
        user_result = await db.execute(
            select(User).where(
                User.id == update_data["user_id"],
                User.deleted_at.is_(None)
            )
        )
        if not user_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)

    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a client"""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.deleted_at.is_(None))
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Soft delete
    client.soft_delete()
    await db.commit()

    return None
