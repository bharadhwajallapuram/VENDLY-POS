# Docker Health Check Script for Vendly API
# ==========================================
# Used in Dockerfile HEALTHCHECK instruction

#!/bin/bash

API_URL="${API_URL:-http://localhost:8000}"
TIMEOUT="${TIMEOUT:-5}"

# Check basic liveness
RESPONSE=$(curl -s -m $TIMEOUT -w "%{http_code}" "$API_URL/health/live" -o /dev/null 2>/dev/null)

if [ "$RESPONSE" = "200" ]; then
    # Check detailed health
    DETAILED=$(curl -s -m $TIMEOUT "$API_URL/health/detailed" 2>/dev/null)
    
    if echo "$DETAILED" | grep -q '"status":"healthy"'; then
        exit 0  # Healthy
    else
        exit 1  # Degraded but running
    fi
else
    exit 1  # Unhealthy
fi
