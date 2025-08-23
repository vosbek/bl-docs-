@echo off
setlocal enabledelayedexpansion

:: Multi-Agent Jira Card Creator - Windows Startup Script
:: This script provides an easy way to start the application on Windows

title Multi-Agent Jira Card Creator - Starting...

echo ==============================================
echo   Multi-Agent Jira Card Creator
echo   Starting Application...
echo ==============================================
echo.

:: Check if Docker is installed and running
echo [%time%] Checking prerequisites...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running
    echo Please start Docker Desktop
    pause
    exit /b 1
)

echo [SUCCESS] Docker is installed and running

:: Check if .env file exists
if not exist .env (
    echo [ERROR] .env file not found
    echo Please copy .env.template to .env and configure it
    echo Run: copy .env.template .env
    pause
    exit /b 1
)

echo [SUCCESS] Configuration file found

:: Validate basic configuration
echo [%time%] Validating configuration...
findstr /C:"AWS_ACCESS_KEY_ID=" .env >nul
if errorlevel 1 (
    echo [ERROR] AWS_ACCESS_KEY_ID not configured in .env
    echo Please edit .env and add your AWS credentials
    pause
    exit /b 1
)

findstr /C:"REPOSITORIES_PATH=" .env >nul
if errorlevel 1 (
    echo [ERROR] REPOSITORIES_PATH not configured in .env
    echo Please edit .env and set the path to your repositories
    pause
    exit /b 1
)

echo [SUCCESS] Basic configuration validation passed

:: Stop any existing containers
echo [%time%] Stopping existing containers...
docker-compose down --remove-orphans >nul 2>&1

:: Start services
echo [%time%] Building and starting containers...
docker-compose up -d --build
if errorlevel 1 (
    echo [ERROR] Failed to start services
    echo Check the error messages above
    pause
    exit /b 1
)

echo [SUCCESS] Services started successfully

:: Wait for services to become healthy
echo [%time%] Waiting for services to become healthy...
set /a "elapsed=0"
set /a "timeout=300"
set "backend_healthy=false"
set "frontend_healthy=false"

:health_loop
if !elapsed! geq !timeout! (
    echo [ERROR] Services failed to become healthy within !timeout! seconds
    echo Run 'docker-compose logs' to check for errors
    pause
    exit /b 1
)

:: Check backend health
curl -s http://localhost:8000/api/health >nul 2>&1
if not errorlevel 1 (
    if "!backend_healthy!"=="false" (
        echo [SUCCESS] Backend is healthy
        set "backend_healthy=true"
    )
)

:: Check frontend health
curl -s http://localhost:4200 >nul 2>&1
if not errorlevel 1 (
    if "!frontend_healthy!"=="false" (
        echo [SUCCESS] Frontend is healthy
        set "frontend_healthy=true"
    )
)

:: Check if both services are healthy
if "!backend_healthy!"=="true" if "!frontend_healthy!"=="true" goto health_complete

:: Show progress every 30 seconds
set /a "progress=elapsed%%30"
if !progress! equ 0 if !elapsed! gtr 0 (
    echo   Still waiting... (!elapsed!s elapsed)
)

timeout /t 10 /nobreak >nul
set /a "elapsed+=10"
goto health_loop

:health_complete

:: Perform quick system test
echo [%time%] Performing system test...
for /f %%i in ('curl -s http://localhost:8000/api/health') do set "health_response=%%i"
echo !health_response! | findstr "status" >nul
if errorlevel 1 (
    echo [ERROR] Backend API test failed
    echo Response: !health_response!
    pause
    exit /b 1
)

echo [SUCCESS] System test passed

:: Show success message
echo.
echo ==============================================
echo   🚀 Application Started Successfully!
echo ==============================================
echo.
echo Application URLs:
echo   📊 Dashboard:    http://localhost:4200
echo   🔧 Backend API:  http://localhost:8000
echo   📚 API Docs:     http://localhost:8000/docs
echo.
echo Quick Commands:
echo   📋 View logs:    logs.bat
echo   🛑 Stop app:     stop.bat
echo   🔄 Restart:      restart.bat
echo   ❤️ Health check: health-check.bat
echo.
echo Next Steps:
echo   1. Open http://localhost:4200 in your browser
echo   2. Check that all system status indicators are green
echo   3. Create your first task to test the workflow
echo.

:: Open browser automatically
echo Opening dashboard in your default browser...
start http://localhost:4200

echo Press any key to close this window...
pause >nul