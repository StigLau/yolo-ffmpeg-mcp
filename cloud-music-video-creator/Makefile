# Cloud Music Video Creator - MVP Makefile

.PHONY: help install run test clean dev build-ts run-ts

help: ## Show this help message
	@echo "Cloud Music Video Creator - Available Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies (Python + TypeScript)
	pip install -e .
	npm install

setup: ## Setup development environment  
	mkdir -p /tmp/music-video-creator/{temp,generated-videos,source,processing}
	@echo "Development environment ready"

# Python MCP Server
run: ## Run Python MCP server
	python scripts/start.py

dev: ## Run Python server in development mode
	ENVIRONMENT=development LOG_LEVEL=DEBUG python scripts/start.py

# TypeScript MCP Server  
build-ts: ## Build TypeScript MCP server
	npm run build

run-ts: build-ts ## Run TypeScript MCP server
	npm start

dev-ts: ## Run TypeScript server in development mode
	npm run dev

test: ## Run integration tests
	python3 tests/test_integration.py

clean: ## Clean temp files and cache
	rm -rf /tmp/music-video-creator/*
	rm -rf __pycache__ src/__pycache__ */__pycache__
	rm -rf dist node_modules
	find . -name "*.pyc" -delete

# Web Interface
web: setup ## Start web interface server
	@echo "🎬 Starting Cloud Music Video Creator Web Interface..."
	@echo "📍 Open your browser to: http://localhost:8001"
	python3 simple_server.py 8001

test-web: ## Test web interface API quickly
	@echo "🧪 Testing Web Interface API..."
	@python3 simple_server.py 8002 &
	@sleep 2
	@curl -s http://localhost:8002/api/health || echo "❌ Server not responding"
	@echo "\n✅ Web server test complete"
	@pkill -f "python3 simple_server.py" || true