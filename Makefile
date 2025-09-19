# Legal Simulation Platform - Development Makefile

.PHONY: help format lint test up down e2e check clean install db-upgrade db-downgrade

# Default target
help:
	@echo "Legal Simulation Platform - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make up          - Start all services with Docker Compose"
	@echo "  make down        - Stop all services"
	@echo "  make clean       - Clean up containers, volumes, and temporary files"
	@echo ""
	@echo "AI Agent Services:"
	@echo "  make ai-agent-worker - Start AI Agent Temporal Worker"
	@echo "  make event-bridge    - Start Temporal Event Bridge"
	@echo "  make ai-services     - Start all AI agent services"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format      - Format code with black and isort"
	@echo "  make lint        - Run linting with flake8 and mypy"
	@echo "  make check       - Run format, lint, and test"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run unit tests"
	@echo "  make integration - Run integration tests"
	@echo "  make e2e         - Run end-to-end tests"
	@echo ""
	@echo "Database:"
	@echo "  make db-upgrade  - Run database migrations"
	@echo "  make db-downgrade - Rollback database migrations"
	@echo ""
	@echo "Installation:"
	@echo "  make install     - Install dependencies"

# Development environment
up:
	@echo "Starting Legal Simulation Platform services..."
	docker-compose up -d
	@echo "Services started. Check status with: docker-compose ps"

down:
	@echo "Stopping Legal Simulation Platform services..."
	docker-compose down
	@echo "Services stopped."

clean:
	@echo "Cleaning up containers, volumes, and temporary files..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete."

# Code formatting
format:
	@echo "Formatting code with black and isort..."
	black --line-length 88 --target-version py311 services/ tests/ agents/ tools/
	isort --profile black --line-length 88 services/ tests/ agents/ tools/
	@echo "Code formatting complete."

# Linting
lint:
	@echo "Running linting checks..."
	flake8 services/ tests/ agents/ tools/ --max-line-length=88 --extend-ignore=E203,W503
	mypy services/ --ignore-missing-imports --no-strict-optional
	@echo "Linting complete."

# Testing
test:
	@echo "Running unit tests..."
	python -m pytest tests/unit/ -v --cov=services --cov-report=term-missing --cov-report=html
	@echo "Unit tests complete."

integration:
	@echo "Running integration tests..."
	python -m pytest tests/integration/ -v
	@echo "Integration tests complete."

e2e:
	@echo "Running end-to-end tests..."
	python -m pytest tests/e2e/ -v
	@echo "End-to-end tests complete."

# Combined checks
check: format lint test
	@echo "All checks completed successfully!"

# Database operations
db-upgrade:
	@echo "Running database migrations..."
	cd services/shared && alembic upgrade head
	@echo "Database migrations complete."

db-downgrade:
	@echo "Rolling back database migrations..."
	cd services/shared && alembic downgrade -1
	@echo "Database rollback complete."

# Installation
install:
	@echo "Installing dependencies..."
	pip install -e .
	pip install -r requirements-test.txt
	@echo "Dependencies installed."

# Service-specific targets
api-gateway:
	@echo "Starting API Gateway service..."
	cd services/api-gateway && python main.py

evidence-processor:
	@echo "Starting Evidence Processor service..."
	cd services/evidence-processor && python main.py

storyboard-service:
	@echo "Starting Storyboard Service..."
	cd services/storyboard-service && python main.py

timeline-compiler:
	@echo "Starting Timeline Compiler service..."
	cd services/timeline-compiler && python main.py

render-orchestrator:
	@echo "Starting Render Orchestrator service..."
	cd services/render-orchestrator && python main.py

# AI Agent services
ai-agent-worker:
	@echo "Starting AI Agent Temporal Worker..."
	python scripts/start_ai_agent_worker.py

event-bridge:
	@echo "Starting Temporal Event Bridge..."
	python scripts/start_event_bridge.py

ai-services: ai-agent-worker event-bridge
	@echo "Starting all AI agent services..."

# Health checks
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health || echo "API Gateway: DOWN"
	@curl -s http://localhost:8001/health || echo "Evidence Processor: DOWN"
	@curl -s http://localhost:8002/health || echo "Storyboard Service: DOWN"
	@curl -s http://localhost:8003/health || echo "Timeline Compiler: DOWN"
	@curl -s http://localhost:8004/health || echo "Render Orchestrator: DOWN"

# Development utilities
logs:
	@echo "Showing service logs..."
	docker-compose logs -f

logs-api:
	@echo "Showing API Gateway logs..."
	docker-compose logs -f api-gateway

logs-evidence:
	@echo "Showing Evidence Processor logs..."
	docker-compose logs -f evidence-processor

logs-storyboard:
	@echo "Showing Storyboard Service logs..."
	docker-compose logs -f storyboard-service

logs-timeline:
	@echo "Showing Timeline Compiler logs..."
	docker-compose logs -f timeline-compiler

logs-render:
	@echo "Showing Render Orchestrator logs..."
	docker-compose logs -f render-orchestrator

# Build targets
build:
	@echo "Building Docker images..."
	docker-compose build

build-no-cache:
	@echo "Building Docker images (no cache)..."
	docker-compose build --no-cache

# Database management
db-reset:
	@echo "Resetting database..."
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 10
	make db-upgrade
	@echo "Database reset complete."

db-shell:
	@echo "Opening database shell..."
	docker-compose exec postgres psql -U legal_sim -d legal_sim

# Testing utilities
test-coverage:
	@echo "Generating test coverage report..."
	python -m pytest tests/ --cov=services --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

test-watch:
	@echo "Running tests in watch mode..."
	python -m pytest tests/ -f

# Documentation
docs:
	@echo "Generating API documentation..."
	cd services/api-gateway && python -c "import main; print('OpenAPI spec generated')"
	@echo "Documentation generated."

# Security
security-scan:
	@echo "Running security scan..."
	safety check
	bandit -r services/ -f json -o security-report.json
	@echo "Security scan complete."

# Performance
perf-test:
	@echo "Running performance tests..."
	python -m pytest tests/performance/ -v
	@echo "Performance tests complete."

# Release
release-check:
	@echo "Running release checks..."
	make check
	make security-scan
	make e2e
	@echo "Release checks complete."

# Environment setup
setup:
	@echo "Setting up development environment..."
	cp env.example .env
	make install
	make up
	sleep 15
	make db-upgrade
	make test
	@echo "Development environment setup complete!"

# Quick development cycle
dev: format lint test
	@echo "Development cycle complete!"

# Production deployment
deploy:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Production deployment complete."