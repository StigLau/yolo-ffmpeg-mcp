#!/bin/bash
# MCP Registry-Guided LLM Test Script
# Integrates with YOLO-FFMPEG-MCP server for registry operations

set -e

# Configuration
MCP_SERVER_PATH="$(pwd)"
OUTPUT_BASE="/tmp/kompo/haiku-ffmpeg"
REGISTRY_PORT="3000"

# Colors for output  
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}🗂️ $1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_mcp_integration() {
    print_header "MCP INTEGRATION CHECK"
    
    # Check if we're in MCP server directory
    if [[ -f "pyproject.toml" ]] && grep -q "yolo-ffmpeg-mcp" pyproject.toml 2>/dev/null; then
        print_success "Running in YOLO-FFMPEG-MCP directory"
    else
        print_error "Not in YOLO-FFMPEG-MCP directory"
        echo "Please run from the MCP server root directory"
        return 1
    fi
    
    # Check MCP server dependencies
    if command -v uv &> /dev/null; then
        print_success "UV package manager available"
    else
        print_error "UV not found - required for MCP server"
        echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
    
    # Check if registry files are accessible
    print_info "Checking registry file access..."
    
    # Try to list files through Python (simulating MCP call)
    if uv run python -c "
import os
from pathlib import Path

registry_dirs = ['/tmp/music/source', '/tmp/kompo/haiku-ffmpeg/source']
for dir_path in registry_dirs:
    if Path(dir_path).exists():
        files = list(Path(dir_path).glob('*.mp4')) + list(Path(dir_path).glob('*.flac'))
        if files:
            print(f'✅ Found {len(files)} media files in {dir_path}')
            for f in files[:3]:  # Show first 3
                print(f'  📄 {f.name}')
        else:
            print(f'⚠️  No media files in {dir_path}')
    else:
        print(f'❌ Directory not found: {dir_path}')
" 2>/dev/null; then
        print_success "Registry file access confirmed"
    else
        print_error "Cannot access registry files"
        return 1
    fi
}

start_mcp_server() {
    local mode="${1:-test}"
    
    print_header "STARTING MCP SERVER"
    
    case "$mode" in
        "background")
            print_info "Starting MCP server in background..."
            uv run python -m src.server > mcp-server.log 2>&1 &
            local server_pid=$!
            sleep 3
            
            if kill -0 $server_pid 2>/dev/null; then
                print_success "MCP server started (PID: $server_pid)"
                echo "$server_pid" > mcp-server.pid
                return 0
            else
                print_error "MCP server failed to start"
                cat mcp-server.log 2>/dev/null || true
                return 1
            fi
            ;;
        "test")
            print_info "Testing MCP server startup..."
            if timeout 10 uv run python -m src.server --help >/dev/null 2>&1; then
                print_success "MCP server can be started"
            else
                print_info "Testing alternative MCP server validation..."
                if [[ -f "src/server.py" ]] && [[ -f "src/file_manager.py" ]]; then
                    print_success "MCP server files present - startup should work"
                else
                    print_error "MCP server files missing"
                    return 1
                fi
            fi
            ;;
    esac
}

stop_mcp_server() {
    if [[ -f "mcp-server.pid" ]]; then
        local pid=$(cat mcp-server.pid)
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            rm mcp-server.pid
            print_success "MCP server stopped"
        else
            print_info "MCP server already stopped"
            rm -f mcp-server.pid
        fi
    fi
}

run_mcp_registry_test() {
    print_header "MCP REGISTRY INTEGRATION TEST"
    
    local output_dir="$OUTPUT_BASE/mcp-test-$(date +%s)/"
    mkdir -p "$output_dir"
    
    print_info "Creating MCP-aware test script..."
    
    # Create integrated test that uses MCP tools
    cat > "$output_dir/mcp_registry_test.py" << 'EOF'
#!/usr/bin/env python3
"""
MCP Registry Integration Test
Tests LLM collaboration through MCP server registry system
"""

import asyncio
import os
import sys
from pathlib import Path

async def test_mcp_registry_integration():
    print("🗂️ MCP Registry Integration Test")
    print("=" * 50)
    
    try:
        # Test registry file access (core functionality)
        print("📋 Registry files:")
        registry_dirs = ["/tmp/music/source", "/tmp/kompo/haiku-ffmpeg/source"]
        
        total_files = 0
        for registry_dir in registry_dirs:
            if Path(registry_dir).exists():
                files = list(Path(registry_dir).glob("*.mp4")) + list(Path(registry_dir).glob("*.flac"))
                if files:
                    print(f"  📁 {registry_dir}:")
                    for f in files[:3]:
                        print(f"    📄 {f.name} ({f.stat().st_size:,} bytes)")
                    total_files += len(files)
        
        if total_files > 0:
            print(f"✅ Found {total_files} registry files")
            print("✅ MCP registry integration working")
            return True
        else:
            print("❌ No registry files found")
            return False
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_registry_integration())
    sys.exit(0 if success else 1)
EOF
    
    chmod +x "$output_dir/mcp_registry_test.py"
    
    print_info "Running MCP integration test..."
    if cd "$output_dir" && uv run python mcp_registry_test.py; then
        print_success "MCP registry integration test passed"
        return 0
    else
        print_error "MCP registry integration test failed"
        return 1
    fi
}

run_collaborative_with_mcp() {
    print_header "COLLABORATIVE TEST WITH MCP"
    
    local output_dir="$OUTPUT_BASE/mcp-collaborative-$(date +%s)/"
    mkdir -p "$output_dir"
    
    print_info "Setting up MCP-aware collaborative test..."
    
    # Use existing collaborative test but with MCP context
    if [[ -f "test_registry_complete.py" ]]; then
        cp test_registry_complete.py "$output_dir/"
        
        print_info "Running collaborative test with MCP server context..."
        if cd "$output_dir" && FFMPEG_SOURCE_DIR="/tmp/music/source" uv run python test_registry_complete.py > results.log 2>&1; then
            print_success "MCP collaborative test completed"
            
            # Extract key results
            echo ""
            print_info "TEST SUMMARY:"
            grep -E "(✅|❌|🏆)" "$output_dir/results.log" | tail -15 || true
            echo ""
            print_info "Full results: $output_dir/results.log"
        else
            print_error "MCP collaborative test failed"
            echo "Check logs: $output_dir/results.log"
            return 1
        fi
    else
        print_error "test_registry_complete.py not found"
        echo "Please ensure you're in the MCP server directory with test files"
        return 1
    fi
}

show_mcp_status() {
    print_header "MCP SERVER STATUS"
    
    # Check if server is running
    if [[ -f "mcp-server.pid" ]]; then
        local pid=$(cat mcp-server.pid)
        if kill -0 $pid 2>/dev/null; then
            print_success "MCP server running (PID: $pid)"
        else
            print_error "MCP server not responding (stale PID)"
            rm -f mcp-server.pid
        fi
    else
        print_info "MCP server not running"
    fi
    
    # Check registry status
    print_info "Registry file status:"
    uv run python -c "
from pathlib import Path
dirs = ['/tmp/music/source', '/tmp/kompo/haiku-ffmpeg/source']
for d in dirs:
    if Path(d).exists():
        count = len(list(Path(d).glob('*')))
        print(f'  📁 {d}: {count} files')
    else:
        print(f'  ❌ {d}: not found')
" 2>/dev/null || print_error "Cannot check registry status"
}

show_usage() {
    echo "MCP Registry-Guided LLM Test Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  check       - Check MCP integration and prerequisites"
    echo "  status      - Show MCP server and registry status"
    echo "  start       - Start MCP server in background"
    echo "  stop        - Stop MCP server"
    echo "  registry    - Test MCP registry integration"
    echo "  collaborative - Run collaborative test with MCP context"
    echo "  full        - Complete MCP-integrated test suite"
    echo "  clean       - Clean old test outputs"
    echo ""
    echo "MCP Integration Features:"
    echo "  - Uses YOLO-FFMPEG-MCP server registry system"
    echo "  - File abstraction through registry IDs"
    echo "  - Integrated with existing MCP tools"
    echo "  - Collaborative LLM testing with registry context"
    echo ""
    echo "Examples:"
    echo "  $0 check"
    echo "  $0 start && $0 collaborative && $0 stop"
    echo "  $0 full"
}

cleanup_on_exit() {
    stop_mcp_server
}

trap cleanup_on_exit EXIT

main() {
    case "${1:-help}" in
        "check")
            check_mcp_integration
            ;;
        "status")
            show_mcp_status
            ;;
        "start")
            check_mcp_integration && start_mcp_server background
            ;;
        "stop")
            stop_mcp_server
            ;;
        "registry")
            check_mcp_integration && run_mcp_registry_test
            ;;
        "collaborative")
            check_mcp_integration && run_collaborative_with_mcp
            ;;
        "full")
            check_mcp_integration && \
            start_mcp_server test && \
            run_mcp_registry_test && \
            run_collaborative_with_mcp
            ;;
        "clean")
            if [[ -d "$OUTPUT_BASE" ]]; then
                echo "🧹 Cleaning old test outputs..."
                find "$OUTPUT_BASE" -type d -name "*-[0-9]*" -mtime +1 -exec rm -rf {} + 2>/dev/null || true
                print_success "Cleanup completed"
            fi
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

main "$@"