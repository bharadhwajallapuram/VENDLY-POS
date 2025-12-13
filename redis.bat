@echo off
REM ================================================
REM Vendly POS - Redis Management Script
REM ================================================

setlocal enabledelayedexpansion

if "%1%"=="" (
    echo Usage: redis.bat [start^|stop^|status^|logs^|clean]
    echo.
    echo Commands:
    echo   start    - Start Redis container
    echo   stop     - Stop Redis container
    echo   status   - Check Redis status
    echo   logs     - View Redis logs
    echo   clean    - Remove Redis container and data
    echo.
    exit /b 1
)

if "%1%"=="start" (
    echo Starting Redis...
    docker rm -f vendly-redis >nul 2>&1
    docker run -d --name vendly-redis -p 6379:6379 -v redis-data:/data redis:7-alpine redis-server --appendonly yes
    timeout /t 2 /nobreak
    docker exec vendly-redis redis-cli ping
    if errorlevel 1 (
        echo ✗ Redis failed to start
        exit /b 1
    )
    echo ✓ Redis started successfully on port 6379
    echo.
    echo You can now run your Vendly backend:
    echo   cd server
    echo   python -m uvicorn app.main:app --reload
    exit /b 0
)

if "%1%"=="stop" (
    echo Stopping Redis...
    docker stop vendly-redis >nul 2>&1
    echo ✓ Redis stopped
    exit /b 0
)

if "%1%"=="status" (
    docker ps -a --filter "name=vendly-redis" --format "{{.Names}}: {{.Status}}"
    if errorlevel 1 (
        echo ✗ Redis is not running
        exit /b 1
    )
    docker exec vendly-redis redis-cli ping
    exit /b 0
)

if "%1%"=="logs" (
    docker logs -f vendly-redis
    exit /b 0
)

if "%1%"=="clean" (
    echo Removing Redis container and data...
    docker rm -f vendly-redis >nul 2>&1
    docker volume rm redis-data >nul 2>&1
    echo ✓ Redis cleaned up
    exit /b 0
)

echo Unknown command: %1%
exit /b 1
