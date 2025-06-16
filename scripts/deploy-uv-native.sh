#!/bin/bash
# UV-Native Deployment Script for FFMPEG MCP Server
# Ultra-fast deployment without containers using UV package manager

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ffmpeg-mcp-server"
UV_VERSION=">=0.5.0"
PYTHON_VERSION="3.13"
SERVICE_PORT="8000"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} ⚡ UV-Native FFMPEG MCP Deploy${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_system_deps() {
    print_info "Checking system dependencies..."
    
    # Check FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        print_warning "FFmpeg not found. Installing..."
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install ffmpeg
        elif [[ -f /etc/debian_version ]]; then
            sudo apt-get update && sudo apt-get install -y ffmpeg mediainfo libsndfile1 libopencv-dev
        elif [[ -f /etc/redhat-release ]]; then
            sudo dnf install -y ffmpeg mediainfo libsndfile1-devel opencv-devel
        else
            print_error "Please install FFmpeg manually"
            exit 1
        fi
    fi
    
    print_success "FFmpeg $(ffmpeg -version | head -1 | cut -d' ' -f3) available"
}

install_uv() {
    print_info "Installing/upgrading UV package manager..."
    
    if ! command -v uv &> /dev/null; then
        print_info "Installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # Add UV to PATH for current session
        export PATH="$HOME/.local/bin:$PATH"
        
        # Verify installation
        if ! command -v uv &> /dev/null; then
            print_error "UV installation failed. Please install manually: https://docs.astral.sh/uv/"
            exit 1
        fi
    fi
    
    print_success "UV $(uv --version | cut -d' ' -f2) available"
}

setup_environment() {
    print_info "Setting up UV project environment..."
    
    # Initialize UV project if not already done
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found. Run from project root."
        exit 1
    fi
    
    # Create virtual environment with UV (10x faster than venv)
    print_info "Creating virtual environment with Python $PYTHON_VERSION..."
    uv venv --python $PYTHON_VERSION .venv
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies with UV (ultra-fast)
    print_info "Installing dependencies with UV..."
    uv sync
    
    # Create necessary directories
    mkdir -p /tmp/music/{source,temp,metadata,screenshots,finished}
    
    print_success "Environment setup complete"
}

create_systemd_service() {
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_warning "Systemd service creation skipped (not Linux)"
        return
    fi
    
    print_info "Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"
    
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=FFMPEG MCP Server (UV-Native)
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/.venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$(pwd)/.venv/bin/python -m src.server
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$APP_NAME

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/tmp/music

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable $APP_NAME
    
    print_success "Systemd service created: $APP_NAME"
}

create_launchd_service() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        return
    fi
    
    print_info "Creating macOS LaunchAgent..."
    
    PLIST_FILE="$HOME/Library/LaunchAgents/com.ffmpeg.mcp.server.plist"
    
    tee $PLIST_FILE > /dev/null <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ffmpeg.mcp.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(pwd)/.venv/bin/python</string>
        <string>-m</string>
        <string>src.server</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ffmpeg-mcp-server.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ffmpeg-mcp-server.error.log</string>
</dict>
</plist>
EOF
    
    launchctl load $PLIST_FILE
    
    print_success "macOS LaunchAgent created and loaded"
}

run_dev() {
    print_info "Starting development server..."
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Start server with UV run (optimized)
    print_info "Server starting on http://localhost:$SERVICE_PORT"
    uv run python -m src.server
}

run_production() {
    print_info "Starting production server..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start $APP_NAME
        sudo systemctl status $APP_NAME --no-pager
        
        print_success "Production server started with systemd"
        print_info "View logs: sudo journalctl -u $APP_NAME -f"
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        launchctl start com.ffmpeg.mcp.server
        
        print_success "Production server started with launchd"
        print_info "View logs: tail -f /tmp/ffmpeg-mcp-server.log"
    else
        print_warning "Running in foreground mode (no service manager)"
        run_dev
    fi
}

run_tests() {
    print_info "Running tests with UV..."
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Run tests with UV (faster test discovery and execution)
    uv run pytest tests/ci/ -v --tb=short
    
    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed"
        exit 1
    fi
}

benchmark() {
    print_info "Running UV vs pip performance benchmark..."
    
    # Create temporary directory for benchmark
    BENCH_DIR=$(mktemp -d)
    cd $BENCH_DIR
    
    # Benchmark UV
    print_info "Benchmarking UV installation speed..."
    time uv venv test-uv && \
    time uv pip install --venv test-uv fastmcp mcp pydantic pytest opencv-python-headless pillow numpy
    
    # Benchmark pip (for comparison)
    print_info "Benchmarking pip installation speed..."
    python -m venv test-pip && \
    source test-pip/bin/activate && \
    time pip install fastmcp mcp pydantic pytest opencv-python-headless pillow numpy
    
    # Cleanup
    cd - && rm -rf $BENCH_DIR
    
    print_success "Benchmark complete. UV should be 10-100x faster!"
}

cleanup() {
    print_warning "Cleaning up UV-native deployment..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl stop $APP_NAME 2>/dev/null || true
        sudo systemctl disable $APP_NAME 2>/dev/null || true
        sudo rm -f /etc/systemd/system/$APP_NAME.service
        sudo systemctl daemon-reload
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        launchctl unload $HOME/Library/LaunchAgents/com.ffmpeg.mcp.server.plist 2>/dev/null || true
        rm -f $HOME/Library/LaunchAgents/com.ffmpeg.mcp.server.plist
    fi
    
    # Remove virtual environment
    read -p "Remove virtual environment? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        print_success "Virtual environment removed"
    fi
    
    print_success "Cleanup completed"
}

show_help() {
    print_header
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup    - Install UV and setup environment"
    echo "  dev      - Start development server"
    echo "  prod     - Start production server with service"
    echo "  test     - Run test suite with UV"
    echo "  bench    - Benchmark UV vs pip performance"
    echo "  clean    - Clean up deployment"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup          # Initial setup"
    echo "  $0 dev            # Development server"
    echo "  $0 prod           # Production deployment"
    echo ""
    echo "UV-Native advantages:"
    echo "  ⚡ 10-100x faster package installation"
    echo "  🚫 No container overhead"
    echo "  🔧 Native system integration"
    echo "  💾 Smaller resource footprint"
    echo "  🛡️  System-level security controls"
    echo "  📊 Better performance monitoring"
}

# Main script logic
case "${1:-help}" in
    setup)
        print_header
        check_system_deps
        install_uv
        setup_environment
        create_systemd_service
        create_launchd_service
        print_success "Setup complete! Run '$0 dev' to start development server"
        ;;
    dev)
        print_header
        run_dev
        ;;
    prod)
        print_header
        run_production
        ;;
    test)
        print_header
        run_tests
        ;;
    bench)
        print_header
        benchmark
        ;;
    clean)
        print_header
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac