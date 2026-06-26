#!/bin/bash

# Railway.com startup script for TradingAgents service

# Set default environment variables if not provided
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}
export TRADINGAGENTS_SERVICE_WORKERS=${TRADINGAGENTS_SERVICE_WORKERS:-1}

# Check if API key is set
if [ -z "$TRADINGAGENTS_SERVICE_API_KEY" ]; then
    echo "Warning: TRADINGAGENTS_SERVICE_API_KEY is not set"
    echo "Setting a default API key for testing (DO NOT USE IN PRODUCTION)"
    export TRADINGAGENTS_SERVICE_API_KEY="railway-default-key-change-in-production"
fi

# Install dependencies if not already installed
if ! python -c "import tradingagents" &> /dev/null; then
    echo "Installing TradingAgents package..."
    pip install --no-cache-dir .
fi

# Start the service
echo "Starting TradingAgents service on $HOST:$PORT"
echo "Workers: $TRADINGAGENTS_SERVICE_WORKERS"

exec python scripts/run_service.py