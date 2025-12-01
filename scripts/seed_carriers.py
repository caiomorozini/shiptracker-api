#!/usr/bin/env python3
"""
Script para popular transportadoras padrão no banco de dados
Execute este script após rodar a migration
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.carrier import Carrier
from app.core.config import get_app_settings
import uuid

def seed_carriers():
    """Cria as transportadoras padrão"""
    settings = get_app_settings()
    engine = create_engine(str(settings.database_url))
    
    default_carriers = [
        {"name": "SSW", "code": "ssw", "color": "#FF6B35"},
        {"name": "Correios", "code": "correios", "color": "#FFCC00"},
        {"name": "SEDEX", "code": "sedex", "color": "#003DA5"},
        {"name": "Jadlog", "code": "jadlog", "color": "#1E90FF"},
        {"name": "Loggi", "code": "loggi", "color": "#FF6B00"},
    ]
    
    with Session(engine) as session:
        # Verifica se já existem transportadoras
        existing_count = session.query(Carrier).count()
        if existing_count > 0:
            print(f"✅ Já existem {existing_count} transportadoras cadastradas. Pulando seed.")
            return
        
        print("🚀 Criando transportadoras padrão...")
        
        for carrier_data in default_carriers:
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
        
        session.commit()
        print(f"\n✅ {len(default_carriers)} transportadoras criadas com sucesso!")

if __name__ == "__main__":
    try:
        seed_carriers()
    except Exception as e:
        print(f"❌ Erro ao criar transportadoras: {e}")
        sys.exit(1)
