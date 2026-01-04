.PHONY: help install install-dev test lint format clean run docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code with black"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make run          - Run the MCP server"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest

lint:
	ruff check mssqlclient_mcp/
	mypy mssqlclient_mcp/

format:
	black mssqlclient_mcp/
	ruff check --fix mssqlclient_mcp/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	python -m mssqlclient_mcp.server

docker-build:
	docker build -t mssqlclient-mcp-python:latest .

docker-run:
	docker run -i --env-file .env mssqlclient-mcp-python:latest

docker-compose-up:
	docker-compose up

docker-compose-down:
	docker-compose down
