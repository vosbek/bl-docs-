@echo off
setlocal enabledelayedexpansion

:: Multi-Agent Jira Card Creator - Windows Logs Viewer

title Multi-Agent Jira Card Creator - Logs

echo ==============================================
echo   Multi-Agent Jira Card Creator - Logs
echo ==============================================
echo.

:: Check if services are running
docker-compose ps -q >temp_check.txt 2>&1
set "containers_running=false"
for /f %%i in (temp_check.txt) do (
    if not "%%i"=="" set "containers_running=true"
)
del temp_check.txt

if "!containers_running!"=="false" (
    echo [ERROR] No services are running.
    echo Start the application first with: start.bat
    pause
    exit /b 1
)

:: Parse command line arguments
set "SERVICE=all"
set "TAIL_LINES=100"
set "FOLLOW="
set "ERRORS_ONLY=false"

if "%1"=="--help" goto show_help
if "%1"=="-h" goto show_help
if "%1"=="backend" set "SERVICE=backend"
if "%1"=="frontend" set "SERVICE=frontend"
if "%1"=="--follow" set "FOLLOW=-f"
if "%1"=="-f" set "FOLLOW=-f"
if "%1"=="--errors" set "ERRORS_ONLY=true"

:: Show log information
if "%SERVICE%"=="all" (
    echo Showing logs for: All services
) else (
    echo Showing logs for: %SERVICE%
)

if "%FOLLOW%"=="-f" (
    echo Mode: Following ^(real-time^)
    echo Press Ctrl+C to stop following logs
) else (
    echo Mode: Last %TAIL_LINES% lines
)

if "%ERRORS_ONLY%"=="true" echo Filter: Errors only

echo.

:: Build and execute docker-compose logs command
set "LOGS_CMD=docker-compose logs"

if not "%FOLLOW%"=="" set "LOGS_CMD=!LOGS_CMD! !FOLLOW!"
if not "%TAIL_LINES%"=="" set "LOGS_CMD=!LOGS_CMD! --tail=%TAIL_LINES%"
if not "%SERVICE%"=="all" set "LOGS_CMD=!LOGS_CMD! %SERVICE%"

if "%ERRORS_ONLY%"=="true" (
    !LOGS_CMD! 2>&1 | findstr /i "error exception fail critical"
) else (
    !LOGS_CMD!
)

goto end

:show_help
echo Usage: %0 [OPTIONS] [SERVICE]
echo.
echo OPTIONS:
echo   -f, --follow     Follow log output ^(like tail -f^)
echo   --errors         Show only ERROR level logs
echo   -h, --help       Show this help message
echo.
echo SERVICES:
echo   backend          Show backend API logs only
echo   frontend         Show frontend logs only
echo   all              Show all service logs ^(default^)
echo.
echo EXAMPLES:
echo   %0                    # Show last 100 lines of all logs
echo   %0 -f                 # Follow all logs in real-time
echo   %0 backend           # Show backend logs only
echo   %0 --errors          # Show error logs only
echo.
pause
exit /b 0

:end
if "%FOLLOW%"=="-f" goto end_no_pause

echo.
echo Useful commands:
echo   logs.bat -f              # Follow logs in real-time
echo   logs.bat --errors        # Show only errors
echo   logs.bat backend         # Show backend logs only
echo   health-check.bat         # Run health check
echo.
echo Press any key to close this window...
pause >nul

:end_no_pause