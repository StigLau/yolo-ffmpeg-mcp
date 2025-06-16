# MCP Server Testing Makefile
# Usage: make -f test_mcp.mk test-mcp

.PHONY: test-mcp test-mcp-quick test-mcp-workflow

test-mcp: ## Run complete MCP server test suite
	@echo "🧪 Running complete MCP server test suite..."
	@./test_mcp_server.sh

test-mcp-quick: ## Run basic MCP server connectivity test  
	@echo "⚡ Running quick MCP server test..."
	@cd $(shell pwd) && PYTHONPATH=$(shell pwd) .venv/bin/python -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from server import mcp
async def test():
    result = await mcp.call_tool('list_files', {})
    print(f'✅ MCP server responding - found {len(result.get(\"files\", []))} files')
asyncio.run(test())
"

test-mcp-workflow: ## Test music video creation workflow only
	@echo "🎬 Testing music video creation workflow..."
	@./test_mcp_server.sh | grep -A 20 "Music Video Creation Workflow"

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
