# 🚀 Guia Rápido - ShipTracker API

## ⚡ Início Rápido

### 1. Configurar ambiente
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar variáveis necessárias
nano .env
```

### 2. Iniciar serviços Docker
```bash
# Iniciar todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps
```

### 3. Instalar dependências
```bash
# Instalar com pip
pip install -e .

# OU com dependências de desenvolvimento
pip install -e ".[dev]"
```

### 4. Executar migrations
```bash
# Criar tabelas no banco
alembic upgrade head
```

### 5. Iniciar aplicação
```bash
# Modo desenvolvimento
uvicorn app.main:app --reload

# OU usando make
make run
```

## 📊 Acessos

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **Swagger Docs** | http://localhost:8000/docs | - |
| **ReDoc** | http://localhost:8000/redoc | - |
| **pgAdmin** | http://localhost:5050 | admin@shiptracker.com / admin |
| **Mongo Express** | http://localhost:8081 | admin / admin |
| **Redis Commander** | http://localhost:8082 | - |
| **PostgreSQL** | localhost:5432 | admin / admin |
| **MongoDB** | localhost:27017 | admin / admin |
| **Redis** | localhost:6379 | password: admin |

## 🗄️ Estrutura de Dados

### PostgreSQL - Tabelas Principais
- `users` - Usuários e equipe
- `clients` - Clientes
- `shipments` - Encomendas
- `shipment_tracking_events` - Eventos de rastreamento
- `tracking_routines` - Rotinas automáticas
- `automations` - Automações de negócio
- `integrations` - Integrações externas
- `audit_logs` - Logs de auditoria
- `notifications` - Notificações
- `reports` - Relatórios salvos

### MongoDB - Collections
- `tracking_events_archive` - Histórico completo
- `analytics_snapshots` - Métricas e dashboards
- `integration_logs` - Logs de integrações
- `automation_history` - Histórico de automações
- `client_interactions` - Interações com clientes
- `carrier_raw_responses` - Respostas brutas de APIs

## 🛠️ Comandos Úteis

```bash
# Gerenciar Docker
make up              # Iniciar serviços
make down            # Parar serviços
make restart         # Reiniciar serviços
make logs            # Ver logs

# Banco de dados
make migrate         # Executar migrations
make migration       # Criar nova migration

# Desenvolvimento
make run             # Iniciar API em dev mode
make test            # Executar testes
make format          # Formatar código
make lint            # Verificar código
make clean           # Limpar cache

# Shell Python
make shell           # IPython com contexto da app
```

## 📝 Criar Nova Migration

```bash
# Método 1: Usando make
make migration
# Digite a mensagem quando solicitado

# Método 2: Comando direto
alembic revision --autogenerate -m "add new column to users"

# Aplicar migration
alembic upgrade head

# Reverter migration
alembic downgrade -1
```

## 🔧 Variáveis de Ambiente Essenciais

```env
# PostgreSQL (obrigatório)
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_NAME=shiptracker_dev
DATABASE_USERNAME=admin
DATABASE_PASSWORD=admin

# Segurança (obrigatório)
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# CORS
ALLOWED_HOSTS=["http://localhost:3000"]
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com coverage
pytest --cov=app

# Teste específico
pytest tests/test_users.py

# Modo verbose
pytest -v
```

## 🐛 Debug

### Ver logs do PostgreSQL
```bash
docker-compose logs -f postgresql
```

### Acessar console do PostgreSQL
```bash
docker exec -it shiptracker-postgres psql -U admin -d shiptracker_dev
```

### Acessar MongoDB shell
```bash
docker exec -it shiptracker-mongodb mongosh -u admin -p admin
```

### Verificar Redis
```bash
docker exec -it shiptracker-redis redis-cli -a admin
```

## 📚 Recursos

- **Documentação FastAPI**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Alembic**: https://alembic.sqlalchemy.org
- **Motor (MongoDB)**: https://motor.readthedocs.io
- **Redis Python**: https://redis-py.readthedocs.io

## 🤝 Contribuindo

1. Crie uma branch: `git checkout -b feature/nova-feature`
2. Commit: `git commit -m 'Adiciona nova feature'`
3. Push: `git push origin feature/nova-feature`
4. Abra um Pull Request

## 📄 Licença

MIT License
