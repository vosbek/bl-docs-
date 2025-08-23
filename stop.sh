#!/bin/bash

# Multi-Agent Jira Card Creator - Stop Script
# This script safely stops all application services

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

echo -e "${BLUE}"
echo "=============================================="
echo "  Multi-Agent Jira Card Creator"
echo "  Stopping Application..."
echo "=============================================="
echo -e "${NC}"

# Determine docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    DOCKER_COMPOSE_CMD="docker compose"
fi

print_step "Stopping services gracefully..."

# Stop services with timeout
if timeout 60s $DOCKER_COMPOSE_CMD down --remove-orphans; then
    print_success "Services stopped successfully"
else
    print_error "Graceful stop failed, forcing shutdown..."
    $DOCKER_COMPOSE_CMD kill
    $DOCKER_COMPOSE_CMD down --remove-orphans
    print_success "Services force stopped"
fi

# Check if any containers are still running
if $DOCKER_COMPOSE_CMD ps -q | grep -q .; then
    print_error "Some containers are still running:"
    $DOCKER_COMPOSE_CMD ps
    exit 1
else
    print_success "All services stopped"
fi

# Optional cleanup
if [ "$1" = "--clean" ]; then
    print_step "Cleaning up containers and networks..."
    docker system prune -f --volumes
    print_success "Cleanup completed"
fi

echo ""
echo -e "${GREEN}=============================================="
echo "  🛑 Application Stopped Successfully!"
echo "=============================================="
echo -e "${NC}"
echo "To start again, run:"
echo "  ./start.sh"
echo ""