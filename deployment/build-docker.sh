#!/bin/bash
# FFMPEG MCP Server - Docker Build and Setup Script
# Usage: ./build-docker.sh [option]
# Options: build, run, dev, test, clean, help

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="ffmpeg-mcp"
VERSION="latest"
CONTAINER_NAME="ffmpeg-mcp-server"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} FFMPEG MCP Server Docker Setup${NC}"
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

check_requirements() {
    print_info "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

build_image() {
    print_info "Building Docker image: $IMAGE_NAME:$VERSION"
    
    docker build -t $IMAGE_NAME:$VERSION .
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
        
        # Display image info
        echo ""
        print_info "Image details:"
        docker images $IMAGE_NAME:$VERSION
    else
        print_error "Docker build failed"
        exit 1
    fi
}

run_production() {
    print_info "Starting FFMPEG MCP Server in production mode..."
    
    # Create test-media directory if it doesn't exist
    if [ ! -d "./test-media" ]; then
        mkdir -p ./test-media
        print_warning "Created ./test-media directory. Add your test video files here."
    fi
    
    # Start with docker-compose
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        print_success "FFMPEG MCP Server started successfully"
        echo ""
        print_info "Server Status:"
        docker-compose ps
        
        echo ""
        print_info "Server URLs:"
        echo "  🌐 MCP Server: http://localhost:8000"
        
        echo ""
        print_info "Useful commands:"
        echo "  📋 View logs: docker-compose logs -f"
        echo "  🔄 Restart: docker-compose restart"
        echo "  🛑 Stop: docker-compose down"
        echo "  🧪 Test: curl http://localhost:8000/health"
    else
        print_error "Failed to start server"
        exit 1
    fi
}

run_development() {
    print_info "Starting FFMPEG MCP Server in development mode..."
    
    # Create test-media directory if it doesn't exist
    if [ ! -d "./test-media" ]; then
        mkdir -p ./test-media
        print_warning "Created ./test-media directory. Add your test video files here."
    fi
    
    # Start with development profile
    docker-compose --profile dev up -d
    
    if [ $? -eq 0 ]; then
        print_success "FFMPEG MCP Server (dev mode) started successfully"
        echo ""
        print_info "Development URLs:"
        echo "  🌐 MCP Server: http://localhost:8000"
        echo "  🔍 MCP Inspector: http://localhost:6274"
        
        echo ""
        print_info "Development commands:"
        echo "  📝 Edit code: Files are mounted from ./src/"
        echo "  🧪 Run tests: docker-compose exec ffmpeg-mcp python -m pytest tests/ -v"
        echo "  🐚 Shell access: docker-compose exec ffmpeg-mcp /bin/bash"
    else
        print_error "Failed to start development server"
        exit 1
    fi
}

run_tests() {
    print_info "Running tests in Docker container..."
    
    # Ensure container is built and running
    docker-compose build ffmpeg-mcp
    docker-compose up -d ffmpeg-mcp
    
    # Wait for container to be ready
    print_info "Waiting for container to be ready..."
    sleep 10
    
    # Run tests
    docker-compose exec ffmpeg-mcp python -m pytest tests/ -v
    
    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed"
        print_info "Check logs with: docker-compose logs ffmpeg-mcp"
    fi
}

clean_docker() {
    print_warning "Cleaning up Docker resources..."
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove image
    docker rmi $IMAGE_NAME:$VERSION 2>/dev/null || true
    
    # Remove volumes (with confirmation)
    echo ""
    read -p "Remove persistent volumes? This will delete all cached data (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume rm ffmpeg-temp ffmpeg-screenshots ffmpeg-metadata ffmpeg-logs 2>/dev/null || true
        print_success "Volumes removed"
    fi
    
    # Prune unused resources
    docker system prune -f
    
    print_success "Cleanup completed"
}

show_help() {
    print_header
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build    - Build Docker image"
    echo "  run      - Start server in production mode"
    echo "  rebuild  - Force rebuild image and start server"
    echo "  dev      - Start server in development mode (with MCP Inspector)"
    echo "  test     - Run tests in container"
    echo "  clean    - Clean up Docker resources"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build          # Build the image"
    echo "  $0 run            # Start production server"
    echo "  $0 rebuild        # Force rebuild and start"
    echo "  $0 dev            # Start development server with inspector"
    echo "  $0 test           # Run test suite"
    echo ""
    echo "For more detailed documentation, see DOCKER_SETUP.md"
}

# Main script logic
case "${1:-help}" in
    build)
        print_header
        check_requirements
        build_image
        ;;
    run)
        print_header
        check_requirements
        build_image
        run_production
        ;;
    rebuild)
        print_header
        check_requirements
        print_info "Rebuilding Docker image..."
        docker-compose build --no-cache ffmpeg-mcp
        run_production
        ;;
    dev)
        print_header
        check_requirements
        build_image
        run_development
        ;;
    test)
        print_header
        check_requirements
        run_tests
        ;;
    clean)
        print_header
        clean_docker
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