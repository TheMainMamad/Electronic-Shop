.PHONY: up down logs migrate migration seed test lint format backend-shell deploy build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

build:
	docker compose build

migrate:
	docker compose exec backend alembic upgrade head

migration:
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

seed:
	docker compose exec backend python -m app.scripts.seed

test:
	cd backend && . .venv/bin/activate && python -m pytest -q
	cd frontend && npm run typecheck && npm run lint

lint:
	cd backend && . .venv/bin/activate && ruff check app tests && mypy app
	cd frontend && npm run lint && npm run typecheck

format:
	cd backend && . .venv/bin/activate && ruff format app tests
	cd frontend && npm run format

backend-shell:
	docker compose exec backend bash

deploy:
	bash scripts/deploy.sh
