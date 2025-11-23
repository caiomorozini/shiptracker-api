#!/usr/bin/env python3
"""
Testa a validação de status em dados vindos do Prefect scraper
"""

from app.schemas.tracking_update import ShipmentTrackingUpdate, TrackingEventData
from datetime import datetime


def test_prefect_scraped_data():
    """Simula dados que vem do scraper do Prefect/SSW"""
    
    print("=" * 60)
    print("TESTE: Validação de Dados do Prefect Scraper")
    print("=" * 60)
    
    # Simula payload real que vem do Prefect (com status em português)
    prefect_payload = {
        "tracking_code": None,
        "invoice_number": "123456",
        "document": "12345678000190",
        "carrier": "SSW",
        "current_status": "Objeto entregue ao destinatário",  # Status em português
        "events": [
            {
                "occurrence_code": "01",
                "status": "Objeto entregue ao destinatário",  # Status em português
                "description": "Objeto entregue ao destinatário  01",
                "location": "SAO PAULO",
                "unit": "1234",
                "occurred_at": "2025-11-20T10:30:00"
            },
            {
                "occurrence_code": "09",
                "status": "Objeto saiu para entrega ao destinatário",  # Status em português
                "description": "Objeto saiu para entrega ao destinatário  09",
                "location": "SAO PAULO",
                "unit": "1234",
                "occurred_at": "2025-11-20T08:00:00"
            },
            {
                "occurrence_code": "CD",
                "status": "Em trânsito para a unidade destino",  # Status mal formatado
                "description": "Em trânsito para a unidade destino  CD",
                "location": "CURITIBA",
                "unit": "5678",
                "occurred_at": "2025-11-19T14:00:00"
            }
        ],
        "last_update": "2025-11-20T10:35:00"
    }
    
    try:
        # Tenta criar o schema (validação automática)
        validated = ShipmentTrackingUpdate(**prefect_payload)
        
        print(f"\n✅ Payload validado com sucesso!\n")
        
        # Verifica se current_status foi normalizado
        print(f"📦 Status Atual:")
        print(f"   Original: \"{prefect_payload['current_status']}\"")
        print(f"   Normalizado: \"{validated.current_status}\"")
        
        # Verifica se eventos foram normalizados
        print(f"\n📋 Eventos ({len(validated.events)}):")
        for i, (original, validated_event) in enumerate(zip(prefect_payload['events'], validated.events), 1):
            print(f"\n   Evento {i}:")
            print(f"   Original: \"{original['status']}\"")
            print(f"   Normalizado: \"{validated_event.status}\"")
        
        # Testa casos específicos
        print(f"\n🧪 Verificações:")
        
        # 1. Status atual deve ser "delivered"
        assert validated.current_status == "delivered", f"Expected 'delivered', got '{validated.current_status}'"
        print(f"   ✓ Status atual = delivered")
        
        # 2. Primeiro evento deve ser "delivered"
        assert validated.events[0].status == "delivered", f"Expected 'delivered', got '{validated.events[0].status}'"
        print(f"   ✓ Evento 1 = delivered")
        
        # 3. Segundo evento deve ser "out_for_delivery"
        assert validated.events[1].status == "out_for_delivery", f"Expected 'out_for_delivery', got '{validated.events[1].status}'"
        print(f"   ✓ Evento 2 = out_for_delivery")
        
        # 4. Terceiro evento deve ser "in_transit"
        assert validated.events[2].status == "in_transit", f"Expected 'in_transit', got '{validated.events[2].status}'"
        print(f"   ✓ Evento 3 = in_transit")
        
        print(f"\n{'='*60}")
        print("✅ TESTE PASSOU - Prefect scraper está protegido!")
        print("='*60}")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = test_prefect_scraped_data()
    sys.exit(0 if success else 1)
