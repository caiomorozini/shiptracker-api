"""
Shipment management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import joinedload, selectinload
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
from app.models.enums import get_all_statuses

router = APIRouter(prefix="/shipments", tags=["Shipments"])


@router.get("/metadata")
async def get_shipments_metadata(
    current_user: User = Depends(get_current_user)
):
    """Get metadata for shipments (available statuses, carriers, etc)"""
    return {
        "statuses": get_all_statuses(),
        "carriers": [
            {"value": "SSW", "label": "SSW"},
            {"value": "Correios", "label": "Correios"},
            {"value": "Jadlog", "label": "Jadlog"},
            {"value": "Total Express", "label": "Total Express"},
            {"value": "Azul Cargo", "label": "Azul Cargo"},
        ]
    }


@router.get("", response_model=List[ShipmentResponse])
async def list_shipments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[List[str]] = Query(None, alias="status"),
    carrier: Optional[str] = None,
    client_id: Optional[UUID] = None,
    origin_city: Optional[str] = None,
    destination_city: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    include_events: bool = Query(False, description="Include tracking events"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all shipments with optional filters"""
    query = select(Shipment).where(Shipment.deleted_at.is_(None))
    
    # Incluir eventos de rastreamento se solicitado (ordenados por data desc)
    if include_events:
        query = query.options(selectinload(Shipment.tracking_events))

    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Shipment.tracking_code.ilike(search_filter),
                Shipment.invoice_number.ilike(search_filter),
                Shipment.document.ilike(search_filter),
                Shipment.description.ilike(search_filter)
            )
        )

    if status_filter and len(status_filter) > 0:
        query = query.where(Shipment.status.in_(status_filter))

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
    status_filter: Optional[List[str]] = Query(None, alias="status"),
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

    if status_filter and len(status_filter) > 0:
        query = query.where(Shipment.status.in_(status_filter))

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
    # Check if tracking code already exists (if provided)
    if shipment_data.tracking_code:
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
    
    # Check if combination of document + invoice_number already exists
    result = await db.execute(
        select(Shipment).where(
            Shipment.document == shipment_data.document,
            Shipment.invoice_number == shipment_data.invoice_number,
            Shipment.deleted_at.is_(None)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A shipment with this document and invoice number already exists"
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


@router.get("/{shipment_id}/tracking-timeline")
async def get_tracking_timeline(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get formatted tracking timeline for frontend display"""
    from app.models.occurrence_code import OccurrenceCode
    
    # Get shipment with tracking events and occurrence codes
    result = await db.execute(
        select(Shipment)
        .options(selectinload(Shipment.tracking_events))
        .where(Shipment.id == shipment_id, Shipment.deleted_at.is_(None))
    )
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    # Get all occurrence codes for lookup
    codes_result = await db.execute(select(OccurrenceCode))
    occurrence_codes = {code.code: code for code in codes_result.scalars().all()}

    # Sort events by date (most recent first)
    events = sorted(shipment.tracking_events, key=lambda e: e.occurred_at, reverse=True)
    
    # Build timeline items
    timeline_items = []
    for i, event in enumerate(events):
        occurrence_info = None
        if event.occurrence_code:  # occurrence_code is the string (code)
            occ = occurrence_codes.get(event.occurrence_code)
            if occ:
                occurrence_info = {
                    "code": occ.code,
                    "description": occ.description,
                    "type": occ.type,
                    "process": occ.process
                }
        
        timeline_items.append({
            "id": str(event.id),
            "status": event.status,
            "description": event.description,
            "location": event.location,
            "unit": event.unit,
            "occurrence_code": occurrence_info,  # Send full object to frontend
            "occurred_at": event.occurred_at.isoformat(),
            "is_current": i == 0  # First event (most recent) is current
        })

    # Calculate statistics
    first_event_date = events[-1].occurred_at if events else None
    last_event_date = events[0].occurred_at if events else None
    
    return {
        "shipment_id": str(shipment.id),
        "tracking_code": shipment.tracking_code,
        "invoice_number": shipment.invoice_number,
        "carrier": shipment.carrier,
        "current_status": shipment.status,
        "total_events": len(events),
        "first_event_date": first_event_date.isoformat() if first_event_date else None,
        "last_event_date": last_event_date.isoformat() if last_event_date else None,
        "estimated_delivery": shipment.estimated_delivery_date.isoformat() if shipment.estimated_delivery_date else None,
        "actual_delivery": shipment.actual_delivery_date.isoformat() if shipment.actual_delivery_date else None,
        "events": timeline_items
    }


@router.get("/{shipment_id}/tracking-stats")
async def get_tracking_stats(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tracking statistics for a shipment"""
    # Verify shipment exists
    result = await db.execute(
        select(Shipment)
        .options(selectinload(Shipment.tracking_events))
        .where(Shipment.id == shipment_id, Shipment.deleted_at.is_(None))
    )
    shipment = result.scalar_one_or_none()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    events = shipment.tracking_events
    
    # Calculate statistics
    total_events = len(events)
    unique_locations = len(set(e.location for e in events if e.location))
    
    # Calculate transit days
    transit_days = None
    if events:
        sorted_events = sorted(events, key=lambda e: e.occurred_at)
        first_date = sorted_events[0].occurred_at
        last_date = sorted_events[-1].occurred_at
        transit_days = (last_date - first_date).days
    
    last_update = max((e.occurred_at for e in events), default=None)
    
    # Status history (count of each status)
    status_counts = {}
    for event in events:
        status_counts[event.status] = status_counts.get(event.status, 0) + 1
    
    status_history = [
        {
            "status": status,
            "count": count,
            "percentage": round((count / total_events * 100), 2) if total_events > 0 else 0
        }
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return {
        "total_events": total_events,
        "unique_locations": unique_locations,
        "transit_days": transit_days,
        "last_update": last_update.isoformat() if last_update else None,
        "status_history": status_history
    }


@router.get("/overview/statistics")
async def get_overview_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365, description="Number of days to include in statistics")
):
    """Get overview statistics for dashboard"""
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Total shipments (all time)
    total_query = select(func.count(Shipment.id)).where(Shipment.deleted_at.is_(None))
    total_result = await db.execute(total_query)
    total_shipments = total_result.scalar_one()
    
    # Recent shipments (within specified days)
    recent_query = select(func.count(Shipment.id)).where(
        Shipment.deleted_at.is_(None),
        Shipment.created_at >= cutoff_date
    )
    recent_result = await db.execute(recent_query)
    recent_shipments = recent_result.scalar_one()
    
    # By status
    status_counts = {}
    for status_value in ["pending", "in_transit", "delivered", "delayed", "cancelled", "returned"]:
        status_query = select(func.count(Shipment.id)).where(
            Shipment.deleted_at.is_(None),
            Shipment.status == status_value
        )
        status_result = await db.execute(status_query)
        status_counts[status_value] = status_result.scalar_one()
    
    # By carrier
    carrier_query = select(
        Shipment.carrier,
        func.count(Shipment.id).label("count")
    ).where(
        Shipment.deleted_at.is_(None)
    ).group_by(Shipment.carrier)
    
    carrier_result = await db.execute(carrier_query)
    carrier_stats = [
        {"carrier": row[0], "count": row[1]}
        for row in carrier_result.all()
    ]
    
    # Average delivery time (for delivered shipments)
    delivered_shipments_query = select(Shipment).where(
        Shipment.deleted_at.is_(None),
        Shipment.status == "delivered",
        Shipment.actual_delivery_date.isnot(None)
    )
    delivered_result = await db.execute(delivered_shipments_query)
    delivered_shipments = delivered_result.scalars().all()
    
    avg_delivery_days = None
    if delivered_shipments:
        total_days = sum(
            (s.actual_delivery_date - s.created_at.date()).days
            for s in delivered_shipments
            if s.actual_delivery_date
        )
        avg_delivery_days = round(total_days / len(delivered_shipments), 1)
    
    return {
        "total_shipments": total_shipments,
        "recent_shipments": recent_shipments,
        "recent_period_days": days,
        "by_status": status_counts,
        "by_carrier": carrier_stats,
        "average_delivery_days": avg_delivery_days,
        "last_updated": datetime.now().isoformat()
    }


@router.get("/search/tracking")
async def search_by_tracking(
    q: str = Query(..., min_length=3, description="Tracking code, invoice number, or document"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Quick search shipments by tracking code, invoice, or document"""
    search_term = f"%{q}%"
    
    query = select(Shipment).where(
        Shipment.deleted_at.is_(None),
        or_(
            Shipment.tracking_code.ilike(search_term),
            Shipment.invoice_number.ilike(search_term),
            Shipment.document.ilike(search_term)
        )
    ).limit(10)
    
    result = await db.execute(query)
    shipments = result.scalars().all()
    
    return [
        {
            "id": str(s.id),
            "tracking_code": s.tracking_code,
            "invoice_number": s.invoice_number,
            "document": s.document,
            "carrier": s.carrier,
            "status": s.status,
            "created_at": s.created_at.isoformat()
        }
        for s in shipments
    ]
