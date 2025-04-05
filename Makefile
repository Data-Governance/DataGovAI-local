.PHONY: activate-env install test lint format clean build docs dev docker-build docker-up docker-down check

# Activate conda environment
activate-env:
	@echo "Activating conda environment..."
	conda activate chatbot
	@echo "Environment activated successfully"

# Installation
install: activate-env
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .

# Testing
test: activate-env
	pytest tests/ -v

test-cov:
	pytest --cov=knowledge_base_agent --cov-report=html

test-watch:
	pytest-watch -- --testmon

# Linting and formatting
lint: activate-env
	flake8 src/ tests/
	mypy src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format: activate-env
	black src/ tests/
	isort src/ tests/

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Building
build: activate-env
	python setup.py sdist bdist_wheel

# Documentation
docs: activate-env
	mkdocs build

# Development server
dev:
	uvicorn knowledge_base_agent.api:app --reload --port 8000

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# All checks
check: lint test 