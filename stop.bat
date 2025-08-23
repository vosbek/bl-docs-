@echo off
setlocal

:: Multi-Agent Jira Card Creator - Windows Stop Script

title Multi-Agent Jira Card Creator - Stopping...

echo ==============================================
echo   Multi-Agent Jira Card Creator
echo   Stopping Application...
echo ==============================================
echo.

echo [%time%] Stopping services gracefully...

:: Stop services with timeout (60 seconds)
timeout /t 60 /nobreak >nul & docker-compose down --remove-orphans
if errorlevel 1 (
    echo [ERROR] Graceful stop failed, forcing shutdown...
    docker-compose kill
    docker-compose down --remove-orphans
    echo [SUCCESS] Services force stopped
) else (
    echo [SUCCESS] Services stopped successfully
)

:: Check if containers are still running
docker-compose ps -q >temp_check.txt 2>&1
for /f %%i in (temp_check.txt) do (
    if not "%%i"=="" (
        echo [ERROR] Some containers are still running:
        docker-compose ps
        del temp_check.txt
        pause
        exit /b 1
    )
)
del temp_check.txt

echo [SUCCESS] All services stopped

:: Optional cleanup if --clean parameter is passed
if "%1"=="--clean" (
    echo [%time%] Cleaning up containers and networks...
    docker system prune -f --volumes
    echo [SUCCESS] Cleanup completed
)

echo.
echo ==============================================
echo   🛑 Application Stopped Successfully!
echo ==============================================
echo.
echo To start again, run:
echo   start.bat
echo.
echo Press any key to close this window...
pause >nul