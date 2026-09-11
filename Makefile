.PHONY: help install migrate migrate-down migrate-stamp test lint api

help:
	@echo "Alvos disponiveis:"
	@echo "  make install        - instala as dependencias do projeto (poetry install)"
	@echo "  make migrate        - aplica as migracoes Alembic ate a revisao mais recente"
	@echo "  make migrate-down   - reverte a ultima migracao Alembic aplicada"
	@echo "  make migrate-stamp  - marca o banco na revisao mais recente sem aplicar DDL"
	@echo "  make test           - roda a suite de testes (pytest)"
	@echo "  make lint           - roda ruff (check + format) e mypy"
	@echo "  make api            - sobe a API FastAPI em modo desenvolvimento (reload)"

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

api:
	PYTHONPATH=src poetry run uvicorn player_modeling.api.app:app --reload --port 8000

# Alvos de worker/simulador (cronjobs) serao adicionados aqui quando esses
# modulos forem implementados (ver docs/escopo.md).
