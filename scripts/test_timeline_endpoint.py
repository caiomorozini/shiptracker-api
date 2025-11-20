#!/usr/bin/env python3
"""
Script para testar o endpoint de tracking timeline
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.conn import get_db
from app.models.shipment import Shipment, ShipmentTrackingEvent
from app.models.occurrence_code import OccurrenceCode


async def test_timeline():
    """Testa o endpoint de timeline"""
    async for db in get_db():
        # Buscar uma encomenda com eventos
        result = await db.execute(
            select(Shipment)
            .where(Shipment.deleted_at.is_(None))
            .limit(1)
        )
        shipment = result.scalar_one_or_none()
        
        if not shipment:
            print("❌ Nenhuma encomenda encontrada")
            return
        
        print(f"✅ Encomenda encontrada: {shipment.id} - NF: {shipment.invoice_number}")
        
        # Buscar eventos com occurrence_code
        result = await db.execute(
            select(ShipmentTrackingEvent)
            .options(joinedload(ShipmentTrackingEvent.occurrence_code))
            .where(ShipmentTrackingEvent.shipment_id == shipment.id)
            .order_by(ShipmentTrackingEvent.occurred_at.desc())
        )
        events = result.unique().scalars().all()
        
        print(f"\n📦 Total de eventos: {len(events)}")
        
        for event in events:
            print(f"\n  🔹 Status: {event.status}")
            print(f"     Ocorrido em: {event.occurred_at}")
            if event.occurrence_code:
                print(f"     Código: {event.occurrence_code.code} - {event.occurrence_code.description}")
            if event.description:
                print(f"     Descrição: {event.description}")
            if event.location:
                print(f"     Local: {event.location}")
        
        return


if __name__ == "__main__":
    asyncio.run(test_timeline())
