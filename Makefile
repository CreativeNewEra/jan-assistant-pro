.PHONY: install test lint format clean run test-coverage test-watch format-check security run-debug build pre-commit-install pre-commit-run

# Development setup
install:
        poetry install --with dev

# Testing
test:
        poetry run pytest tests/ -v

test-coverage:
        poetry run pytest tests/ --cov=src --cov-report=html --cov-report=term

test-watch:
        poetry run pytest-watch tests/ src/

# Code quality
lint:
        ruff src/ tests/
        mypy src/

format:
        black src/ tests/

format-check:
        black --check src/ tests/

# Security check
security:
	bandit -r src/
	safety check

# Clean up
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/

# Run application
run:
	python main.py

run-debug:
	JAN_ASSISTANT_DEBUG=true JAN_ASSISTANT_LOG_LEVEL=DEBUG python main.py

# Build distribution
build:
        poetry build

# Pre-commit hooks
pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files
