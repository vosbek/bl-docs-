#!/bin/bash

# Multi-Agent Jira Card Creator - Logs Viewer Script
# This script provides easy access to application logs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determine docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    DOCKER_COMPOSE_CMD="docker compose"
fi

show_usage() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  Multi-Agent Jira Card Creator - Logs"
    echo "=============================================="
    echo -e "${NC}"
    echo "Usage: $0 [OPTIONS] [SERVICE]"
    echo ""
    echo "OPTIONS:"
    echo "  -f, --follow     Follow log output (like tail -f)"
    echo "  -t, --tail N     Show last N lines (default: 100)"
    echo "  --since TIME     Show logs since timestamp (e.g., '2023-01-01', '1h')"
    echo "  --errors         Show only ERROR level logs"
    echo "  --save FILE      Save logs to file"
    echo "  -h, --help       Show this help message"
    echo ""
    echo "SERVICES:"
    echo "  backend          Show backend API logs only"
    echo "  frontend         Show frontend logs only"
    echo "  all              Show all service logs (default)"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                          # Show last 100 lines of all logs"
    echo "  $0 -f                       # Follow all logs in real-time"
    echo "  $0 -t 50 backend           # Show last 50 lines of backend logs"
    echo "  $0 --since 1h --errors     # Show error logs from last hour"
    echo "  $0 --save app.log          # Save all logs to app.log file"
    echo ""
}

# Default values
FOLLOW=false
TAIL_LINES=100
SINCE=""
ERRORS_ONLY=false
SAVE_FILE=""
SERVICE="all"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -t|--tail)
            TAIL_LINES="$2"
            shift 2
            ;;
        --since)
            SINCE="$2"
            shift 2
            ;;
        --errors)
            ERRORS_ONLY=true
            shift
            ;;
        --save)
            SAVE_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        backend|frontend|all)
            SERVICE="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if services are running
if ! $DOCKER_COMPOSE_CMD ps -q > /dev/null 2>&1; then
    echo -e "${RED}Error: No services are running.${NC}"
    echo "Start the application first with: ./start.sh"
    exit 1
fi

# Build docker-compose logs command
LOGS_CMD="$DOCKER_COMPOSE_CMD logs"

if [ "$FOLLOW" = true ]; then
    LOGS_CMD="$LOGS_CMD -f"
fi

if [ -n "$TAIL_LINES" ]; then
    LOGS_CMD="$LOGS_CMD --tail=$TAIL_LINES"
fi

if [ -n "$SINCE" ]; then
    LOGS_CMD="$LOGS_CMD --since=$SINCE"
fi

# Add service filter
if [ "$SERVICE" != "all" ]; then
    LOGS_CMD="$LOGS_CMD $SERVICE"
fi

# Show header
echo -e "${BLUE}"
echo "=============================================="
echo "  Multi-Agent Jira Card Creator - Logs"
echo "=============================================="
echo -e "${NC}"

if [ "$SERVICE" = "all" ]; then
    echo "Showing logs for: All services"
else
    echo "Showing logs for: $SERVICE"
fi

if [ "$FOLLOW" = true ]; then
    echo "Mode: Following (real-time)"
    echo -e "${YELLOW}Press Ctrl+C to stop following logs${NC}"
else
    echo "Mode: Last $TAIL_LINES lines"
fi

if [ -n "$SINCE" ]; then
    echo "Since: $SINCE"
fi

if [ "$ERRORS_ONLY" = true ]; then
    echo "Filter: Errors only"
fi

if [ -n "$SAVE_FILE" ]; then
    echo "Saving to: $SAVE_FILE"
fi

echo ""

# Execute logs command
if [ "$ERRORS_ONLY" = true ]; then
    # Filter for error logs
    if [ -n "$SAVE_FILE" ]; then
        $LOGS_CMD 2>&1 | grep -i "error\|exception\|fail\|critical" | tee "$SAVE_FILE"
    else
        $LOGS_CMD 2>&1 | grep -i "error\|exception\|fail\|critical"
    fi
elif [ -n "$SAVE_FILE" ]; then
    # Save to file
    echo "Saving logs to $SAVE_FILE..."
    $LOGS_CMD > "$SAVE_FILE" 2>&1
    echo "Logs saved to $SAVE_FILE"
    echo ""
    echo "Recent logs:"
    tail -20 "$SAVE_FILE"
else
    # Normal log display
    $LOGS_CMD
fi

# Show helpful commands at the end (only if not following)
if [ "$FOLLOW" = false ] && [ -z "$SAVE_FILE" ]; then
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo "  ./logs.sh -f              # Follow logs in real-time"
    echo "  ./logs.sh --errors        # Show only errors"
    echo "  ./logs.sh backend         # Show backend logs only"
    echo "  ./health-check.sh         # Run health check"
    echo ""
fi