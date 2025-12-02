"""
User management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from uuid import UUID

from app.db.conn import get_db
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.api.routes.auth import get_current_user, hash_password
from app.api.dependencies.permissions import (
    can_view_users,
    can_create_users,
    can_edit_users,
    can_delete_users,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    status_filter: Optional[UserStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_view_users)
):
    """List all users with optional filters (requires can_view_users permission)"""
    query = select(User).where(User.deleted_at.is_(None))

    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                User.full_name.ilike(search_filter),
                User.email.ilike(search_filter)
            )
        )

    if role:
        query = query.where(User.role == role)

    if status_filter:
        query = query.where(User.status == status_filter)

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    return users


@router.get("/count")
async def count_users(
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    status_filter: Optional[UserStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_view_users)
):
    """Count total users with optional filters (requires can_view_users permission)"""
    query = select(func.count(User.id)).where(User.deleted_at.is_(None))

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                User.full_name.ilike(search_filter),
                User.email.ilike(search_filter)
            )
        )

    if role:
        query = query.where(User.role == role)

    if status_filter:
        query = query.where(User.status == status_filter)

    result = await db.execute(query)
    count = result.scalar_one()

    return {"count": count}


@router.get("/sellers/list", response_model=List[UserResponse])
async def list_sellers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all active sellers (available to all authenticated users for shipment assignment)"""
    query = select(User).where(
        User.deleted_at.is_(None),
        User.role == UserRole.SELLER,
        User.status == UserStatus.ACTIVE
    ).order_by(User.full_name)

    result = await db.execute(query)
    sellers = result.scalars().all()

    return sellers


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_view_users)
):
    """Get a specific user by ID (requires can_view_users permission)"""
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_create_users)
):
    """Create a new user (requires can_create_users permission)"""
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        phone=user_data.phone,
        must_change_password=True  # Force password change on first login
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_edit_users)
):
    """Update a user (requires can_edit_users permission)"""

    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Handle password update separately
    if "password" in update_data:
        password = update_data.pop("password")
        if password:
            user.password_hash = hash_password(password)
    
    # Check if email is being changed and if it's available
    if "email" in update_data and update_data["email"] != user.email:
        email_result = await db.execute(
            select(User).where(User.email == update_data["email"])
        )
        if email_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    # Only admin can change role and status
    if current_user.role != UserRole.ADMIN:
        update_data.pop("role", None)
        update_data.pop("status", None)

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_delete_users)
):
    """Soft delete a user (requires can_delete_users permission)"""
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Soft delete
    user.soft_delete()
    await db.commit()

    return None
