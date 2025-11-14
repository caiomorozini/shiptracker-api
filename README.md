# shiptracker-api

# Comandos docker

Comando para iniciar o container

```bash
sudo docker-compose up -d

```
Comando para parar o container

```
sudo docker-compose down

```

# Comandos Api


Iniciar Api

```
poetry run uvicorn app.main:app --reload
```

Parar Api

```
Ctrl + C
```

# Comandos Alembic

### Inicializar

```
alembic init alembic
```

### Upgrade

```
alembic upgrade ${codigo_revisao}
```

### Downgrade

```
alembic downgrade ${codigo_revisao}
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