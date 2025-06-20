.PHONY: install test lint format clean run

# Development setup
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .

# Testing
test:
	python -m pytest tests/ -v

test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

test-watch:
	python -m pytest-watch tests/ src/

# Code quality
lint:
	flake8 src/ tests/
	mypy src/
	bandit -r src/

format:
	black src/ tests/
	isort src/ tests/

format-check:
	black --check src/ tests/
	isort --check-only src/ tests/

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
	python setup.py sdist bdist_wheel

# Pre-commit hooks
pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files
