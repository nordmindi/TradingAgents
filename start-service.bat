@echo off

REM TradingAgents Service Startup Script (Windows)

REM Check if .env file exists, if not copy from example
if not exist .env (
    echo Creating .env file from example...
    copy .env.example .env
    echo Please edit .env to configure your API keys and settings
    exit /b 1
)

REM Check if required environment variables are set
setlocal enabledelayedexpansion
if "%TRADINGAGENTS_SERVICE_API_KEY%"=="" (
    echo Error: TRADINGAGENTS_SERVICE_API_KEY is not set
    echo Please set it in your .env file
    exit /b 1
)

if "%TRADINGAGENTS_SERVICE_API_KEY%"=="change-me-in-production" (
    echo Error: TRADINGAGENTS_SERVICE_API_KEY is still the default value
    echo Please set it in your .env file
    exit /b 1
)

REM Install dependencies if not already installed
python -c "import tradingagents" >nul 2>&1
if errorlevel 1 (
    echo Installing TradingAgents package...
    pip install -e .
)

REM Start the service
echo Starting TradingAgents service...
python scripts/run_service.py

endlocal