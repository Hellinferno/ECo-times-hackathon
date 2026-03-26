.PHONY: dev dev-backend dev-frontend setup seed migrate test lint clean docker-up docker-down

# One-command development
dev: docker-up dev-backend dev-frontend

# Infrastructure only
docker-up:
	docker compose up -d postgres redis

docker-down:
	docker compose down

# Backend
dev-backend:
	cd apps/backend && python -m uvicorn main:app --reload --port 8000

setup-backend:
	cd apps/backend && python -m venv venv && venv/Scripts/pip install -r requirements.txt

migrate:
	cd apps/backend && python -m alembic upgrade head

seed:
	cd scripts && python seed_stocks.py

# Frontend
dev-frontend:
	cd apps/frontend && npm run dev

setup-frontend:
	cd apps/frontend && npm install

build-frontend:
	cd apps/frontend && npm run build

# Full setup
setup: setup-backend setup-frontend migrate seed

# Testing
test:
	cd apps/backend && python -m pytest -v

test-backend:
	cd apps/backend && python -m pytest -v

lint:
	cd apps/frontend && npm run lint

# Cleanup
clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
