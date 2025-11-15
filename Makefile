# Makefile for ShipTracker API

.PHONY: help install dev-install up down restart logs shell migrate migration test clean format lint

help:
	@echo "ShipTracker API - Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make up            - Start all Docker services"
	@echo "  make down          - Stop all Docker services"
	@echo "  make restart       - Restart all Docker services"
	@echo "  make logs          - Show Docker logs"
	@echo "  make shell         - Open Python shell with app context"
	@echo "  make migrate       - Run database migrations"
	@echo "  make migration     - Create a new migration"
	@echo "  make test          - Run tests"
	@echo "  make clean         - Clean cache and build files"
	@echo "  make format        - Format code with black and isort"
	@echo "  make lint          - Run linting checks"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

up:
	docker-compose up -d
	@echo "Services started!"
	@echo "PostgreSQL: localhost:5432"
	@echo "MongoDB: localhost:27017"
	@echo "Redis: localhost:6379"
	@echo "pgAdmin: http://localhost:5050"
	@echo "Mongo Express: http://localhost:8081"
	@echo "Redis Commander: http://localhost:8082"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

shell:
	python -m IPython

migrate:
	alembic upgrade head

migration:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

test:
	pytest -v --cov=app tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

format:
	black app/
	isort app/

lint:
	flake8 app/
	mypy app/

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
