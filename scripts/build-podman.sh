#!/bin/bash
# Podman Build Script for FFMPEG MCP Server
# Ultra-fast, secure, rootless container alternative to Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="ffmpeg-mcp-podman"
VERSION="latest"
CONTAINER_NAME="ffmpeg-mcp-server-podman"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} 🚀 Podman FFMPEG MCP Server${NC}"
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

check_podman() {
    print_info "Checking Podman availability..."
    
    if ! command -v podman &> /dev/null; then
        print_error "Podman not found. Installing..."
        
        # Auto-install on macOS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew install podman
            else
                print_error "Please install Homebrew first: https://brew.sh"
                exit 1
            fi
        
        # Auto-install on Ubuntu/Debian
        elif [[ -f /etc/debian_version ]]; then
            sudo apt-get update
            sudo apt-get install -y podman
        
        # Auto-install on RHEL/Fedora
        elif [[ -f /etc/redhat-release ]]; then
            sudo dnf install -y podman
        
        else
            print_error "Please install Podman: https://podman.io/getting-started/installation"
            exit 1
        fi
    fi
    
    print_success "Podman $(podman version --format '{{.Client.Version}}') available"
}

build_image() {
    print_info "Building Podman image: $IMAGE_NAME:$VERSION"
    
    # Build with Containerfile (Podman's preferred format) or fallback
    if [ -f "Containerfile" ]; then
        print_info "Using Containerfile for build..."
        podman build -f Containerfile -t $IMAGE_NAME:$VERSION .
    elif [ -f "docker/Dockerfile.ci-test" ]; then
        print_warning "Containerfile not found, using Docker CI test file..."
        podman build -f docker/Dockerfile.ci-test -t $IMAGE_NAME:$VERSION .
    else
        print_error "No suitable build file found (Containerfile or docker/Dockerfile.ci-test)"
        exit 1
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Podman image built successfully"
        
        # Display image info
        echo ""
        print_info "Image details:"
        podman images $IMAGE_NAME:$VERSION
    else
        print_error "Podman build failed"
        exit 1
    fi
}

run_rootless() {
    print_info "Starting FFMPEG MCP Server in rootless Podman container..."
    
    # Stop existing container if running
    podman stop $CONTAINER_NAME 2>/dev/null || true
    podman rm $CONTAINER_NAME 2>/dev/null || true
    
    # Create test-media directory if it doesn't exist
    if [ ! -d "./test-media" ]; then
        mkdir -p ./test-media
        print_warning "Created ./test-media directory. Add your test video files here."
    fi
    
    # Run rootless container with volume mounts
    podman run -d \
        --name $CONTAINER_NAME \
        --publish 8000:8000 \
        --volume ./test-media:/tmp/music/source:Z \
        --volume ./output:/tmp/music/temp:Z \
        --security-opt label=disable \
        $IMAGE_NAME:$VERSION
    
    if [ $? -eq 0 ]; then
        print_success "FFMPEG MCP Server started successfully (rootless)"
        echo ""
        print_info "Server Status:"
        podman ps --filter name=$CONTAINER_NAME
        
        echo ""
        print_info "Server URLs:"
        echo "  🌐 MCP Server: http://localhost:8000"
        
        echo ""
        print_info "Useful commands:"
        echo "  📋 View logs: podman logs -f $CONTAINER_NAME"
        echo "  🔄 Restart: podman restart $CONTAINER_NAME"
        echo "  🛑 Stop: podman stop $CONTAINER_NAME"
        echo "  🧪 Test: curl http://localhost:8000/health"
        echo "  🐚 Shell: podman exec -it $CONTAINER_NAME /bin/bash"
    else
        print_error "Failed to start server"
        exit 1
    fi
}

run_tests() {
    print_info "Running tests in Podman container..."
    
    # Build test container with fallback logic
    if [ -f "Containerfile" ]; then
        print_info "Building test container with Containerfile..."
        podman build -f Containerfile -t $IMAGE_NAME-test:latest .
    elif [ -f "docker/Dockerfile.ci-test" ]; then
        print_warning "Using Docker CI test file for testing..."
        podman build -f docker/Dockerfile.ci-test -t $IMAGE_NAME-test:latest .
    else
        print_error "No suitable build file found for testing"
        exit 1
    fi
    
    # Run tests
    podman run --rm \
        --volume ./tests:/app/tests:Z \
        $IMAGE_NAME-test:latest \
        python -m pytest tests/ci/ -v
    
    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed"
    fi
}

cleanup() {
    print_warning "Cleaning up Podman resources..."
    
    # Stop and remove containers
    podman stop $CONTAINER_NAME 2>/dev/null || true
    podman rm $CONTAINER_NAME 2>/dev/null || true
    
    # Remove images (with confirmation)
    echo ""
    read -p "Remove Podman images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        podman rmi $IMAGE_NAME:$VERSION 2>/dev/null || true
        podman rmi $IMAGE_NAME-test:latest 2>/dev/null || true
        print_success "Images removed"
    fi
    
    # Prune unused resources
    podman system prune -f
    
    print_success "Cleanup completed"
}

show_help() {
    print_header
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build    - Build Podman image"
    echo "  run      - Start server in rootless container"
    echo "  test     - Run tests in container"
    echo "  clean    - Clean up Podman resources"
    echo "  install  - Install Podman (if not present)"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build          # Build the Podman image"
    echo "  $0 run            # Start rootless server"
    echo "  $0 test           # Run test suite"
    echo ""
    echo "Podman advantages over Docker:"
    echo "  🔒 Rootless containers (enhanced security)"
    echo "  🚫 No daemon required (better resource usage)"
    echo "  ⚡ Faster startup times"
    echo "  🐧 Linux-native (better performance)"
    echo "  📜 OCI-compliant (full Docker compatibility)"
}

# Main script logic
case "${1:-help}" in
    build)
        print_header
        check_podman
        build_image
        ;;
    run)
        print_header
        check_podman
        build_image
        run_rootless
        ;;
    test)
        print_header
        check_podman
        run_tests
        ;;
    install)
        print_header
        check_podman
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