PYTHON ?= python3
VENV := .venv
VENV_BIN := $(VENV)/bin
BACKEND := backend
FRONTEND := frontend

.PHONY: setup dev up down logs test test-backend test-backend-postgres test-frontend lint format typecheck migrate migration build docs-check

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --require-hashes -r $(BACKEND)/requirements-dev.lock
	npm ci --prefix $(FRONTEND)

dev:
	docker compose -f compose.dev.yaml up --build

up:
	docker compose up -d --build

down:
	docker compose down
	docker compose -f compose.dev.yaml down

logs:
	docker compose logs -f app postgres

test: test-backend test-backend-postgres test-frontend

test-backend:
	cd $(BACKEND) && ../$(VENV_BIN)/pytest

test-backend-postgres:
	cd $(BACKEND) && HERMES_TEST_POSTGRES=1 ../$(VENV_BIN)/pytest tests/integration

test-frontend:
	npm test --prefix $(FRONTEND)

lint:
	$(VENV_BIN)/ruff check $(BACKEND) scripts
	$(VENV_BIN)/ruff format --check $(BACKEND) scripts
	npm run lint --prefix $(FRONTEND)
	npm run format:check --prefix $(FRONTEND)
	$(MAKE) docs-check

format:
	$(VENV_BIN)/ruff check --fix $(BACKEND) scripts
	$(VENV_BIN)/ruff format $(BACKEND) scripts
	npm run format --prefix $(FRONTEND)

typecheck:
	cd $(BACKEND) && ../$(VENV_BIN)/mypy
	npm run typecheck --prefix $(FRONTEND)

migrate:
	cd $(BACKEND) && ../$(VENV_BIN)/alembic upgrade head

migration:
	@test -n "$(name)" || (echo 'usage: make migration name="describe change"' && exit 2)
	cd $(BACKEND) && ../$(VENV_BIN)/alembic revision --autogenerate -m "$(name)"

build:
	docker compose build

docs-check:
	$(VENV_BIN)/python scripts/check_docs.py
