#!/bin/bash
# ================================================
# Vendly POS - Redis Management Script
# ================================================

if [ $# -eq 0 ]; then
    echo "Usage: ./redis.sh [start|stop|status|logs|clean]"
    echo ""
    echo "Commands:"
    echo "  start    - Start Redis container"
    echo "  stop     - Stop Redis container"
    echo "  status   - Check Redis status"
    echo "  logs     - View Redis logs"
    echo "  clean    - Remove Redis container and data"
    echo ""
    exit 1
fi

case "$1" in
    start)
        echo "Starting Redis..."
        docker rm -f vendly-redis >/dev/null 2>&1
        docker run -d --name vendly-redis -p 6379:6379 -v redis-data:/data redis:7-alpine redis-server --appendonly yes
        sleep 2
        if docker exec vendly-redis redis-cli ping >/dev/null 2>&1; then
            echo "✓ Redis started successfully on port 6379"
            echo ""
            echo "You can now run your Vendly backend:"
            echo "  cd server"
            echo "  python -m uvicorn app.main:app --reload"
            exit 0
        else
            echo "✗ Redis failed to start"
            exit 1
        fi
        ;;
    stop)
        echo "Stopping Redis..."
        docker stop vendly-redis >/dev/null 2>&1
        echo "✓ Redis stopped"
        exit 0
        ;;
    status)
        docker ps -a --filter "name=vendly-redis" --format "{{.Names}}: {{.Status}}"
        if docker exec vendly-redis redis-cli ping >/dev/null 2>&1; then
            echo "✓ Redis is running"
            exit 0
        else
            echo "✗ Redis is not running"
            exit 1
        fi
        ;;
    logs)
        docker logs -f vendly-redis
        exit 0
        ;;
    clean)
        echo "Removing Redis container and data..."
        docker rm -f vendly-redis >/dev/null 2>&1
        docker volume rm redis-data >/dev/null 2>&1
        echo "✓ Redis cleaned up"
        exit 0
        ;;
    *)
        echo "Unknown command: $1"
        exit 1
        ;;
esac
