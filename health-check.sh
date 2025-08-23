#!/bin/bash

# Multi-Agent Jira Card Creator - Health Check Script
# This script performs comprehensive health checks on all application components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Health check results
OVERALL_HEALTH=true
ISSUES=()

print_header() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  Multi-Agent Jira Card Creator"
    echo "  Health Check Report"
    echo "  $(date)"
    echo "=============================================="
    echo -e "${NC}"
}

print_check() {
    echo -e "${YELLOW}[CHECK] $1${NC}"
}

print_pass() {
    echo -e "${GREEN}[PASS]  ✓ $1${NC}"
}

print_fail() {
    echo -e "${RED}[FAIL]  ✗ $1${NC}"
    OVERALL_HEALTH=false
    ISSUES+=("$1")
}

print_warning() {
    echo -e "${YELLOW}[WARN]  ⚠ $1${NC}"
}

# Determine docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    DOCKER_COMPOSE_CMD="docker compose"
fi

check_docker() {
    print_check "Docker environment"
    
    if command -v docker &> /dev/null; then
        print_pass "Docker is installed"
    else
        print_fail "Docker is not installed"
        return
    fi
    
    if docker info &> /dev/null; then
        print_pass "Docker is running"
    else
        print_fail "Docker is not running"
        return
    fi
    
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        print_pass "Docker Compose is available"
    else
        print_fail "Docker Compose is not available"
    fi
}

check_containers() {
    print_check "Container status"
    
    local containers=$($DOCKER_COMPOSE_CMD ps -q 2>/dev/null || echo "")
    
    if [ -z "$containers" ]; then
        print_fail "No containers are running"
        return
    fi
    
    # Check individual containers
    local backend_running=false
    local frontend_running=false
    
    while read -r container; do
        if [ -n "$container" ]; then
            local name=$(docker inspect --format '{{.Name}}' "$container" | sed 's|/||')
            local status=$(docker inspect --format '{{.State.Status}}' "$container")
            
            if [[ "$name" == *"backend"* ]] || [[ "$name" == *"jira-backend"* ]]; then
                if [ "$status" = "running" ]; then
                    print_pass "Backend container is running"
                    backend_running=true
                else
                    print_fail "Backend container is not running (status: $status)"
                fi
            elif [[ "$name" == *"frontend"* ]] || [[ "$name" == *"jira-frontend"* ]]; then
                if [ "$status" = "running" ]; then
                    print_pass "Frontend container is running"
                    frontend_running=true
                else
                    print_fail "Frontend container is not running (status: $status)"
                fi
            fi
        fi
    done <<< "$containers"
    
    if [ "$backend_running" = false ]; then
        print_fail "Backend container is not detected"
    fi
    
    if [ "$frontend_running" = false ]; then
        print_fail "Frontend container is not detected"
    fi
}

check_api_endpoints() {
    print_check "API endpoint health"
    
    # Backend health check
    local health_response=$(curl -s --max-time 10 http://localhost:8000/api/health 2>/dev/null || echo "")
    
    if [ -n "$health_response" ] && echo "$health_response" | grep -q '"status"'; then
        local status=$(echo "$health_response" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
        if [ "$status" = "healthy" ]; then
            print_pass "Backend API health endpoint responding (status: $status)"
        else
            print_warning "Backend API health endpoint responding but status is: $status"
        fi
    else
        print_fail "Backend API health endpoint not responding"
        return
    fi
    
    # Test repositories endpoint
    local repos_response=$(curl -s --max-time 10 http://localhost:8000/api/repositories 2>/dev/null || echo "")
    
    if [ -n "$repos_response" ] && echo "$repos_response" | grep -q '"repositories"'; then
        print_pass "Repository scanner API responding"
    else
        print_fail "Repository scanner API not responding"
    fi
    
    # Test API docs
    local docs_response=$(curl -s --max-time 10 -I http://localhost:8000/docs 2>/dev/null || echo "")
    
    if echo "$docs_response" | grep -q "200 OK"; then
        print_pass "API documentation accessible"
    else
        print_warning "API documentation not accessible"
    fi
}

check_frontend() {
    print_check "Frontend accessibility"
    
    local frontend_response=$(curl -s --max-time 10 -I http://localhost:4200 2>/dev/null || echo "")
    
    if echo "$frontend_response" | grep -q "200 OK"; then
        print_pass "Frontend is accessible"
    else
        print_fail "Frontend is not accessible"
    fi
}

check_configuration() {
    print_check "Configuration validation"
    
    if [ -f .env ]; then
        print_pass ".env configuration file exists"
        
        source .env
        
        # Check critical variables
        if [ -n "$AWS_ACCESS_KEY_ID" ]; then
            print_pass "AWS credentials configured"
        else
            print_fail "AWS credentials not configured"
        fi
        
        if [ -n "$REPOSITORIES_PATH" ] && [ -d "$REPOSITORIES_PATH" ]; then
            local repo_count=$(find "$REPOSITORIES_PATH" -mindepth 1 -maxdepth 1 -type d | wc -l)
            print_pass "Repository path exists with $repo_count directories"
        else
            print_fail "Repository path not configured or doesn't exist"
        fi
        
        if [ -n "$JIRA_URL" ]; then
            print_pass "Jira URL configured"
        else
            print_warning "Jira URL not configured"
        fi
        
    else
        print_fail ".env configuration file not found"
    fi
}

check_resources() {
    print_check "System resources"
    
    # Memory usage
    if command -v free &> /dev/null; then
        local mem_usage=$(free | awk '/^Mem:/{printf "%.0f", $3/$2*100}')
        if [ "$mem_usage" -lt 80 ]; then
            print_pass "Memory usage: ${mem_usage}%"
        else
            print_warning "High memory usage: ${mem_usage}%"
        fi
    fi
    
    # Disk space
    local disk_usage=$(df . | awk 'NR==2{printf "%.0f", $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 90 ]; then
        print_pass "Disk usage: ${disk_usage}%"
    else
        print_warning "High disk usage: ${disk_usage}%"
    fi
    
    # Docker system info
    local docker_info=$(docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}" 2>/dev/null || echo "")
    if [ -n "$docker_info" ]; then
        print_pass "Docker system resources available"
    else
        print_warning "Unable to check Docker system resources"
    fi
}

check_connectivity() {
    print_check "External connectivity"
    
    # AWS Bedrock connectivity (simplified check)
    if command -v dig &> /dev/null; then
        if dig +short bedrock.us-east-1.amazonaws.com > /dev/null 2>&1; then
            print_pass "AWS Bedrock DNS resolution working"
        else
            print_warning "AWS Bedrock DNS resolution failed"
        fi
    fi
    
    # General internet connectivity
    if curl -s --max-time 5 https://httpbin.org/get > /dev/null 2>&1; then
        print_pass "Internet connectivity working"
    else
        print_warning "Internet connectivity may be limited"
    fi
}

generate_report() {
    echo ""
    echo -e "${BLUE}=============================================="
    
    if [ "$OVERALL_HEALTH" = true ]; then
        echo -e "${GREEN}  ✅ OVERALL HEALTH: GOOD"
        echo -e "${BLUE}=============================================="
        echo -e "${NC}"
        echo "All critical systems are functioning normally."
        echo ""
        echo "Application URLs:"
        echo "  📊 Dashboard:   http://localhost:4200"
        echo "  🔧 Backend API: http://localhost:8000"
        echo "  📚 API Docs:    http://localhost:8000/docs"
    else
        echo -e "${RED}  ❌ OVERALL HEALTH: ISSUES DETECTED"
        echo -e "${BLUE}=============================================="
        echo -e "${NC}"
        echo -e "${RED}Issues found:${NC}"
        for issue in "${ISSUES[@]}"; do
            echo "  • $issue"
        done
        echo ""
        echo "Recommendations:"
        echo "  1. Check logs: ./logs.sh"
        echo "  2. Restart application: ./restart.sh"
        echo "  3. Review configuration: cat .env"
    fi
    
    echo -e "${NC}"
}

# Main execution
main() {
    print_header
    
    check_docker
    check_configuration
    check_containers
    check_api_endpoints
    check_frontend
    check_resources
    check_connectivity
    
    generate_report
    
    if [ "$OVERALL_HEALTH" = true ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"