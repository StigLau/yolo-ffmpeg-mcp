# FFMPEG MCP Server Makefile

.PHONY: help install start test clean config add-mcp

help: ## Show this help message
	@echo "FFMPEG MCP Server Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

start: ## Start MCP server
	uv run python -m src.server

test: ## Run integration tests
	uv run pytest tests/test_ffmpeg_integration.py -v -s

clean: ## Clean temporary files
	rm -rf /tmp/music/temp/*
	uv cache clean

config: ## Generate Claude Code MCP configuration
	@echo "Add this to your Claude Code MCP configuration:"
	@echo ""
	@echo "{"
	@echo "  \"mcpServers\": {"
	@echo "    \"ffmpeg-mcp\": {"
	@echo "      \"command\": \"uv\","
	@echo "      \"args\": [\"run\", \"python\", \"-m\", \"src.server\"],"
	@echo "      \"cwd\": \"$(PWD)\""
	@echo "    }"
	@echo "  }"
	@echo "}"

setup-dirs: ## Create required directories
	mkdir -p /tmp/music/source /tmp/music/temp

inspector: ## Start MCP Inspector for testing
	npx @modelcontextprotocol/inspector uv run python -m src.server

add-mcp: ## Add MCP server to Claude Code (project scope)
	claude mcp add ffmpeg-mcp --scope project -- uv run python -m src.server

dev: setup-dirs install ## Full development setup
	@echo "Development environment ready!"
	@echo "Next steps:"
	@echo "1. Run 'make config' to get Claude Code configuration"
	@echo "2. Add configuration to Claude Code settings"
	@echo "3. Restart Claude Code"
	@echo "4. Place video files in /tmp/music/source/"