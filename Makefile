# IBR Platform — Makefile
# Common commands for development, testing, and deployment.
# Run `make help` to see all available commands.

.PHONY: help install dev-install test test-unit test-integration lint type-check security-check format clean build run dev

PYTHON := python3
PIP := pip3
PYTEST := pytest
RUFF := ruff
MYPY := mypy
BANDIT := bandit

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "IBR Platform — Available Commands"
	@echo "=================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Usage: make <target>"
	@echo "Example: make test-unit"

# ============================================
# Installation
# ============================================

install: ## Install the package in production mode
	$(PIP) install .

dev-install: ## Install the package in development mode with all extras
	$(PIP) install -e ".[dev,ml,vector,graph,api]"
	@echo "✓ Development installation complete"

# ============================================
# Testing
# ============================================

test: test-unit test-integration ## Run all tests

test-unit: ## Run unit tests
	$(PYTEST) tests/unit/ -v

test-integration: ## Run integration tests (requires Docker)
	$(PYTEST) tests/integration/ -v -m integration

test-e2e: ## Run end-to-end tests
	$(PYTEST) tests/e2e/ -v -m e2e

test-cov: ## Run tests with coverage report
	$(PYTEST) tests/ --cov=ibr_platform --cov-report=html --cov-report=term

test-perf: ## Run performance benchmarks
	$(PYTEST) tests/perf/ -v -m "slow" --benchmark-only

test-security: ## Run security tests
	$(PYTEST) tests/security/ -v

# ============================================
# Code Quality
# ============================================

lint: ## Run linter (ruff)
	$(RUFF) check src/ tests/
	@echo "✓ Linting passed"

lint-fix: ## Fix linting issues automatically
	$(RUFF) check --fix src/ tests/

format: ## Format code with ruff
	$(RUFF) format src/ tests/
	$(RUFF) check --fix src/ tests/
	@echo "✓ Code formatted"

type-check: ## Run type checker (mypy)
	$(MYPY) src/ibr_platform/
	@echo "✓ Type checking passed"

security-check: ## Run security scanner (bandit)
	$(BANDIT) -r src/ -c pyproject.toml
	@echo "✓ Security check passed"

audit: ## Audit dependencies for vulnerabilities
	$(PIP) audit
	@echo "✓ Dependency audit passed"

check: lint type-check security-check ## Run all checks (lint, type, security)
	@echo "✓ All checks passed"

# ============================================
# Build
# ============================================

build: ## Build the package
	$(PYTHON) -m build
	@echo "✓ Build complete (dist/)"

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"

# ============================================
# Development
# ============================================

dev: ## Start development server (API + dashboard)
	@echo "Starting development server..."
	$(PYTHON) -m ibr_platform.api.server --reload --port 8000

run: ## Run the CLI
	$(PYTHON) -m ibr_platform.cli

# ============================================
# Docker
# ============================================

docker-build: ## Build Docker image
	docker build -t ibr-platform:latest .

docker-run: ## Run Docker container
	docker run -p 8000:8000 -p 9090:9090 ibr-platform:latest

# ============================================
# Git
# ============================================

git-status: ## Show git status
	@git status

git-log: ## Show recent commits
	@git log --oneline -10

# ============================================
# Documentation
# ============================================

docs-serve: ## Serve documentation locally
	@echo "Serving docs at http://localhost:8000"
	@cd docs && $(PYTHON) -m http.server 8000

# ============================================
# Quick checks (run before commit)
# ============================================

pre-commit: format lint type-check test-unit ## Run all pre-commit checks
	@echo "✓ Pre-commit checks passed. Ready to commit."
