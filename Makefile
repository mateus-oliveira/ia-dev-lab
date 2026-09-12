.PHONY: help install migrate migrate-down migrate-stamp test lint run rabbitmq-up publisher subscriber

# Carrega as variaveis do .env (se existir) e exporta para os comandos abaixo.
ifneq (,$(wildcard .env))
include .env
export
endif

help:
	@echo "Alvos disponiveis:"
	@echo "  make install        - instala as dependencias do projeto (poetry install)"
	@echo "  make migrate        - aplica as migracoes Alembic ate a revisao mais recente"
	@echo "  make migrate-down   - reverte a ultima migracao Alembic aplicada"
	@echo "  make migrate-stamp  - marca o banco na revisao mais recente sem aplicar DDL"
	@echo "  make test           - roda a suite de testes (pytest)"
	@echo "  make lint           - roda ruff (check + format) e mypy"
	@echo "  make run            - sobe a API FastAPI em modo desenvolvimento (reload)"
	@echo "  make rabbitmq-up    - sobe o RabbitMQ via docker-compose (ADR 0007)"
	@echo "  make publisher      - roda o worker publisher (gera e publica eventos sinteticos)"
	@echo "  make subscriber     - roda o worker subscriber (consome a fila e persiste features)"

install:
	poetry install

migrate:
	poetry run alembic upgrade head

migrate-down:
	poetry run alembic downgrade -1

migrate-stamp:
	poetry run alembic stamp head

test:
	poetry run pytest

lint:
	poetry run ruff check .
	poetry run ruff format .
	poetry run mypy .

run:
	PYTHONPATH=src poetry run uvicorn player_modeling.api.app:app --reload --port 8000

rabbitmq-up:
	docker compose up -d

publisher:
	PYTHONPATH=src poetry run python -m player_modeling.simulator.publisher

subscriber:
	PYTHONPATH=src poetry run python -m player_modeling.worker.subscriber
