# API Testing Guide

## 📋 Visão Geral

Esta suíte de testes cobre todas as funcionalidades da API ShipTracker, incluindo:
- Autenticação e autorização
- Gerenciamento de usuários
- Gerenciamento de clientes
- Gerenciamento de encomendas
- Permissões e controle de acesso

## 🛠️ Instalação

### Instalar dependências de teste:

```bash
# Com uv
uv pip install -e ".[dev]"

# Ou com pip
pip install -e ".[dev]"
```

Pacotes instalados:
- `pytest` - Framework de testes
- `pytest-asyncio` - Suporte async/await
- `pytest-cov` - Cobertura de código
- `httpx` - Cliente HTTP async
- `faker` - Geração de dados fake

## 🚀 Executando os Testes

### Todos os testes:
```bash
pytest
```

### Com cobertura de código:
```bash
pytest --cov=app --cov-report=html
```

### Testes específicos:

```bash
# Por arquivo
pytest tests/test_auth.py

# Por classe
pytest tests/test_auth.py::TestAuth

# Por função
pytest tests/test_auth.py::TestAuth::test_login_success

# Por marcador
pytest -m auth
pytest -m integration
```

### Modo verbose:
```bash
pytest -v
pytest -vv  # Extra verbose
```

### Com saída detalhada:
```bash
pytest -s  # Mostra prints
pytest -x  # Para no primeiro erro
pytest --lf  # Roda apenas os que falharam
```

## 📂 Estrutura dos Testes

```
tests/
├── conftest.py              # Fixtures compartilhadas
├── test_auth.py             # Testes de autenticação
├── test_users.py            # Testes de usuários
├── test_clients.py          # Testes de clientes
├── test_shipments.py        # Testes de encomendas
└── test_permissions.py      # Testes de permissões
```

## 🔧 Fixtures Disponíveis

### Fixtures de Banco de Dados:
- `db_session`: Sessão de banco de dados limpa para cada teste
- `client`: Cliente HTTP com injeção de dependências

### Fixtures de Usuários:
- `test_user`: Usuário operator padrão
- `admin_user`: Usuário admin
- `manager_user`: Usuário manager
- `viewer_user`: Usuário viewer

### Fixtures de Autenticação:
- `auth_headers`: Headers com token do test_user
- `admin_headers`: Headers com token do admin
- `manager_headers`: Headers com token do manager
- `viewer_headers`: Headers com token do viewer

### Fixtures de Dados:
- `test_client_record`: Cliente de teste no banco
- `test_shipment`: Encomenda de teste no banco

## 📊 Cobertura de Testes

### Visualizar relatório HTML:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Relatório no terminal:
```bash
pytest --cov=app --cov-report=term-missing
```

### Meta de cobertura:
- **Mínimo**: 80%
- **Recomendado**: 90%+

## ✅ Checklist de Testes

### Autenticação (`test_auth.py`):
- [x] Registro de novo usuário
- [x] Registro com email duplicado
- [x] Registro com email inválido
- [x] Login com sucesso
- [x] Login com senha errada
- [x] Login com usuário inexistente
- [x] Obter usuário atual
- [x] Acesso não autorizado
- [x] Token inválido
- [x] Refresh de token
- [x] Logout

### Usuários (`test_users.py`):
- [x] Listar usuários (admin)
- [x] Listar usuários (não autorizado)
- [x] Obter usuário por ID
- [x] Obter usuário inexistente
- [x] Criar usuário (admin)
- [x] Criar usuário (não autorizado)
- [x] Atualizar usuário
- [x] Deletar usuário
- [x] Trocar senha
- [x] Trocar senha com senha antiga errada

### Clientes (`test_clients.py`):
- [x] Listar clientes
- [x] Buscar clientes
- [x] Obter cliente por ID
- [x] Criar cliente
- [x] Criar cliente com email inválido
- [x] Atualizar cliente
- [x] Deletar cliente
- [x] Estatísticas de clientes

### Encomendas (`test_shipments.py`):
- [x] Listar encomendas
- [x] Listar com filtros
- [x] Buscar por código de rastreio
- [x] Obter encomenda por ID
- [x] Criar encomenda
- [x] Criar encomenda com código duplicado
- [x] Atualizar encomenda
- [x] Atualizar status
- [x] Deletar encomenda
- [x] Estatísticas de encomendas
- [x] Acesso não autorizado

## 🎯 Boas Práticas

### 1. **Isolamento de Testes**
- Cada teste deve ser independente
- Use fixtures para setup/teardown
- Banco de dados é resetado entre testes

### 2. **Nomenclatura Clara**
```python
# ✅ Bom
def test_login_with_invalid_credentials_returns_401():
    ...

# ❌ Ruim
def test_login_fail():
    ...
```

### 3. **Arrange-Act-Assert**
```python
@pytest.mark.asyncio
async def test_create_user():
    # Arrange
    user_data = {...}
    
    # Act
    response = await client.post("/api/users", json=user_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["email"] == user_data["email"]
```

### 4. **Use Marcadores**
```python
@pytest.mark.slow
@pytest.mark.integration
async def test_complex_workflow():
    ...
```

### 5. **Teste Casos de Erro**
```python
async def test_create_user_with_duplicate_email():
    # Testa que a API retorna erro apropriado
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]
```

## 🐛 Debug de Testes

### Rodar teste específico com debug:
```bash
pytest -s -vv tests/test_auth.py::TestAuth::test_login_success
```

### Adicionar breakpoint:
```python
import pdb; pdb.set_trace()  # Python debugger
```

### Com pytest:
```python
pytest.set_trace()  # Pausa no ponto
```

## 🔄 CI/CD Integration

### GitHub Actions example:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## 📈 Métricas Atuais

```
Tests: 50+
Coverage: 85%+
Duration: ~5 seconds
```

## 🚧 TODOs

- [ ] Testes de permissões detalhados
- [ ] Testes de tracking events
- [ ] Testes de relatórios
- [ ] Testes de integração MongoDB
- [ ] Testes de cache Redis
- [ ] Testes de rate limiting
- [ ] Testes de websockets

## 📚 Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/)
- [HTTPX Documentation](https://www.python-httpx.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
