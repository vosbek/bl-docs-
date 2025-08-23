#!/bin/bash

# Multi-Agent Jira Card Creator - Restart Script
# This script safely restarts the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ✗ $1${NC}"
}

# Parse command line arguments
REBUILD=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild)
            REBUILD=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            echo -e "${BLUE}"
            echo "=============================================="
            echo "  Multi-Agent Jira Card Creator - Restart"
            echo "=============================================="
            echo -e "${NC}"
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "OPTIONS:"
            echo "  --rebuild    Rebuild containers from scratch"
            echo "  --clean      Clean up unused containers and images"
            echo "  -h, --help   Show this help message"
            echo ""
            echo "EXAMPLES:"
            echo "  $0              # Simple restart"
            echo "  $0 --rebuild    # Restart with container rebuild"
            echo "  $0 --clean      # Restart with cleanup"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}"
echo "=============================================="
echo "  Multi-Agent Jira Card Creator"
echo "  Restarting Application..."
echo "=============================================="
echo -e "${NC}"

# Determine docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Stop the application
print_step "Stopping current services..."
if timeout 60s $DOCKER_COMPOSE_CMD down --remove-orphans; then
    print_success "Services stopped successfully"
else
    print_error "Graceful stop failed, forcing shutdown..."
    $DOCKER_COMPOSE_CMD kill
    $DOCKER_COMPOSE_CMD down --remove-orphans
    print_success "Services force stopped"
fi

# Clean up if requested
if [ "$CLEAN" = true ]; then
    print_step "Cleaning up unused containers and images..."
    docker system prune -f
    print_success "Cleanup completed"
fi

# Wait a moment to ensure everything is stopped
sleep 2

# Start the application
print_step "Starting services..."

if [ "$REBUILD" = true ]; then
    print_step "Rebuilding containers..."
    $DOCKER_COMPOSE_CMD up -d --build --force-recreate
else
    $DOCKER_COMPOSE_CMD up -d
fi

if [ $? -eq 0 ]; then
    print_success "Services started successfully"
else
    print_error "Failed to start services"
    exit 1
fi

# Wait for services to be ready
print_step "Waiting for services to become healthy..."

HEALTH_CHECK_TIMEOUT=120
HEALTH_CHECK_INTERVAL=5
elapsed=0
backend_healthy=false
frontend_healthy=false

while [ $elapsed -lt $HEALTH_CHECK_TIMEOUT ]; do
    # Check backend health
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        if [ "$backend_healthy" = false ]; then
            print_success "Backend is healthy"
            backend_healthy=true
        fi
    fi
    
    # Check frontend health
    if curl -s http://localhost:4200 > /dev/null 2>&1; then
        if [ "$frontend_healthy" = false ]; then
            print_success "Frontend is healthy"
            frontend_healthy=true
        fi
    fi
    
    # If both services are healthy, we're done
    if [ "$backend_healthy" = true ] && [ "$frontend_healthy" = true ]; then
        break
    fi
    
    # Show progress every 15 seconds
    if [ $((elapsed % 15)) -eq 0 ] && [ $elapsed -gt 0 ]; then
        echo -e "${YELLOW}  Still waiting for services... (${elapsed}s elapsed)${NC}"
    fi
    
    sleep $HEALTH_CHECK_INTERVAL
    elapsed=$((elapsed + HEALTH_CHECK_INTERVAL))
done

if [ "$backend_healthy" != true ] || [ "$frontend_healthy" != true ]; then
    print_error "Services failed to become healthy within ${HEALTH_CHECK_TIMEOUT}s"
    echo ""
    echo "Container status:"
    $DOCKER_COMPOSE_CMD ps
    echo ""
    echo "Run './logs.sh' to check the logs for errors."
    exit 1
fi

# Run a quick system test
print_step "Running quick system test..."

# Test backend API
health_response=$(curl -s http://localhost:8000/api/health)
if echo "$health_response" | grep -q '"status"'; then
    print_success "Backend API test passed"
else
    print_error "Backend API test failed"
    echo "Response: $health_response"
    echo "Run './health-check.sh' for detailed diagnostics."
    exit 1
fi

# Show success message
echo ""
echo -e "${GREEN}=============================================="
echo "  🔄 Application Restarted Successfully!"
echo "=============================================="
echo -e "${NC}"
echo "Application URLs:"
echo "  📊 Dashboard:    http://localhost:4200"
echo "  🔧 Backend API:  http://localhost:8000"
echo "  📚 API Docs:     http://localhost:8000/docs"
echo ""
echo "Quick Commands:"
echo "  📋 View logs:    ./logs.sh"
echo "  ❤️ Health check: ./health-check.sh"
echo "  🛑 Stop app:     ./stop.sh"
echo ""

# Show container status
echo "Container Status:"
$DOCKER_COMPOSE_CMD ps

echo ""
echo -e "${GREEN}Restart completed successfully!${NC}"