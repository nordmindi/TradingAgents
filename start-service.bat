@echo off

REM TradingAgents Service Startup Script (Windows)

REM Check if .env file exists, if not copy from example
if not exist .env (
    echo Creating .env file from example...
    copy .env.example .env
    echo Please edit .env to configure your API keys and settings
    exit /b 1
)

REM Load environment variables from .env file
for /f "tokens=*" %%i in ('type .env') do (
    set "line=%%i"
    if not "!line:~0,1!"=="#" (
        for /f "tokens=1,* delims==" %%a in ("!line!") do (
            set "%%a=%%b"
        )
    )
)

REM Check if required environment variables are set
setlocal enabledelayedexpansion
if "!TRADINGAGENTS_SERVICE_API_KEY!"=="" (
    echo Error: TRADINGAGENTS_SERVICE_API_KEY is not set
    echo Please set it in your .env file
    exit /b 1
)

if "!TRADINGAGENTS_SERVICE_API_KEY!"=="change-me-in-production" (
    echo Error: TRADINGAGENTS_SERVICE_API_KEY is still the default value
    echo Please set it in your .env file
    exit /b 1
)

if "!TRADINGAGENTS_SERVICE_API_KEY!"=="admin-staging-9f8e7d6c-5b4a-3c2d-1e0f-123456789abc" (
    echo Warning: Using staging API key - OK for testing but change for production
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