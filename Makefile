# Makefile for checkmate

.PHONY: help install install-dev test test-unit test-integration lint format type-check clean docs

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install checkmate
	pip install -e .

install-dev: ## Install checkmate with development dependencies
	pip install -e .[dev]

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest -m "not integration"

test-integration: ## Run integration tests only
	pytest -m integration

lint: ## Run linting
	ruff check checkmate/
	black --check checkmate/

format: ## Format code
	black checkmate/
	ruff check --fix checkmate/

type-check: ## Run type checking
	mypy checkmate/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docs: ## Build documentation
	sphinx-build -b html docs _build/html

check: lint type-check test-unit ## Run all checks

ci: install-dev check ## Run CI pipeline
