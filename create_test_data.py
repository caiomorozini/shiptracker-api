import asyncio
from app.db.conn import get_session
from app.models.shipment import Shipment
from app.models.client import Client
from app.models.user import User
from datetime import datetime, timedelta
import uuid

async def create_test_data():
    async for session in get_session():
        try:
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.email == "test@test.com"))
            user = result.scalar_one_or_none()

            if not user:
                print("Usuário test@test.com não encontrado!")
                return

            client = Client(
                id=str(uuid.uuid4()),
                name="Cliente Teste",
                email="cliente@test.com",
                phone="+55 11 99999-9999",
                city="São Paulo",
                state="SP",
                country="BR",
                is_favorite=False,
                is_vip=True,
                total_shipments=3,
                total_spent=105.00,
                user_id=user.id
            )
            session.add(client)
            await session.flush()

            shipments_data = [
                ("BR123456789BR", "correios", "in_transit", "São Paulo", "SP", "Rio de Janeiro", "RJ", 2.5, 45.00, 250.00, "Notebook Dell"),
                ("SSW987654321BR", "ssw", "delivered", "Curitiba", "PR", "Florianópolis", "SC", 1.2, 32.00, 150.00, "Smartphone Samsung"),
                ("JL456789012BR", "jadlog", "pending", "Belo Horizonte", "MG", "Brasília", "DF", 0.8, 28.00, 80.00, "Livros técnicos"),
            ]

            for (code, carrier, status, orig_city, orig_state, dest_city, dest_state, weight, freight, value, desc) in shipments_data:
                shipment = Shipment(
                    tracking_code=code,
                    carrier=carrier,
                    status=status,
                    origin_city=orig_city,
                    origin_state=orig_state,
                    destination_city=dest_city,
                    destination_state=dest_state,
                    weight_kg=weight,
                    freight_cost=freight,
                    declared_value=value,
                    description=desc,
                    client_id=client.id,
                    created_by=user.id,
                    estimated_delivery_date=datetime.now() + timedelta(days=5)
                )
                session.add(shipment)

            await session.commit()
            print("✅ Dados criados!")
            print(f"   Cliente: {client.name} ({client.id})")
            print(f"   3 encomendas adicionadas")

        except Exception as e:
            await session.rollback()
            print(f"❌ Erro: {e}")
        finally:
            break

asyncio.run(create_test_data())
