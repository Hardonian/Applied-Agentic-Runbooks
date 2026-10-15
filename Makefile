.PHONY: ci lint type-check test test-unit test-integration test-e2e format install clean help migrate migrate-up migrate-down migrate-current seed validate-schema env-check doc-sync security-audit deploy-help deploy-doctor smoke-tests metrics-collect unit-economics yc-checklist user-acquisition dataroom-placeholders test-coverage weekly-progress readiness-check verify-runbook check-readiness-heartbeat verify-release package-check

help:
	@echo "Available commands:"
	@echo "  make ci              - Run all CI checks (lint, type-check, test-unit)"
	@echo "  make lint            - Run linters (ruff + black check)"
	@echo "  make format          - Format code (black + ruff fix)"
	@echo "  make type-check      - Run type checker (mypy)"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests only (fast, no I/O)"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-e2e        - Run E2E tests"
	@echo "  make test-cov        - Run tests with coverage report"
	@echo "  make install         - Install dependencies"
	@echo "  make clean           - Clean cache and build artifacts"
	@echo ""
	@echo "Database commands:"
	@echo "  make migrate         - Run database migrations (upgrade head)"
	@echo "  make migrate-up      - Upgrade database one revision"
	@echo "  make migrate-down    - Downgrade database one revision"
	@echo "  make migrate-current - Show current migration revision"
	@echo "  make seed            - Seed database with demo data"
	@echo "  make validate-schema - Validate database schema"
	@echo ""
	@echo "Utility commands:"
	@echo "  make env-check       - Check environment variables"
	@echo "  make doc-sync        - Check documentation synchronization"
	@echo "  make verify-runbook  - Verify readiness runbook and workflow contract"
	@echo "  make verify-release  - Verify release metadata and changelog alignment"
	@echo "  make package-check   - Build and validate distributable package"
	@echo "  make check-readiness-heartbeat - Verify latest scheduled run via GitHub API"

ci: lint type-check test-unit

lint:
	@echo "Running ruff..."
	ruff check agent_factory/ tests/
	@echo "Running black check..."
	black --check agent_factory/ tests/ || echo "Formatting differences detected (non-blocking)"

format:
	@echo "Formatting with black..."
	black agent_factory/ tests/
	@echo "Fixing with ruff..."
	ruff check --fix agent_factory/ tests/

type-check:
	@echo "Running mypy..."
	mypy agent_factory/ --ignore-missing-imports

test:
	@echo "Running all tests..."
	pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	pytest tests/ -m "not integration and not slow" -v

test-integration:
	@echo "Running integration tests..."
	pytest tests/ -m integration -v

test-e2e:
	@echo "Running E2E tests..."
	pytest tests/e2e/ -m e2e -v

test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ -m "not integration and not slow" -v --cov=agent_factory --cov-report=html --cov-report=term

install:
	@echo "Installing dependencies..."
	pip install -e ".[dev]"

clean:
	@echo "Cleaning cache and build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Clean complete."

# Database commands
migrate:
	@echo "Running database migrations..."
	alembic upgrade head

migrate-up:
	@echo "Upgrading database one revision..."
	alembic upgrade +1

migrate-down:
	@echo "Downgrading database one revision..."
	alembic downgrade -1

migrate-current:
	@echo "Current migration revision:"
	alembic current

seed:
	@echo "Seeding database with demo data..."
	python scripts/db-seed-demo.py

validate-schema:
	@echo "Validating database schema..."
	python scripts/db-validate-schema.py

# Utility commands
env-check:
	@echo "Checking environment variables..."
	python scripts/env-doctor.py

doc-sync:
	@echo "Checking documentation synchronization..."
	python scripts/doc-sync.py --check

# Venture OS - Readiness & Execution Commands
security-audit:
	@echo "Running security audit..."
	@bash scripts/security-audit.sh

deploy-help:
	@echo "Production deployment helper..."
	@bash scripts/deploy-production.sh

deploy-doctor:
	@echo "Checking deployment configuration..."
	@bash scripts/deploy-doctor.sh

smoke-tests:
	@echo "Running smoke tests..."
	@bash scripts/smoke-tests.sh

metrics-collect:
	@echo "Collecting metrics..."
	@bash scripts/collect-metrics.sh

unit-economics:
	@echo "Calculating unit economics..."
	@python3 scripts/calculate-unit-economics.py

yc-checklist:
	@echo "YC application checklist..."
	@bash scripts/yc-application-checklist.sh

user-acquisition:
	@echo "User acquisition checklist..."
	@bash scripts/get-users-checklist.sh

dataroom-placeholders:
	@echo "Analyzing data-room placeholders..."
	@python3 scripts/fill-dataroom-placeholders.py

test-coverage:
	@echo "Test coverage improvement plan..."
	@bash scripts/test-coverage-improvement.sh

weekly-progress:
	@echo "Weekly progress tracker..."
	@bash scripts/weekly-progress.sh

# Quick readiness check
readiness-check:
	@bash scripts/quick-start-readiness.sh

verify-runbook:
	@python scripts/verify-runbook-contract.py

verify-release:
	@python scripts/verify-release.py

package-check: verify-release
	@python -m build
	@twine check dist/*

check-readiness-heartbeat:
	@python scripts/check-readiness-heartbeat.py
