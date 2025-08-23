#!/bin/bash

# Multi-Agent Jira Card Creator - Startup Script
# This script provides an easy way to start the application with health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HEALTH_CHECK_TIMEOUT=300  # 5 minutes
HEALTH_CHECK_INTERVAL=10  # 10 seconds

print_header() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  Multi-Agent Jira Card Creator"
    echo "  Starting Application..."
    echo "=============================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ✗ $1${NC}"
}

check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        print_error ".env file not found. Please copy .env.template to .env and configure it."
        echo "Run: cp .env.template .env"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

check_configuration() {
    print_step "Validating configuration..."
    
    # Check required environment variables
    source .env
    
    missing_vars=()
    
    if [ -z "$AWS_ACCESS_KEY_ID" ]; then
        missing_vars+=("AWS_ACCESS_KEY_ID")
    fi
    
    if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        missing_vars+=("AWS_SECRET_ACCESS_KEY")
    fi
    
    if [ -z "$REPOSITORIES_PATH" ]; then
        missing_vars+=("REPOSITORIES_PATH")
    fi
    
    if [ -z "$JIRA_URL" ]; then
        missing_vars+=("JIRA_URL")
    fi
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required configuration variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo "Please update your .env file."
        exit 1
    fi
    
    # Check if repositories path exists
    if [ ! -d "$REPOSITORIES_PATH" ]; then
        print_error "Repository path does not exist: $REPOSITORIES_PATH"
        echo "Please ensure the REPOSITORIES_PATH in .env points to a valid directory."
        exit 1
    fi
    
    print_success "Configuration validation passed"
}

start_services() {
    print_step "Starting services..."
    
    # Use docker-compose or docker compose based on availability
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        DOCKER_COMPOSE_CMD="docker compose"
    fi
    
    # Stop any existing containers
    print_step "Stopping existing containers..."
    $DOCKER_COMPOSE_CMD down --remove-orphans 2>/dev/null || true
    
    # Start services
    print_step "Building and starting containers..."
    if $DOCKER_COMPOSE_CMD up -d --build; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
    
    # Wait a moment for containers to initialize
    sleep 5
}

wait_for_health() {
    print_step "Waiting for services to become healthy..."
    
    local elapsed=0
    local backend_healthy=false
    local frontend_healthy=false
    
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
        
        # Show progress
        if [ $((elapsed % 30)) -eq 0 ] && [ $elapsed -gt 0 ]; then
            echo -e "${YELLOW}  Still waiting... (${elapsed}s elapsed)${NC}"
        fi
        
        sleep $HEALTH_CHECK_INTERVAL
        elapsed=$((elapsed + HEALTH_CHECK_INTERVAL))
    done
    
    if [ "$backend_healthy" != true ] || [ "$frontend_healthy" != true ]; then
        print_error "Services failed to become healthy within ${HEALTH_CHECK_TIMEOUT}s"
        echo ""
        echo "Checking container status:"
        $DOCKER_COMPOSE_CMD ps
        echo ""
        echo "Recent logs:"
        $DOCKER_COMPOSE_CMD logs --tail=20
        exit 1
    fi
}

perform_system_test() {
    print_step "Performing system test..."
    
    # Test backend API
    local health_response=$(curl -s http://localhost:8000/api/health)
    if echo "$health_response" | grep -q '"status"'; then
        print_success "Backend API test passed"
    else
        print_error "Backend API test failed"
        echo "Response: $health_response"
        return 1
    fi
    
    # Test repository scanning
    local repos_response=$(curl -s http://localhost:8000/api/repositories)
    if echo "$repos_response" | grep -q '"repositories"'; then
        print_success "Repository scanner test passed"
    else
        print_error "Repository scanner test failed"
        echo "Response: $repos_response"
        return 1
    fi
    
    return 0
}

show_status() {
    echo ""
    echo -e "${GREEN}=============================================="
    echo "  🚀 Application Started Successfully!"
    echo "=============================================="
    echo -e "${NC}"
    echo "Application URLs:"
    echo "  📊 Dashboard:    http://localhost:4200"
    echo "  🔧 Backend API:  http://localhost:8000"
    echo "  📚 API Docs:     http://localhost:8000/docs"
    echo ""
    echo "Quick Commands:"
    echo "  📋 View logs:    ./logs.sh"
    echo "  🛑 Stop app:     ./stop.sh"
    echo "  🔄 Restart:      ./restart.sh"
    echo "  ❤️ Health check: ./health-check.sh"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Open http://localhost:4200 in your browser"
    echo "  2. Check that all system status indicators are green"
    echo "  3. Create your first task to test the workflow"
    echo ""
}

# Main execution
main() {
    print_header
    
    # Trap exit signals to clean up
    trap 'echo -e "${RED}Startup interrupted${NC}"; exit 1' INT TERM
    
    check_prerequisites
    check_configuration
    start_services
    wait_for_health
    
    if perform_system_test; then
        show_status
        exit 0
    else
        print_error "System test failed. Check the logs for details."
        echo "Run './logs.sh' to view detailed logs."
        exit 1
    fi
}

# Run main function
main "$@"