.PHONY: setup install install-dev lint format test test-unit test-integration test-cov test-cov-unit build version bundle-validate bundle-validate-dev bundle-validate-prod bundle-deploy-dev bundle-deploy-prod bundle-destroy-dev clean help

# Load .env file if it exists (from project root)
ifneq (,$(wildcard .env))
    include .env
    export
endif
# =============================================================================
# Setup
# =============================================================================

setup: install-dev
	@echo "✅ Setup complete!"

install:
	pip install -r requirements.txt
	pip install -e .
	@echo "✅ Dependencies installed"

install-dev: install
	pip install -r requirements.dev.txt
	@echo "✅ Dev dependencies installed"

# =============================================================================
# Linting
# =============================================================================

lint:
	ruff check databricks_contracts/ tests/ examples/resources/
	ruff format --check databricks_contracts/ tests/ examples/resources/

format:
	ruff check --fix databricks_contracts/ tests/ examples/resources/
	ruff format databricks_contracts/ tests/ examples/resources/

# =============================================================================
# Testing
# =============================================================================

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-cov:
	pytest tests/ -v --cov=databricks_contracts --cov-report=html --cov-report=term

test-cov-unit:
	pytest tests/unit/ -v --cov=databricks_contracts --cov-report=term

# =============================================================================
# Build
# =============================================================================

build:
	pip install build setuptools-scm
	python -m build --wheel
	@echo "✅ Wheel built in dist/"

version:
	@python -c "from setuptools_scm import get_version; print(get_version())"

# =============================================================================
# Databricks Asset Bundles (DAB)
# =============================================================================

bundle-validate:
	databricks bundle validate -t dev
	databricks bundle validate -t prod
	@echo "✅ Bundle validated for all targets"

bundle-validate-dev:
	databricks bundle validate -t dev

bundle-validate-prod:
	databricks bundle validate -t prod

bundle-deploy-dev:
	@echo "🚀 Deploying to DEV..."
	databricks bundle deploy -t dev
	@echo "✅ Deployed to DEV!"

bundle-deploy-prod:
	@echo "🚀 Deploying to PROD..."
	databricks bundle deploy -t prod
	@echo "✅ Deployed to PROD!"

bundle-destroy-dev:
	@echo "🗑️  Destroying DEV bundle..."
	databricks bundle destroy -t dev --auto-approve
	@echo "✅ DEV bundle destroyed!"

# =============================================================================
# Utilities
# =============================================================================

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .ruff_cache/ htmlcov/ .databricks/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned"


# =============================================================================
# GitHub Secrets
# =============================================================================

secrets-list:
	@./scripts/update-secrets.sh --list

secrets-update:
	@./scripts/update-secrets.sh -f scripts/.secrets.env

secrets-update-dev:
	@./scripts/update-secrets.sh -f scripts/.secrets.env -e dev

secrets-update-prod:
	@./scripts/update-secrets.sh -f scripts/.secrets.env -e prod

secrets-update-dry:
	@./scripts/update-secrets.sh -f scripts/.secrets.env --dry-run

secrets-set:
	@./scripts/update-secrets.sh -s $(SECRET) -v "$(VALUE)"

# =============================================================================
# Help
# =============================================================================

help:
	@echo "databricks-contracts library"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "  Setup:"
	@echo "    make setup          - Full setup (deps + install)"
	@echo "    make install        - Install production dependencies"
	@echo "    make install-dev    - Install all dependencies"
	@echo ""
	@echo "  Linting:"
	@echo "    make lint           - Check code style (ruff)"
	@echo "    make format         - Auto-format code"
	@echo ""
	@echo "  Testing:"
	@echo "    make test           - Run all tests"
	@echo "    make test-unit      - Run unit tests only"
	@echo "    make test-integration - Run integration tests only"
	@echo "    make test-cov       - Run all tests with coverage + HTML report"
	@echo "    make test-cov-unit  - Run unit tests with coverage"
	@echo ""
	@echo "  Build:"
	@echo "    make build          - Build wheel (uses setuptools-scm for version)"
	@echo "    make version        - Show current version from Git"
	@echo ""
	@echo "  Databricks Bundles:"
	@echo "    make bundle-validate      - Validate bundle (dev + prod)"
	@echo "    make bundle-validate-dev  - Validate bundle for dev"
	@echo "    make bundle-validate-prod - Validate bundle for prod"
	@echo "    make bundle-deploy-dev    - Deploy bundle to dev"
	@echo "    make bundle-deploy-prod   - Deploy bundle to prod"
	@echo "    make bundle-destroy-dev   - Destroy dev bundle"
	@echo ""
	@echo "  GitHub Secrets (requires gh CLI):"
	@echo "    make secrets-list         - List all secrets in repository"
	@echo "    make secrets-update       - Update all secrets from scripts/.secrets.env"
	@echo "    make secrets-update-dev   - Update secrets for dev environment only"
	@echo "    make secrets-update-prod  - Update secrets for prod environment only"
	@echo "    make secrets-update-dry   - Preview secrets update (dry-run)"
	@echo "    make secrets-set SECRET=NAME VALUE=xxx - Set a single secret"
	@echo ""
	@echo "  Utilities:"
	@echo "    make clean          - Remove build artifacts"
