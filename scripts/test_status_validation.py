#!/usr/bin/env python3
"""
Script para testar a validação de status nos schemas.
Garante que valores legacy, mal formatados e inválidos são normalizados corretamente.
"""

from app.schemas.shipment import ShipmentCreate, ShipmentUpdate, TrackingEventCreate
from app.models.enums import ShipmentStatus
from datetime import datetime
from uuid import uuid4


def test_shipment_status_validation():
    """Testa validação de status em shipments"""

    print("=" * 60)
    print("TESTE: Validação de Status em Shipments")
    print("=" * 60)

    test_cases = [
        # (input_status, expected_output, description)
        ("delivered", "delivered", "Status padrão válido"),
        ("in_transit", "in_transit", "Status padrão válido"),
        ("entregue", "delivered", "Status em português"),
        ("em_transito", "in_transit", "Status em português"),
        ("em_transito_para_a_unidade_destino", "in_transit", "Status mal formatado dos Correios"),
        ("objeto_entregue_ao_destinatario", "delivered", "Status longo dos Correios"),
        ("STATUS_INVALIDO_XYZ", "pending", "Status inválido - fallback"),
        ("", "pending", "Status vazio - fallback"),
    ]

    passed = 0
    failed = 0

    for input_status, expected, description in test_cases:
        try:
            shipment = ShipmentCreate(
                invoice_number="12345",
                document="12345678901",
                carrier="correios",
                status=input_status
            )

            if shipment.status == expected:
                print(f"✅ {description}")
                print(f"   Input: '{input_status}' → Output: '{shipment.status}'")
                passed += 1
            else:
                print(f"❌ {description}")
                print(f"   Input: '{input_status}'")
                print(f"   Expected: '{expected}', Got: '{shipment.status}'")
                failed += 1

        except Exception as e:
            print(f"❌ {description}")
            print(f"   Input: '{input_status}'")
            print(f"   Error: {e}")
            failed += 1

        print()

    print(f"Resultado: {passed} passou, {failed} falhou")
    print()

    return failed == 0


def test_tracking_event_status_validation():
    """Testa validação de status em eventos de rastreio"""

    print("=" * 60)
    print("TESTE: Validação de Status em Eventos de Rastreio")
    print("=" * 60)

    test_cases = [
        ("out_for_delivery", "out_for_delivery", "Status válido"),
        ("objeto_saiu_para_entrega_ao_destinatario", "out_for_delivery", "Status Correios"),
        ("tentativa_de_entrega_nao_realizada", "failed_delivery", "Tentativa falha"),
        ("STATUS_DESCONHECIDO", "pending", "Status inválido - fallback"),
    ]

    passed = 0
    failed = 0

    for input_status, expected, description in test_cases:
        try:
            event = TrackingEventCreate(
                shipment_id=uuid4(),
                status=input_status,
                occurred_at=datetime.now()
            )

            if event.status == expected:
                print(f"✅ {description}")
                print(f"   Input: '{input_status}' → Output: '{event.status}'")
                passed += 1
            else:
                print(f"❌ {description}")
                print(f"   Input: '{input_status}'")
                print(f"   Expected: '{expected}', Got: '{event.status}'")
                failed += 1

        except Exception as e:
            print(f"❌ {description}")
            print(f"   Input: '{input_status}'")
            print(f"   Error: {e}")
            failed += 1

        print()

    print(f"Resultado: {passed} passou, {failed} falhou")
    print()

    return failed == 0


def test_enum_from_string():
    """Testa o método from_string do enum"""

    print("=" * 60)
    print("TESTE: Método from_string do ShipmentStatus")
    print("=" * 60)

    test_cases = [
        ("delivered", ShipmentStatus.DELIVERED),
        ("entregue", ShipmentStatus.DELIVERED),
        ("em_transito_para_a_unidade_destino", ShipmentStatus.IN_TRANSIT),
        ("objeto_postado", ShipmentStatus.POSTED),
        ("STATUS_INVALIDO", ShipmentStatus.PENDING),  # Fallback
    ]

    passed = 0
    failed = 0

    for input_str, expected_enum in test_cases:
        result = ShipmentStatus.from_string(input_str)

        if result == expected_enum:
            print(f"✅ '{input_str}' → {result.value}")
            passed += 1
        else:
            print(f"❌ '{input_str}'")
            print(f"   Expected: {expected_enum.value}, Got: {result.value}")
            failed += 1

    print()
    print(f"Resultado: {passed} passou, {failed} falhou")
    print()

    return failed == 0


if __name__ == "__main__":
    print("\n🧪 SUITE DE TESTES: Validação de Status\n")

    results = []

    # Executa todos os testes
    results.append(test_enum_from_string())
    results.append(test_shipment_status_validation())
    results.append(test_tracking_event_status_validation())

    # Resumo final
    print("=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)

    if all(results):
        print("✅ Todos os testes passaram!")
        exit(0)
    else:
        print("❌ Alguns testes falharam")
        exit(1)
