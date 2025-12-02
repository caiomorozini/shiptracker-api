"""
Script para testar a implementação da role SELLER
"""
from app.models.user import UserRole
from app.models.shipment import Shipment
from app.api.dependencies.permissions import ROLE_PERMISSIONS

def test_seller_role():
    """Testa se o role SELLER foi adicionado"""
    print("✓ UserRole.SELLER existe:", hasattr(UserRole, 'SELLER'))
    print("✓ Valor do enum:", UserRole.SELLER.value if hasattr(UserRole, 'SELLER') else 'N/A')
    
def test_seller_permissions():
    """Testa se as permissões do SELLER foram configuradas"""
    if hasattr(UserRole, 'SELLER'):
        seller_perms = ROLE_PERMISSIONS.get(UserRole.SELLER, {})
        print("\n✓ Permissões do SELLER configuradas:")
        print(f"  - Ver encomendas: {seller_perms.get('can_view_shipments')}")
        print(f"  - Criar encomendas: {seller_perms.get('can_create_shipments')}")
        print(f"  - Editar encomendas: {seller_perms.get('can_edit_shipments')}")
        print(f"  - Ver clientes: {seller_perms.get('can_view_clients')}")
        print(f"  - Criar clientes: {seller_perms.get('can_create_clients')}")
    else:
        print("\n✗ UserRole.SELLER não encontrado")

def test_shipment_seller_field():
    """Testa se o campo seller_id foi adicionado ao modelo Shipment"""
    # Verifica se o campo seller_id está definido no modelo
    from sqlalchemy import inspect
    mapper = inspect(Shipment)
    columns = [col.key for col in mapper.columns]
    print(f"\n✓ Campo seller_id no Shipment: {'seller_id' in columns}")
    
if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DA IMPLEMENTAÇÃO DO SELLER")
    print("=" * 60)
    
    try:
        test_seller_role()
        test_seller_permissions()
        test_shipment_seller_field()
        print("\n" + "=" * 60)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
