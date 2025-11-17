"""
Shipment management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import joinedload
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from app.db.conn import get_db
from app.models.shipment import Shipment, ShipmentTrackingEvent
from app.models.client import Client
from app.models.user import User
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentResponse,
    ShipmentDetailResponse,
    TrackingEventCreate,
    TrackingEventResponse
)
from app.api.routes.auth import get_current_user
from app.api.dependencies.permissions import (
    can_create_shipments,
    can_edit_shipments,
    can_delete_shipments,
)

router = APIRouter(prefix="/shipments", tags=["Shipments"])


@router.get("", response_model=List[ShipmentResponse])
async def list_shipments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    carrier: Optional[str] = None,
    client_id: Optional[UUID] = None,
    origin_city: Optional[str] = None,
    destination_city: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all shipments with optional filters"""
    query = select(Shipment).where(Shipment.deleted_at.is_(None))

    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Shipment.tracking_code.ilike(search_filter),
                Shipment.description.ilike(search_filter)
            )
        )

    if status_filter:
        query = query.where(Shipment.status == status_filter)

    if carrier:
        query = query.where(Shipment.carrier.ilike(f"%{carrier}%"))

    if client_id:
        query = query.where(Shipment.client_id == client_id)

    if origin_city:
        query = query.where(Shipment.origin_city.ilike(f"%{origin_city}%"))

    if destination_city:
        query = query.where(Shipment.destination_city.ilike(f"%{destination_city}%"))

    if date_from:
        query = query.where(Shipment.created_at >= datetime.combine(date_from, datetime.min.time()))

    if date_to:
        query = query.where(Shipment.created_at <= datetime.combine(date_to, datetime.max.time()))

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Shipment.created_at.desc())

    result = await db.execute(query)
    shipments = result.scalars().all()

    return shipments


@router.get("/count")
async def count_shipments(
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    carrier: Optional[str] = None,
    client_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Count total shipments with optional filters"""
    query = select(func.count(Shipment.id)).where(Shipment.deleted_at.is_(None))

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Shipment.tracking_code.ilike(search_filter),
                Shipment.description.ilike(search_filter)
            )
        )

    if status_filter:
        query = query.where(Shipment.status == status_filter)

    if carrier:
        query = query.where(Shipment.carrier.ilike(f"%{carrier}%"))

    if client_id:
        query = query.where(Shipment.client_id == client_id)

    if date_from:
        query = query.where(Shipment.created_at >= datetime.combine(date_from, datetime.min.time()))

    if date_to:
        query = query.where(Shipment.created_at <= datetime.combine(date_to, datetime.max.time()))

    result = await db.execute(query)
    count = result.scalar_one()

    return {"count": count}


@router.get("/stats")
async def get_shipment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get shipment statistics"""
    total_query = select(func.count(Shipment.id)).where(Shipment.deleted_at.is_(None))
    total_result = await db.execute(total_query)
    total_shipments = total_result.scalar_one()

    in_transit_query = select(func.count(Shipment.id)).where(
        Shipment.deleted_at.is_(None),
        Shipment.status.in_(["in_transit", "pending", "processing"])
    )
    in_transit_result = await db.execute(in_transit_query)
    in_transit = in_transit_result.scalar_one()

    delivered_query = select(func.count(Shipment.id)).where(
        Shipment.deleted_at.is_(None),
        Shipment.status == "delivered"
    )
    delivered_result = await db.execute(delivered_query)
    delivered = delivered_result.scalar_one()

    delayed_query = select(func.count(Shipment.id)).where(
        Shipment.deleted_at.is_(None),
        Shipment.status == "delayed"
    )
    delayed_result = await db.execute(delayed_query)
    delayed = delayed_result.scalar_one()

    cancelled_query = select(func.count(Shipment.id)).where(
        Shipment.deleted_at.is_(None),
        Shipment.status.in_(["cancelled", "returned"])
    )
    cancelled_result = await db.execute(cancelled_query)
    cancelled = cancelled_result.scalar_one()

    return {
        "total_shipments": total_shipments,
        "in_transit": in_transit,
        "delivered": delivered,
        "delayed": delayed,
        "cancelled": cancelled
    }


@router.get("/{shipment_id}", response_model=ShipmentDetailResponse)
async def get_shipment(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific shipment by ID with tracking events"""
    result = await db.execute(
        select(Shipment)
        .options(joinedload(Shipment.tracking_events))
        .where(Shipment.id == shipment_id, Shipment.deleted_at.is_(None))
    )
    shipment = result.unique().scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    return shipment


@router.get("/tracking/{tracking_code}", response_model=ShipmentDetailResponse)
async def get_shipment_by_tracking_code(
    tracking_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific shipment by tracking code with tracking events"""
    result = await db.execute(
        select(Shipment)
        .options(joinedload(Shipment.tracking_events))
        .where(Shipment.tracking_code == tracking_code, Shipment.deleted_at.is_(None))
    )
    shipment = result.unique().scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    return shipment


@router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    shipment_data: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_create_shipments)
):
    """Create a new shipment (requires can_create_shipments permission)"""
    # Check if tracking code already exists
    result = await db.execute(
        select(Shipment).where(
            Shipment.tracking_code == shipment_data.tracking_code,
            Shipment.deleted_at.is_(None)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tracking code already exists"
        )

    # Validate client_id if provided
    client = None
    if shipment_data.client_id:
        client_result = await db.execute(
            select(Client).where(
                Client.id == shipment_data.client_id,
                Client.deleted_at.is_(None)
            )
        )
        client = client_result.scalar_one_or_none()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client not found"
            )

    # Create new shipment
    shipment_dict = shipment_data.model_dump()
    new_shipment = Shipment(**shipment_dict, created_by=current_user.id)

    db.add(new_shipment)
    
    # Update client shipment count if client exists
    if client:
        client.total_shipments += 1
        if shipment_data.freight_cost:
            client.total_spent += shipment_data.freight_cost

    await db.commit()
    await db.refresh(new_shipment)

    return new_shipment


@router.patch("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(
    shipment_id: UUID,
    shipment_data: ShipmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_edit_shipments)
):
    """Update a shipment (requires can_edit_shipments permission)"""
    # Get shipment
    result = await db.execute(
        select(Shipment).where(Shipment.id == shipment_id, Shipment.deleted_at.is_(None))
    )
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    # Update fields
    update_data = shipment_data.model_dump(exclude_unset=True)
    
    # Check if tracking code is being changed and if it's available
    if "tracking_code" in update_data and update_data["tracking_code"] != shipment.tracking_code:
        code_result = await db.execute(
            select(Shipment).where(
                Shipment.tracking_code == update_data["tracking_code"],
                Shipment.deleted_at.is_(None)
            )
        )
        if code_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tracking code already in use"
            )

    # Validate client_id if being changed
    if "client_id" in update_data and update_data["client_id"]:
        client_result = await db.execute(
            select(Client).where(
                Client.id == update_data["client_id"],
                Client.deleted_at.is_(None)
            )
        )
        if not client_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client not found"
            )

    for field, value in update_data.items():
        setattr(shipment, field, value)

    await db.commit()
    await db.refresh(shipment)

    return shipment


@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(can_delete_shipments)
):
    """Soft delete a shipment (requires can_delete_shipments permission)"""
    result = await db.execute(
        select(Shipment).where(Shipment.id == shipment_id, Shipment.deleted_at.is_(None))
    )
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    # Soft delete
    shipment.soft_delete()
    await db.commit()

    return None


# Tracking Events
@router.post("/{shipment_id}/tracking-events", response_model=TrackingEventResponse, status_code=status.HTTP_201_CREATED)
async def add_tracking_event(
    shipment_id: UUID,
    event_data: TrackingEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a tracking event to a shipment"""
    # Verify shipment exists
    result = await db.execute(
        select(Shipment).where(Shipment.id == shipment_id, Shipment.deleted_at.is_(None))
    )
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    # Create tracking event
    event_dict = event_data.model_dump()
    event_dict["shipment_id"] = shipment_id
    new_event = ShipmentTrackingEvent(**event_dict)

    # Update shipment status if different
    if event_data.status != shipment.status:
        shipment.status = event_data.status

    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    return new_event


@router.get("/{shipment_id}/tracking-events", response_model=List[TrackingEventResponse])
async def list_tracking_events(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all tracking events for a shipment"""
    # Verify shipment exists
    result = await db.execute(
        select(Shipment).where(Shipment.id == shipment_id, Shipment.deleted_at.is_(None))
    )
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    # Get tracking events
    events_result = await db.execute(
        select(ShipmentTrackingEvent)
        .where(ShipmentTrackingEvent.shipment_id == shipment_id)
        .order_by(ShipmentTrackingEvent.occurred_at.desc())
    )
    events = events_result.scalars().all()

    return events
