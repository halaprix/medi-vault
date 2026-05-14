.PHONY: up down logs build shell-backend shell-db seed migrate rollback lint test clean

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

shell-backend:
	docker compose exec backend /bin/bash

shell-db:
	docker compose exec postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

seed:
	docker compose exec backend python scripts/seed_biomarkers.py

migrate:
	docker compose exec backend alembic upgrade head

rollback:
	docker compose exec backend alembic downgrade -1

lint:
	docker compose exec backend ruff check app/
	docker compose exec frontend npx eslint apps/frontend/

test:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term

test-frontend:
	docker compose exec frontend npx vitest run

clean:
	docker compose down -v
	rm -rf pgdata/ chroma_db/ model_cache/

generate-key:
	python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
