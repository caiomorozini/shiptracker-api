# ShipTracker API

API REST para gerenciamento de encomendas e rastreamento de entregas.

## 🚀 Tecnologias

- **FastAPI** - Framework web assíncrono
- **SQLAlchemy** - ORM para PostgreSQL
- **Alembic** - Migrations de banco de dados
- **PostgreSQL** - Banco de dados principal
- **UV** - Gerenciador de pacotes Python

## 📁 Estrutura do Projeto

```
shiptracker-api/
├── app/                    # Código fonte da aplicação
│   ├── api/               # Endpoints e rotas
│   │   ├── routes/       # Rotas organizadas por domínio
│   │   └── dependencies/ # Dependências de autenticação e permissões
│   ├── core/             # Configurações centrais
│   ├── db/               # Configuração de banco de dados
│   ├── models/           # Modelos SQLAlchemy
│   └── schemas/          # Schemas Pydantic
├── alembic/              # Migrations do banco
├── scripts/              # Scripts utilitários e de desenvolvimento
│   ├── old_airflow/     # DAGs antigos (deprecado)
│   └── *.py             # Scripts de seed, testes, etc
└── tests/                # Testes automatizados
```

## 🛠️ Setup

### 1. Configurar ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar variáveis de ambiente
nano .env
```

### 2. Iniciar banco de dados

```bash
# Docker
docker-compose up -d

# Ou manual (PostgreSQL precisa estar instalado)
```

### 3. Executar migrations

```bash
alembic upgrade head
```

### 4. Popular dados iniciais

```bash
# Códigos de ocorrência (obrigatório)
python scripts/seed_occurrence_codes.py

# Dados de teste (opcional)
python scripts/create_test_data.py
```

## ▶️ Executar API

```bash
# Desenvolvimento
uv run uvicorn app.main:app --reload

# Produção
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Acesse: http://localhost:8000/docs

## 🗃️ Comandos Alembic

```bash
# Criar nova migration
alembic revision --autogenerate -m "descrição"

# Aplicar migrations
alembic upgrade head

# Reverter última migration
alembic downgrade -1

# Ver histórico
alembic history
```

## 🧪 Scripts Utilitários

Ver documentação completa em [`scripts/README.md`](scripts/README.md)

```bash
# Popular occurrence_codes
python scripts/seed_occurrence_codes.py

# Criar dados de teste
python scripts/create_test_data.py

# Verificar códigos
python scripts/check_codes.py

# Testar timeline
python scripts/test_timeline_simple.py
```

## 📦 Docker

```bash
# Iniciar containers
docker-compose up -d

# Parar containers
docker-compose down

# Ver logs
docker-compose logs -f api
```

### Setar revisão

```
alembic stamp ${codigo_revisao}
```

### Checar qual revisão estou

```
alembic current
```

onde ${codigo_revisao} é o código da revisão que você deseja fazer o upgrade ou downgrade (para o mais recente, colocar head)