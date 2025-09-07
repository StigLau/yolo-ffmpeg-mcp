# Komposteur MCP Server - TypeScript
# Makefile for essential project operations

.PHONY: help install build test dev clean lint validate-jar download-jar

# Colors for output
GREEN = \033[0;32m
BLUE = \033[0;34m
YELLOW = \033[1;33m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Komposteur MCP Server - Available Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	npm install

build: ## Build TypeScript to JavaScript
	@echo "$(YELLOW)Building TypeScript...$(NC)"
	npm run build

test: ## Run test suite
	@echo "$(YELLOW)Running tests...$(NC)"
	npm test

dev: ## Start development server with hot reload
	@echo "$(YELLOW)Starting development server...$(NC)"
	npm run dev

clean: ## Clean build artifacts
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	npm run clean
	rm -rf node_modules/.cache

lint: ## Run linter and fix issues
	@echo "$(YELLOW)Running linter...$(NC)"
	npm run lint:fix

validate-jar: ## Validate Komposteur JAR availability and functionality
	@echo "$(YELLOW)Validating Komposteur JAR...$(NC)"
	node scripts/validate-komposteur.js

download-jar: ## Download Komposteur JAR (manual process)
	@echo "$(YELLOW)Download Komposteur JAR...$(NC)"
	node scripts/download-komposteur.js

setup: install validate-jar ## Complete project setup
	@echo "$(GREEN)✅ Setup complete! Run 'make dev' to start development.$(NC)"

quick-test: ## Quick validation of core functionality
	@echo "$(YELLOW)Running quick validation...$(NC)"
	@$(MAKE) validate-jar
	@npm run build
	@echo "$(GREEN)✅ Quick test passed!$(NC)"

# Development workflow commands
watch: ## Watch for changes and rebuild
	@echo "$(YELLOW)Watching for changes...$(NC)"
	npx tsc --watch

format: ## Format code
	@echo "$(YELLOW)Formatting code...$(NC)"
	npm run lint:fix

# Production commands
dist: build ## Create distribution package
	@echo "$(YELLOW)Creating distribution package...$(NC)"
	@echo "$(GREEN)✅ Distribution ready in dist/$(NC)"

# Status and info commands
status: ## Show project status
	@echo "$(BLUE)Project Status:$(NC)"
	@echo "Node version: $$(node --version)"
	@echo "NPM version: $$(npm --version)"
	@echo "TypeScript: $$(npx tsc --version)"
	@$(MAKE) validate-jar

info: status ## Alias for status
	@echo "$(GREEN)Use 'make help' for available commands$(NC)"