@echo off
setlocal enabledelayedexpansion

:: Multi-Agent Jira Card Creator - Windows Health Check Script

title Multi-Agent Jira Card Creator - Health Check

echo ==============================================
echo   Multi-Agent Jira Card Creator
echo   Health Check Report
echo   %date% %time%
echo ==============================================
echo.

set "OVERALL_HEALTH=true"
set "ISSUES_COUNT=0"

:: Check Docker
echo [CHECK] Docker environment
docker --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL]  ✗ Docker is not installed or not accessible
    set "OVERALL_HEALTH=false"
    set /a "ISSUES_COUNT+=1"
) else (
    echo [PASS]  ✓ Docker is installed
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [FAIL]  ✗ Docker is not running
    set "OVERALL_HEALTH=false"
    set /a "ISSUES_COUNT+=1"
) else (
    echo [PASS]  ✓ Docker is running
)

:: Check containers
echo [CHECK] Container status

docker-compose ps -q >temp_containers.txt 2>&1
set "containers_found=false"
for /f %%i in (temp_containers.txt) do (
    if not "%%i"=="" set "containers_found=true"
)

if "!containers_found!"=="false" (
    echo [FAIL]  ✗ No containers are running
    set "OVERALL_HEALTH=false"
    set /a "ISSUES_COUNT+=1"
) else (
    :: Check specific containers
    set "backend_found=false"
    set "frontend_found=false"
    
    for /f %%i in (temp_containers.txt) do (
        for /f "tokens=*" %%j in ('docker inspect --format "{{.Name}}" %%i') do (
            set "container_name=%%j"
            set "container_name=!container_name:/=!"
            
            echo !container_name! | findstr /i "backend" >nul
            if not errorlevel 1 (
                for /f %%k in ('docker inspect --format "{{.State.Status}}" %%i') do (
                    if "%%k"=="running" (
                        echo [PASS]  ✓ Backend container is running
                        set "backend_found=true"
                    ) else (
                        echo [FAIL]  ✗ Backend container is not running ^(status: %%k^)
                        set "OVERALL_HEALTH=false"
                        set /a "ISSUES_COUNT+=1"
                    )
                )
            )
            
            echo !container_name! | findstr /i "frontend" >nul
            if not errorlevel 1 (
                for /f %%k in ('docker inspect --format "{{.State.Status}}" %%i') do (
                    if "%%k"=="running" (
                        echo [PASS]  ✓ Frontend container is running
                        set "frontend_found=true"
                    ) else (
                        echo [FAIL]  ✗ Frontend container is not running ^(status: %%k^)
                        set "OVERALL_HEALTH=false"
                        set /a "ISSUES_COUNT+=1"
                    )
                )
            )
        )
    )
    
    if "!backend_found!"=="false" (
        echo [FAIL]  ✗ Backend container not detected
        set "OVERALL_HEALTH=false"
        set /a "ISSUES_COUNT+=1"
    )
    
    if "!frontend_found!"=="false" (
        echo [FAIL]  ✗ Frontend container not detected
        set "OVERALL_HEALTH=false"
        set /a "ISSUES_COUNT+=1"
    )
)

del temp_containers.txt >nul 2>&1

:: Check API endpoints
echo [CHECK] API endpoint health

curl -s --max-time 10 http://localhost:8000/api/health >temp_health.txt 2>&1
findstr "status" temp_health.txt >nul
if errorlevel 1 (
    echo [FAIL]  ✗ Backend API health endpoint not responding
    set "OVERALL_HEALTH=false"
    set /a "ISSUES_COUNT+=1"
) else (
    findstr "healthy" temp_health.txt >nul
    if errorlevel 1 (
        echo [WARN]  ⚠ Backend API responding but status may not be healthy
    ) else (
        echo [PASS]  ✓ Backend API health endpoint responding ^(status: healthy^)
    )
)
del temp_health.txt >nul 2>&1

curl -s --max-time 10 http://localhost:8000/api/repositories >temp_repos.txt 2>&1
findstr "repositories" temp_repos.txt >nul
if errorlevel 1 (
    echo [FAIL]  ✗ Repository scanner API not responding
    set "OVERALL_HEALTH=false"
    set /a "ISSUES_COUNT+=1"
) else (
    echo [PASS]  ✓ Repository scanner API responding
)
del temp_repos.txt >nul 2>&1

:: Check frontend
echo [CHECK] Frontend accessibility

curl -s --max-time 10 -I http://localhost:4200 >temp_frontend.txt 2>&1
findstr "200 OK" temp_frontend.txt >nul
if errorlevel 1 (
    echo [FAIL]  ✗ Frontend is not accessible
    set "OVERALL_HEALTH=false"
    set /a "ISSUES_COUNT+=1"
) else (
    echo [PASS]  ✓ Frontend is accessible
)
del temp_frontend.txt >nul 2>&1

:: Check configuration
echo [CHECK] Configuration validation

if exist .env (
    echo [PASS]  ✓ .env configuration file exists
    
    findstr /C:"AWS_ACCESS_KEY_ID=" .env >nul
    if errorlevel 1 (
        echo [FAIL]  ✗ AWS credentials not configured
        set "OVERALL_HEALTH=false"
        set /a "ISSUES_COUNT+=1"
    ) else (
        echo [PASS]  ✓ AWS credentials configured
    )
    
    findstr /C:"JIRA_URL=" .env >nul
    if errorlevel 1 (
        echo [WARN]  ⚠ Jira URL not configured
    ) else (
        echo [PASS]  ✓ Jira URL configured
    )
    
) else (
    echo [FAIL]  ✗ .env configuration file not found
    set "OVERALL_HEALTH=false"
    set /a "ISSUES_COUNT+=1"
)

:: Generate report
echo.
echo ==============================================

if "!OVERALL_HEALTH!"=="true" (
    echo   ✅ OVERALL HEALTH: GOOD
    echo ==============================================
    echo.
    echo All critical systems are functioning normally.
    echo.
    echo Application URLs:
    echo   📊 Dashboard:   http://localhost:4200
    echo   🔧 Backend API: http://localhost:8000
    echo   📚 API Docs:    http://localhost:8000/docs
    echo.
) else (
    echo   ❌ OVERALL HEALTH: ISSUES DETECTED
    echo ==============================================
    echo.
    echo Found !ISSUES_COUNT! issue^(s^)
    echo.
    echo Recommendations:
    echo   1. Check logs: logs.bat
    echo   2. Restart application: restart.bat
    echo   3. Review configuration: type .env
    echo.
)

echo Press any key to close this window...
pause >nul

if "!OVERALL_HEALTH!"=="true" (
    exit /b 0
) else (
    exit /b 1
)