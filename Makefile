.PHONY: help install install-dev dev test lint format type-check clean run check

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev]"

dev: install-dev  ## Set up development environment
	pre-commit install
	@echo "✅ Development environment ready!"

test:  ## Run tests
	pytest -v

lint:  ## Run linting
	ruff check --fix src tests

format:  ## Format code
	black src tests
	ruff check --fix src tests

type-check:  ## Run type checking
	mypy src

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:  ## Run the baseball MCP server
	python -m baseball_mcp.server

check: lint type-check test  ## Run all checks

pre-commit-install:  ## Install pre-commit hooks
	pre-commit install

pre-commit-run:  ## Run pre-commit on all files
	pre-commit run --all-files 