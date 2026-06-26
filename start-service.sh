#!/bin/bash

# TradingAgents Service Startup Script

# Check if .env file exists, if not copy from example
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env to configure your API keys and settings"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$TRADINGAGENTS_SERVICE_API_KEY" ] || [ "$TRADINGAGENTS_SERVICE_API_KEY" = "change-me-in-production" ]; then
    echo "Error: TRADINGAGENTS_SERVICE_API_KEY is not set or is still the default value"
    echo "Please set it in your .env file"
    exit 1
fi

# Install dependencies if not already installed
if ! python -c "import tradingagents" &> /dev/null; then
    echo "Installing TradingAgents package..."
    pip install -e .
fi

# Start the service
echo "Starting TradingAgents service..."
python scripts/run_service.py