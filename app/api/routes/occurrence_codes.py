"""
Occurrence Code management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.db.conn import get_db
from app.models.occurrence_code import OccurrenceCode
from app.models.user import User
from app.schemas.occurrence_code import (
    OccurrenceCodeCreate,
    OccurrenceCodeUpdate,
    OccurrenceCodeResponse,
    OccurrenceCodeListResponse
)
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/occurrence-codes", tags=["Occurrence Codes"])


@router.get("", response_model=OccurrenceCodeListResponse)
async def list_occurrence_codes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    type_filter: Optional[str] = Query(None, alias="type"),
    process: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all occurrence codes with optional filters"""
    query = select(OccurrenceCode)

    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            OccurrenceCode.description.ilike(search_filter)
        )
    
    if type_filter:
        query = query.where(OccurrenceCode.type == type_filter)
    
    if process:
        query = query.where(OccurrenceCode.process == process)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    occurrence_codes = result.scalars().all()

    return OccurrenceCodeListResponse(
        total=total,
        items=occurrence_codes
    )


@router.get("/{code}", response_model=OccurrenceCodeResponse)
async def get_occurrence_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get occurrence code by code"""
    query = select(OccurrenceCode).where(OccurrenceCode.code == code)
    result = await db.execute(query)
    occurrence_code = result.scalar_one_or_none()

    if not occurrence_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código de ocorrência '{code}' não encontrado"
        )

    return occurrence_code


@router.post("", response_model=OccurrenceCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_occurrence_code(
    occurrence_code_data: OccurrenceCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new occurrence code"""
    # Check if code already exists
    query = select(OccurrenceCode).where(OccurrenceCode.code == occurrence_code_data.code)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Código de ocorrência '{occurrence_code_data.code}' já existe"
        )

    # Create new occurrence code
    occurrence_code = OccurrenceCode(**occurrence_code_data.model_dump())
    db.add(occurrence_code)
    await db.commit()
    await db.refresh(occurrence_code)

    return occurrence_code


@router.put("/{code}", response_model=OccurrenceCodeResponse)
async def update_occurrence_code(
    code: str,
    occurrence_code_data: OccurrenceCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an occurrence code"""
    query = select(OccurrenceCode).where(OccurrenceCode.code == code)
    result = await db.execute(query)
    occurrence_code = result.scalar_one_or_none()

    if not occurrence_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código de ocorrência '{code}' não encontrado"
        )

    # Update fields
    update_data = occurrence_code_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(occurrence_code, field, value)

    await db.commit()
    await db.refresh(occurrence_code)

    return occurrence_code


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_occurrence_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an occurrence code"""
    query = select(OccurrenceCode).where(OccurrenceCode.code == code)
    result = await db.execute(query)
    occurrence_code = result.scalar_one_or_none()

    if not occurrence_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código de ocorrência '{code}' não encontrado"
        )

    await db.delete(occurrence_code)
    await db.commit()

    return None
