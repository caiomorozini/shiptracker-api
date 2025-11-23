"""
Tracking update routes for cronjob operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, List, Union
from uuid import UUID
from datetime import datetime
import json

from app.db.conn import get_db
from app.models.shipment import Shipment, ShipmentTrackingEvent
from app.models.occurrence_code import OccurrenceCode
from app.models.user import User
from app.schemas.tracking_update import (
    ShipmentTrackingUpdate,
    BulkTrackingUpdate,
    TrackingUpdateResponse,
    BulkTrackingUpdateResponse,
    TrackingEventData
)
from app.api.dependencies.auth import require_api_key, get_current_user_or_api_key
from loguru import logger

router = APIRouter(prefix="/tracking-updates", tags=["Tracking Updates"])


async def find_or_create_shipment(
    db: AsyncSession,
    tracking_data: ShipmentTrackingUpdate,
    current_user: Optional[User] = None
) -> Shipment:
    """Find existing shipment or create new one"""

    # Try to find by tracking_code first
    query = select(Shipment).where(
        Shipment.deleted_at.is_(None)
    )

    if tracking_data.tracking_code:
        query = query.where(Shipment.tracking_code == tracking_data.tracking_code)
    else:
        # Find by invoice_number + document
        query = query.where(
            and_(
                Shipment.invoice_number == tracking_data.invoice_number,
                Shipment.document == tracking_data.document
            )
        )

    result = await db.execute(query)
    shipment = result.scalar_one_or_none()

    if not shipment:
        # Create new shipment
        shipment = Shipment(
            tracking_code=tracking_data.tracking_code,
            invoice_number=tracking_data.invoice_number,
            document=tracking_data.document,
            carrier=tracking_data.carrier or "SSW",
            status=tracking_data.current_status or "pending",
            created_by=current_user.id if current_user else None
        )
        db.add(shipment)
        await db.flush()
        logger.info(f"Created new shipment: {shipment.id}")
    else:
        # Update existing shipment
        if tracking_data.tracking_code and not shipment.tracking_code:
            shipment.tracking_code = tracking_data.tracking_code

        if tracking_data.current_status:
            shipment.status = tracking_data.current_status

        logger.info(f"Found existing shipment: {shipment.id}")

    return shipment


async def create_or_update_tracking_event(
    db: AsyncSession,
    shipment: Shipment,
    event_data: TrackingEventData
) -> tuple[ShipmentTrackingEvent, bool]:
    """Create or update a tracking event. Returns (event, is_new)"""

    # Check if event already exists (same shipment, occurred_at, and status)
    query = select(ShipmentTrackingEvent).where(
        and_(
            ShipmentTrackingEvent.shipment_id == shipment.id,
            ShipmentTrackingEvent.occurred_at == event_data.occurred_at,
            ShipmentTrackingEvent.status == event_data.status
        )
    )

    result = await db.execute(query)
    existing_event = result.scalar_one_or_none()

    if existing_event:
        # Update existing event
        existing_event.description = event_data.description
        existing_event.location = event_data.location

        # Validate and set occurrence_code (max 10 chars)
        if event_data.occurrence_code:
            existing_event.occurrence_code = event_data.occurrence_code[:10] if event_data.occurrence_code else None

        existing_event.unit = event_data.unit
        existing_event.protocol = event_data.protocol

        if event_data.raw_data:
            existing_event.carrier_raw_data = event_data.raw_data

        logger.debug(f"Updated tracking event: {existing_event.id}")
        return existing_event, False
    else:
        # Create new event
        # Validate occurrence_code length (max 10 chars as per DB schema)
        validated_occurrence_code = event_data.occurrence_code[:10] if event_data.occurrence_code else None

        new_event = ShipmentTrackingEvent(
            shipment_id=shipment.id,
            status=event_data.status,
            description=event_data.description,
            location=event_data.location,
            occurrence_code=validated_occurrence_code,
            unit=event_data.unit,
            protocol=event_data.protocol,
            occurred_at=event_data.occurred_at,
            carrier_raw_data=event_data.raw_data
        )
        db.add(new_event)
        logger.debug(f"Created new tracking event for shipment {shipment.id}")
        return new_event, True


@router.post("/shipment", response_model=TrackingUpdateResponse)
async def update_shipment_tracking(
    tracking_data: ShipmentTrackingUpdate,
    db: AsyncSession = Depends(get_db),
    auth: Union[User, str] = Depends(get_current_user_or_api_key)
):
    """
    Update or create a shipment with tracking events.
    Accepts both JWT token (for users) and API Key (for cronjobs).
    """
    try:
        errors = []

        # Find or create shipment (without current_user for API key auth)
        shipment = await find_or_create_shipment(db, tracking_data, None)

        events_created = 0
        events_updated = 0
        has_finalization_event = False

        # Get finalization codes for checking
        # Process that indicate finalization: 'entrega', 'finalizadora'
        from app.models.occurrence_code import OccurrenceCode
        finalization_query = select(OccurrenceCode.code).where(
            OccurrenceCode.process.in_(["entrega", "finalizadora"])
        )
        finalization_result = await db.execute(finalization_query)
        finalization_codes = [row[0] for row in finalization_result.all()]

        # Process tracking events
        for event_data in tracking_data.events:
            try:
                event, is_new = await create_or_update_tracking_event(
                    db, shipment, event_data
                )

                if is_new:
                    events_created += 1
                else:
                    events_updated += 1

                # Check if this event has a finalization occurrence code
                if event_data.occurrence_code and event_data.occurrence_code in finalization_codes:
                    has_finalization_event = True

            except Exception as e:
                error_msg = f"Error processing event: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Update shipment status based on finalization
        if has_finalization_event:
            shipment.status = "delivered"
            logger.info(f"Shipment {shipment.id} marked as delivered (finalization event detected)")
        elif tracking_data.current_status:
            # Update to current status if no finalization
            shipment.status = tracking_data.current_status.lower().replace(" ", "_")

        # Commit all changes
        await db.commit()
        await db.refresh(shipment)

        return TrackingUpdateResponse(
            success=True,
            message=f"Shipment tracking updated successfully",
            shipment_id=str(shipment.id),
            events_created=events_created,
            events_updated=events_updated,
            errors=errors
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating shipment tracking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating shipment: {str(e)}"
        )


@router.post("/bulk", response_model=BulkTrackingUpdateResponse)
async def bulk_update_tracking(
    bulk_data: BulkTrackingUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(require_api_key)
):
    """
    Bulk update multiple shipments with tracking events.
    This endpoint is optimized for batch processing from cronjobs.
    """
    results = []
    successful = 0
    failed = 0

    for tracking_data in bulk_data.shipments:
        try:
            result = await update_shipment_tracking(
                tracking_data=tracking_data,
                db=db
            )
            results.append(result)
            successful += 1
        except Exception as e:
            error_msg = f"Failed to update shipment {tracking_data.invoice_number}: {str(e)}"
            logger.error(error_msg)
            results.append(TrackingUpdateResponse(
                success=False,
                message=error_msg,
                errors=[str(e)]
            ))
            failed += 1

    return BulkTrackingUpdateResponse(
        total_processed=len(bulk_data.shipments),
        successful=successful,
        failed=failed,
        results=results
    )


@router.get("/occurrence-codes", response_model=List[dict])
async def get_occurrence_codes_mapping(
    db: AsyncSession = Depends(get_db),
    auth: Union[User, str] = Depends(get_current_user_or_api_key)
):
    """
    Get all occurrence codes for mapping in the scraper.
    Returns a simplified list for easy lookup.
    Accepts both JWT token (for users) and API Key (for cronjobs).
    """
    query = select(OccurrenceCode)
    result = await db.execute(query)
    codes = result.scalars().all()

    return [
        {
            "code": code.code,
            "description": code.description,
            "type": code.type,
            "process": code.process
        }
        for code in codes
    ]


@router.get("/pending-shipments", response_model=List[dict])
async def get_pending_shipments_for_sync(
    db: AsyncSession = Depends(get_db),
    auth: Union[User, str] = Depends(get_current_user_or_api_key),
    limit: int = 100
):
    """
    Get active shipments for cronjob synchronization.
    Returns shipments that are not delivered (status != 'delivered').
    This is a simplified version that works reliably.
    Accepts both JWT token (for users) and API Key (for cronjobs).
    """
    # Simple query: get all shipments that are not delivered
    query = select(Shipment).where(
        and_(
            Shipment.deleted_at.is_(None),
            Shipment.status != "delivered"
        )
    ).limit(limit)

    result = await db.execute(query)
    shipments = result.scalars().all()

    return [
        {
            "id": str(shipment.id),
            "tracking_code": shipment.tracking_code,
            "invoice_number": shipment.invoice_number,
            "document": shipment.document,
            "carrier": shipment.carrier,
            "status": shipment.status
        }
        for shipment in shipments
    ]
