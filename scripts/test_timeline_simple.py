"""
Teste do endpoint de tracking timeline
Executa uma consulta de teste diretamente no banco
"""
import asyncio
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.conn import AsyncSessionLocal
from app.models.shipment import Shipment, ShipmentTrackingEvent


async def test_timeline():
    """Testa a consulta de timeline"""
    async with AsyncSessionLocal() as db:
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
        
        print(f"✅ Encomenda encontrada: {shipment.id}")
        print(f"   📄 NF: {shipment.invoice_number}")
        print(f"   📦 Tracking: {shipment.tracking_code or 'N/A'}")
        print(f"   🏷️  Status: {shipment.status}")
        
        # Buscar eventos com occurrence_code
        result = await db.execute(
            select(ShipmentTrackingEvent)
            .options(joinedload(ShipmentTrackingEvent.occurrence_code))
            .where(ShipmentTrackingEvent.shipment_id == shipment.id)
            .order_by(ShipmentTrackingEvent.occurred_at.desc())
        )
        events = result.unique().scalars().all()
        
        print(f"\n📊 Total de eventos: {len(events)}")
        print("=" * 60)
        
        if not events:
            print("⚠️  Nenhum evento de rastreamento encontrado")
            print("\n💡 Dica: Execute o Prefect flow para capturar eventos")
            return
        
        for i, event in enumerate(events, 1):
            print(f"\n🔹 Evento #{i}")
            print(f"   Status: {event.status}")
            print(f"   Ocorrido em: {event.occurred_at}")
            
            if event.occurrence_code:
                print(f"   Código: [{event.occurrence_code.code}] {event.occurrence_code.description}")
            else:
                print(f"   Código: N/A")
            
            if event.description:
                print(f"   Descrição: {event.description}")
            
            if event.location:
                print(f"   📍 Local: {event.location}")
        
        print("\n" + "=" * 60)
        print(f"✅ Teste concluído! {len(events)} eventos processados")


if __name__ == "__main__":
    print("🚀 Iniciando teste do endpoint de tracking timeline...")
    print()
    asyncio.run(test_timeline())
