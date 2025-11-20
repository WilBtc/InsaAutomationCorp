# ============================================================================
# Alkhorayef ESP IoT Platform - Makefile
# ============================================================================
# Common development and deployment tasks
# Usage: make <target>
# ============================================================================

.PHONY: help install dev test lint format clean build run docker-build docker-run deploy

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
VENV := venv
DOCKER_IMAGE := alkhorayef-esp
DOCKER_TAG := 1.0.0
PORT := 8000

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ Help

help: ## Display this help message
	@echo "$(GREEN)Alkhorayef ESP IoT Platform - Available Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development Setup

install: ## Install all dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

venv: ## Create virtual environment
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✓ Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate with: source $(VENV)/bin/activate$(NC)"

dev: ## Install development dependencies and setup
	@echo "$(GREEN)Setting up development environment...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	@echo "$(GREEN)✓ Development environment ready$(NC)"

env: ## Create .env file from .env.example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ Created .env file from .env.example$(NC)"; \
		echo "$(YELLOW)⚠ Remember to update .env with your actual values!$(NC)"; \
	else \
		echo "$(YELLOW)⚠ .env file already exists$(NC)"; \
	fi

##@ Code Quality

lint: ## Run all linters (flake8, mypy, pylint)
	@echo "$(GREEN)Running linters...$(NC)"
	@echo "$(YELLOW)→ flake8$(NC)"
	flake8 . --max-line-length=100 --exclude=venv,build,dist
	@echo "$(YELLOW)→ mypy$(NC)"
	mypy . --exclude venv
	@echo "$(YELLOW)→ pylint$(NC)"
	pylint app.py --max-line-length=100 --disable=C0111,C0103
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code with black and isort
	@echo "$(GREEN)Formatting code...$(NC)"
	@echo "$(YELLOW)→ isort$(NC)"
	isort . --profile black --line-length 100
	@echo "$(YELLOW)→ black$(NC)"
	black . --line-length 100
	@echo "$(GREEN)✓ Code formatted$(NC)"

type-check: ## Run mypy type checking
	@echo "$(GREEN)Running type checks...$(NC)"
	mypy . --exclude venv
	@echo "$(GREEN)✓ Type checking complete$(NC)"

##@ Testing

test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	pytest -v --tb=short
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	pytest -v -m unit
	@echo "$(GREEN)✓ Unit tests complete$(NC)"

test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	pytest -v -m integration
	@echo "$(GREEN)✓ Integration tests complete$(NC)"

##@ Running

run: ## Run the application locally
	@echo "$(GREEN)Starting application...$(NC)"
	$(PYTHON) app.py

run-dev: ## Run with auto-reload (development)
	@echo "$(GREEN)Starting development server with auto-reload...$(NC)"
	uvicorn app:app --reload --host 0.0.0.0 --port $(PORT)

run-prod: ## Run with Gunicorn (production)
	@echo "$(GREEN)Starting production server...$(NC)"
	gunicorn app:app \
		--bind 0.0.0.0:$(PORT) \
		--workers 4 \
		--worker-class uvicorn.workers.UvicornWorker \
		--timeout 120 \
		--access-logfile - \
		--error-logfile -

##@ Docker

docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_IMAGE):latest
	@echo "$(GREEN)✓ Docker image built: $(DOCKER_IMAGE):$(DOCKER_TAG)$(NC)"

docker-run: ## Run Docker container
	@echo "$(GREEN)Running Docker container...$(NC)"
	docker run -d \
		--name alkhorayef-esp \
		--env-file .env \
		-p $(PORT):8000 \
		-v $$(pwd)/logs:/app/logs \
		-v $$(pwd)/ml-models:/app/ml-models \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)✓ Container started on http://localhost:$(PORT)$(NC)"

docker-stop: ## Stop Docker container
	@echo "$(YELLOW)Stopping Docker container...$(NC)"
	docker stop alkhorayef-esp
	docker rm alkhorayef-esp
	@echo "$(GREEN)✓ Container stopped$(NC)"

docker-logs: ## View Docker container logs
	docker logs -f alkhorayef-esp

docker-shell: ## Open shell in Docker container
	docker exec -it alkhorayef-esp /bin/bash

docker-compose-up: ## Start all services with docker-compose
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ All services started$(NC)"

docker-compose-down: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ All services stopped$(NC)"

##@ Database

db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

db-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	alembic downgrade -1
	@echo "$(GREEN)✓ Rollback complete$(NC)"

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)⚠ WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "$(GREEN)✓ Database reset$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

##@ Cleanup

clean: ## Remove all generated files
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/ build/ dist/
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean ## Remove all generated files including venv
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	rm -rf $(VENV)
	@echo "$(GREEN)✓ Deep cleanup complete$(NC)"

##@ Deployment

deploy: ## Deploy to production (requires configuration)
	@echo "$(GREEN)Deploying to production...$(NC)"
	@echo "$(RED)⚠ Not implemented - configure your deployment method$(NC)"
	# TODO: Add deployment commands (kubectl, terraform, etc.)

health-check: ## Check application health
	@echo "$(GREEN)Checking application health...$(NC)"
	@curl -f http://localhost:$(PORT)/health || echo "$(RED)✗ Health check failed$(NC)"

##@ Documentation

docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	mkdocs build
	@echo "$(GREEN)✓ Documentation generated in site/$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation at http://localhost:8001$(NC)"
	mkdocs serve

##@ Security

security-scan: ## Run security vulnerability scan
	@echo "$(GREEN)Running security scan...$(NC)"
	pip-audit
	bandit -r . -f json -o security-report.json || true
	@echo "$(GREEN)✓ Security scan complete$(NC)"

secrets-check: ## Check for exposed secrets in code
	@echo "$(GREEN)Checking for secrets...$(NC)"
	@if grep -r "CHANGE_ME" .env 2>/dev/null; then \
		echo "$(RED)✗ Found CHANGE_ME placeholders in .env$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ No obvious secrets found$(NC)"; \
	fi

##@ Utilities

version: ## Show application version
	@echo "$(GREEN)Alkhorayef ESP IoT Platform$(NC)"
	@echo "Version: $(DOCKER_TAG)"
	@$(PYTHON) --version
	@docker --version

logs: ## Tail application logs
	tail -f logs/app.log

ps: ## Show running processes
	@echo "$(GREEN)Running processes:$(NC)"
	@ps aux | grep -E "python|uvicorn|gunicorn" | grep -v grep

check-deps: ## Check for dependency updates
	@echo "$(GREEN)Checking for dependency updates...$(NC)"
	pip list --outdated

requirements-update: ## Update requirements.txt with current versions
	@echo "$(GREEN)Updating requirements.txt...$(NC)"
	pip freeze > requirements.txt.new
	@echo "$(YELLOW)Review requirements.txt.new before replacing requirements.txt$(NC)"
