"""
Carrier routes for managing shipping carriers
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.conn import get_db
from app.models.carrier import Carrier
from app.models.user import User, UserRole
from app.schemas.carrier import CarrierCreate, CarrierUpdate, CarrierResponse
from app.api.routes.auth import get_current_user


router = APIRouter(prefix="/carriers", tags=["carriers"])


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify that current user is an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action"
        )
    return current_user


@router.get("/", response_model=List[CarrierResponse])
async def list_carriers(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all carriers.
    
    - **active_only**: If True, only return active carriers
    """
    query = select(Carrier)
    if active_only:
        query = query.where(Carrier.active == True)
    
    query = query.order_by(Carrier.is_default.desc(), Carrier.name)
    result = await db.execute(query)
    carriers = result.scalars().all()
    
    return carriers


@router.get("/{carrier_id}", response_model=CarrierResponse)
async def get_carrier(
    carrier_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific carrier by ID"""
    result = await db.execute(select(Carrier).where(Carrier.id == carrier_id))
    carrier = result.scalar_one_or_none()
    
    if not carrier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrier not found"
        )
    
    return carrier


@router.post("/", response_model=CarrierResponse, status_code=status.HTTP_201_CREATED)
async def create_carrier(
    carrier_data: CarrierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new carrier.
    
    Only admin users can create carriers.
    """
    # Check if carrier with same name or code already exists
    result = await db.execute(
        select(Carrier).where(
            (Carrier.name == carrier_data.name) | (Carrier.code == carrier_data.code)
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        if existing.name == carrier_data.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Carrier with name '{carrier_data.name}' already exists"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Carrier with code '{carrier_data.code}' already exists"
            )
    
    # Create new carrier
    carrier = Carrier(**carrier_data.model_dump())
    db.add(carrier)
    await db.commit()
    await db.refresh(carrier)
    
    return carrier


@router.patch("/{carrier_id}", response_model=CarrierResponse)
async def update_carrier(
    carrier_id: uuid.UUID,
    carrier_data: CarrierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update a carrier.
    
    Only admin users can update carriers.
    """
    result = await db.execute(select(Carrier).where(Carrier.id == carrier_id))
    carrier = result.scalar_one_or_none()
    
    if not carrier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrier not found"
        )
    
    # Check if carrier is default (cannot be modified in some ways)
    if carrier.is_default and carrier_data.active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate default carriers"
        )
    
    # Check for name conflicts if name is being updated
    if carrier_data.name and carrier_data.name != carrier.name:
        result = await db.execute(
            select(Carrier).where(Carrier.name == carrier_data.name)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Carrier with name '{carrier_data.name}' already exists"
            )
    
    # Update carrier
    update_data = carrier_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(carrier, key, value)
    
    await db.commit()
    await db.refresh(carrier)
    
    return carrier


@router.delete("/{carrier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_carrier(
    carrier_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a carrier.
    
    Only admin users can delete carriers.
    Default carriers cannot be deleted.
    """
    result = await db.execute(select(Carrier).where(Carrier.id == carrier_id))
    carrier = result.scalar_one_or_none()
    
    if not carrier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrier not found"
        )
    
    if carrier.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default carriers"
        )
    
    await db.delete(carrier)
    await db.commit()
    
    return None
