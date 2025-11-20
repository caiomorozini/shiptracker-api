# Scripts

Esta pasta contém scripts utilitários e de desenvolvimento para o ShipTracker API.

## Estrutura

```
scripts/
├── check_codes.py              # Valida códigos de ocorrência no banco
├── create_test_data.py         # Cria dados de teste no banco
├── seed_occurrence_codes.py    # Popula tabela occurrence_codes
├── test_seed.py               # Testa seed de occurrence_codes
├── test_timeline_endpoint.py   # Testa endpoint de timeline
├── test_timeline_simple.py     # Teste simplificado de timeline
├── test_tracking_updates.py    # Testa endpoints de tracking updates
└── old_airflow/               # DAGs antigos do Airflow (deprecado)
    └── dags/
```

## Scripts Disponíveis

### Seed e Setup

- **`seed_occurrence_codes.py`**: Popula a tabela `occurrence_codes` com os 65 códigos do SSW
  ```bash
  cd /home/caiomorozini/Dev/shiptracker-api
  python scripts/seed_occurrence_codes.py
  ```

- **`create_test_data.py`**: Cria dados fictícios para testes (usuários, clientes, encomendas)
  ```bash
  python scripts/create_test_data.py
  ```

### Validação

- **`check_codes.py`**: Verifica se os códigos de ocorrência estão corretamente cadastrados
  ```bash
  python scripts/check_codes.py
  ```

### Testes de Endpoints

- **`test_timeline_endpoint.py`**: Testa o endpoint GET `/api/v1/shipments/{id}/tracking-timeline`
  ```bash
  python scripts/test_timeline_endpoint.py
  ```

- **`test_timeline_simple.py`**: Versão simplificada do teste de timeline
  ```bash
  python scripts/test_timeline_simple.py
  ```

- **`test_tracking_updates.py`**: Testa endpoints de atualização de tracking
  ```bash
  python scripts/test_tracking_updates.py
  ```

## Old Airflow

A pasta `old_airflow/` contém os DAGs antigos do Apache Airflow que foram substituídos pelo Prefect. Mantidos apenas para referência histórica.

**Status:** Deprecado - Não usar em produção

## Notas

- Todos os scripts assumem que você está no diretório raiz do projeto
- Certifique-se de ter as variáveis de ambiente configuradas (`.env`)
- Alguns scripts requerem que a API esteja rodando
- Para scripts que modificam o banco, sempre use ambiente de desenvolvimento

## Desenvolvimento

Ao criar novos scripts utilitários, adicione-os nesta pasta e documente aqui seu propósito e uso.
