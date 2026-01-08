#!/bin/bash
# Health check script for deployment verification

set -e

API_URL="${API_URL:-http://localhost:8000}"
MAX_RETRIES="${MAX_RETRIES:-30}"
RETRY_INTERVAL="${RETRY_INTERVAL:-2}"

echo "🔍 Checking API health at $API_URL"

for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf "$API_URL/health" > /dev/null; then
        echo "✅ API is healthy!"
        exit 0
    fi

    echo "⏳ Attempt $i/$MAX_RETRIES failed, retrying in ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
done

echo "❌ API health check failed after $MAX_RETRIES attempts"
exit 1
