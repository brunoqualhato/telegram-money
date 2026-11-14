.PHONY: setup up down test demo build lint-frontend test-frontend check-frontend
setup:
	python3 scripts/setup.py
up:
	docker compose up -d --build
down:
	docker compose down
test:
	cd backend && UV_CACHE_DIR=/tmp/telegram-money-uv uv sync --frozen --python 3.12 && .venv/bin/pytest -q
build:
	cd frontend && npm ci --no-audit --no-fund && npm run build
demo:
	@echo 'Leia a seção Demonstração local no README.md.'

lint-frontend:
	cd frontend && npm run lint
test-frontend:
	cd frontend && npm test
check-frontend:
	cd frontend && npm run check
