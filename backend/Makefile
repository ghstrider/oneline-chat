.PHONY: help install dev test test-integration test-all coverage run run-prod clean docker-build docker-up docker-down db-create db-migrate format lint type-check

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in production mode
	pip install .

dev: ## Install the package in development mode with dev dependencies
	pip install -e ".[dev]"

test: ## Run unit tests
	python -m pytest tests/ -v --no-cov -m "not integration"

test-integration: ## Run integration tests only
	python -m pytest tests/test_integration_local.py tests/test_chat_router.py -v --no-cov -m integration

test-all: ## Run all tests
	python -m pytest tests/ -v --no-cov

coverage: ## Run tests with coverage report
	python -m pytest tests/ -v --cov=oneline_chat --cov-report=term-missing --cov-report=html

run: ## Run the application in development mode
	python -m uvicorn oneline_chat.app:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run the application in production mode
	python -m oneline_chat.main

clean: ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker image
	docker build -t oneline-chat:latest .

docker-up: ## Start services with docker-compose
	docker-compose up -d

docker-down: ## Stop services with docker-compose
	docker-compose down

docker-logs: ## Show docker-compose logs
	docker-compose logs -f

db-create: ## Create database tables
	python -c "from oneline_chat.db import create_db_and_tables; create_db_and_tables()"

db-reset: ## Reset database (drop and recreate)
	python -c "from sqlmodel import text; from oneline_chat.db import engine, create_db_and_tables; \
		with engine.begin() as conn: conn.execute(text('DROP SCHEMA IF EXISTS oneline CASCADE')); \
		create_db_and_tables()"

format: ## Format code with black
	black src/ tests/

lint: ## Lint code with ruff
	ruff check src/ tests/

type-check: ## Type check with mypy
	mypy src/

check: format lint type-check ## Run all code quality checks

serve-ollama: ## Start Ollama server (if installed locally)
	ollama serve

pull-model: ## Pull the deepseek model for Ollama
	ollama pull deepseek-r1:8b

env-example: ## Create example .env file
	@echo "# Oneline Chat Environment Variables" > .env.example
	@echo "APP_ENV=development" >> .env.example
	@echo "LOG_LEVEL=INFO" >> .env.example
	@echo "" >> .env.example
	@echo "# Database Configuration" >> .env.example
	@echo "DB_HOST=localhost" >> .env.example
	@echo "DB_PORT=5432" >> .env.example
	@echo "DB_USER=postgres" >> .env.example
	@echo "DB_PASSWORD=" >> .env.example
	@echo "DB_NAME=oneline_chat_app" >> .env.example
	@echo "" >> .env.example
	@echo "# AI Provider Configuration" >> .env.example
	@echo "AI_PROVIDER=ollama  # or 'openai'" >> .env.example
	@echo "" >> .env.example
	@echo "# Ollama Configuration" >> .env.example
	@echo "OLLAMA_BASE_URL=http://localhost:11434/v1" >> .env.example
	@echo "OLLAMA_MODEL=deepseek-r1:8b" >> .env.example
	@echo "" >> .env.example
	@echo "# OpenAI Configuration (if using OpenAI)" >> .env.example
	@echo "# OPENAI_API_KEY=your-api-key-here" >> .env.example
	@echo "" >> .env.example
	@echo "Created .env.example file"