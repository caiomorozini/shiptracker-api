#!/usr/bin/env python3
"""
Script para verificar e criar transportadoras em produção
Execute: python scripts/check_and_seed_carriers_prod.py
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.carrier import Carrier
from app.core.config import get_app_settings
import uuid

async def check_and_seed_carriers():
    """Verifica e cria as transportadoras padrão se necessário"""
    settings = get_app_settings()
    
    # Criar engine assíncrono
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    default_carriers = [
        {"name": "SSW", "code": "ssw", "color": "#FF6B35"},
        {"name": "Correios", "code": "correios", "color": "#FFCC00"},
        {"name": "SEDEX", "code": "sedex", "color": "#003DA5"},
        {"name": "Jadlog", "code": "jadlog", "color": "#1E90FF"},
        {"name": "Loggi", "code": "loggi", "color": "#FF6B00"},
        {"name": "Total Express", "code": "total-express", "color": "#E74C3C"},
        {"name": "Azul Cargo", "code": "azul-cargo", "color": "#3498DB"},
    ]
    
    async with async_session() as session:
        # Verifica quantas transportadoras existem
        result = await session.execute(select(Carrier))
        existing_carriers = result.scalars().all()
        existing_count = len(existing_carriers)
        
        print(f"📊 Transportadoras existentes: {existing_count}")
        
        if existing_count > 0:
            print("\n✅ Transportadoras cadastradas:")
            for carrier in existing_carriers:
                status = "✓ Ativa" if carrier.active else "✗ Inativa"
                default = "(Padrão)" if carrier.is_default else ""
                print(f"  • {carrier.name} ({carrier.code}) - {status} {default}")
        
        # Verifica se precisa adicionar novas
        existing_codes = {c.code for c in existing_carriers}
        missing_carriers = [c for c in default_carriers if c["code"] not in existing_codes]
        
        if missing_carriers:
            print(f"\n🚀 Adicionando {len(missing_carriers)} transportadoras faltantes...")
            
            for carrier_data in missing_carriers:
                carrier = Carrier(
                    id=uuid.uuid4(),
                    name=carrier_data["name"],
                    code=carrier_data["code"],
                    color=carrier_data["color"],
                    active=True,
                    is_default=True
                )
                session.add(carrier)
                print(f"  ✓ {carrier.name} ({carrier.code})")
            
            await session.commit()
            print(f"\n✅ Transportadoras adicionadas com sucesso!")
        else:
            print("\n✅ Todas as transportadoras padrão já estão cadastradas!")
    
    await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(check_and_seed_carriers())
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
