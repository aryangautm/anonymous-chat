.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'


# Environment Setup


.PHONY: setup
setup: ## Initial setup: create venv and install dependencies
	cd backend && uv venv
	cd backend && . .venv/bin/activate && uv pip install -r requirements.txt

.PHONY: install
install: ## Install/sync dependencies from requirements.txt
	cd backend && . .venv/bin/activate && uv pip sync requirements.txt

.PHONY: update
update: ## Update dependencies from requirements.in
	cd backend && . .venv/bin/activate && uv pip compile requirements.in -o requirements.txt


# Database Operations
.PHONY: db-init
db-init: ## Initialize database (create DB and install extensions)
	cd backend && . .venv/bin/activate && python scripts/init_database.py

.PHONY: db-migrate
db-migrate: ## Apply all pending migrations
	cd backend && . .venv/bin/activate && alembic upgrade head

.PHONY: db-downgrade
db-downgrade: ## Rollback last migration
	cd backend && . .venv/bin/activate && alembic downgrade -1

.PHONY: db-reset
db-reset: ## Reset database to base (WARNING: destroys all data)
	@echo "WARNING: This will destroy all data in the database!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	cd backend && . .venv/bin/activate && alembic downgrade base

.PHONY: db-current
db-current: ## Show current migration version
	cd backend && . .venv/bin/activate && alembic current

.PHONY: db-history
db-history: ## Show migration history
	cd backend && . .venv/bin/activate && alembic history --verbose

.PHONY: db-revision
db-revision: ## Create a new migration (autogenerate from models)
	@read -p "Migration message: " msg; \
	cd backend && . .venv/bin/activate && alembic revision --autogenerate -m "$$msg" && python scripts/postprocess_migration.py

.PHONY: db-revision-empty
db-revision-empty: ## Create an empty migration file
	@read -p "Migration message: " msg; \
	cd backend && . .venv/bin/activate && alembic revision -m "$$msg"

.PHONY: db-setup
db-setup: db-init db-migrate ## Complete database setup (init + migrate)


# Development
.PHONY: dev
dev: ## Run development server
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: shell
shell: ## Open Python shell with app context
	cd backend && . .venv/bin/activate && python

.PHONY: clean
clean: ## Clean up cache files and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true


# Testing & Quality
.PHONY: test
test: ## Run tests
	cd backend && . .venv/bin/activate && pytest

.PHONY: test-cov
test-cov: ## Run tests with coverage
	cd backend && . .venv/bin/activate && pytest --cov=app --cov-report=html --cov-report=term

.PHONY: lint
lint: ## Run linters (flake8 for style, imports, print statements)
	cd backend && . .venv/bin/activate && flake8 app/ scripts/ alembic/

.PHONY: format
format: ## Format code with black and isort
	cd backend && . .venv/bin/activate && isort app/ scripts/ alembic/
	cd backend && . .venv/bin/activate && black app/ scripts/ alembic/

.PHONY: format-check
format-check: ## Check formatting without making changes
	cd backend && . .venv/bin/activate && isort --check-only app/ scripts/ alembic/
	cd backend && . .venv/bin/activate && black --check app/ scripts/ alembic/


# Production Deployment
.PHONY: deploy-migrate
deploy-migrate: ## Production: run migrations
	cd backend && . .venv/bin/activate && python scripts/init_database.py && alembic upgrade head

.PHONY: prod
prod: ## Run production server (with uvicorn)
	cd backend && . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4


# Information

.PHONY: info
info: ## Show environment information
	@echo "Python version:"
	@cd backend && . .venv/bin/activate && python --version
	@echo ""
	@echo "Database status:"
	@cd backend && . .venv/bin/activate && alembic current 2>/dev/null || echo "  Not initialized"
	@echo ""
	@echo "Environment file:"
	@if [ -f .env ]; then echo "  .env exists"; else echo "  .env NOT FOUND"; fi

.PHONY: check
check: ## Check if environment is properly set up
	@echo "Checking environment..."
	@test -d backend/.venv || (echo "❌ Virtual environment not found. Run 'make setup'" && exit 1)
	@echo "✓ Virtual environment exists"
	@test -f .env || (echo "⚠ Warning: .env file not found (required for database operations)")
	@cd backend && . .venv/bin/activate && python -c "import app" 2>/dev/null || (echo "❌ App package not importable" && exit 1)
	@echo "✓ App package importable"
	@echo "✓ Environment is ready!"

