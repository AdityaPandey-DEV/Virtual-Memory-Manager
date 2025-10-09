@echo off
REM Virtual Memory Manager Deployment Script for Windows
REM This script handles deployment of the VMM system

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_NAME=vmm
set COMPOSE_FILE=docker-compose.yml
set PROD_COMPOSE_FILE=docker-compose.prod.yml
set ENV_FILE=.env

REM Functions
:log_info
echo [INFO] %~1
goto :eof

:log_success
echo [SUCCESS] %~1
goto :eof

:log_warning
echo [WARNING] %~1
goto :eof

:log_error
echo [ERROR] %~1
goto :eof

REM Check if Docker is installed
:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Docker is not installed. Please install Docker first."
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Docker Compose is not installed. Please install Docker Compose first."
    exit /b 1
)

call :log_success "Docker and Docker Compose are installed"
goto :eof

REM Check if environment file exists
:check_env
if not exist "%ENV_FILE%" (
    call :log_warning "Environment file %ENV_FILE% not found"
    if exist "env.example" (
        call :log_info "Copying env.example to %ENV_FILE%"
        copy env.example %ENV_FILE%
        call :log_warning "Please edit %ENV_FILE% with your configuration before continuing"
    ) else (
        call :log_error "No environment file found. Please create %ENV_FILE%"
        exit /b 1
    )
) else (
    call :log_success "Environment file found"
)
goto :eof

REM Deploy development
:deploy_dev
call :log_info "Deploying in development mode..."

REM Stop existing containers
docker-compose -f %COMPOSE_FILE% down 2>nul

REM Build and start services
docker-compose -f %COMPOSE_FILE% up --build -d

call :log_success "Development deployment completed"
call :log_info "Services available at:"
call :log_info "  Frontend: http://localhost:3000"
call :log_info "  Backend: http://localhost:8080"
call :log_info "  AI Predictor: http://localhost:5000"
goto :eof

REM Deploy production
:deploy_prod
call :log_info "Deploying in production mode..."

REM Stop existing containers
docker-compose -f %PROD_COMPOSE_FILE% down 2>nul

REM Create necessary directories
if not exist logs mkdir logs
if not exist nginx\ssl mkdir nginx\ssl

REM Build and start services
docker-compose -f %PROD_COMPOSE_FILE% up --build -d

call :log_success "Production deployment completed"
call :log_info "Services available at:"
call :log_info "  Frontend: http://localhost:80"
call :log_info "  Backend API: http://localhost:80/api/"
call :log_info "  AI Predictor: http://localhost:80/ai/"
goto :eof

REM Stop services
:stop_services
call :log_info "Stopping all services..."

REM Stop development services
docker-compose -f %COMPOSE_FILE% down 2>nul

REM Stop production services
docker-compose -f %PROD_COMPOSE_FILE% down 2>nul

call :log_success "All services stopped"
goto :eof

REM Show logs
:show_logs
if "%2"=="" (
    call :log_info "Showing logs for all services..."
    docker-compose -f %COMPOSE_FILE% logs -f
) else (
    call :log_info "Showing logs for %2..."
    docker-compose -f %COMPOSE_FILE% logs -f %2
)
goto :eof

REM Health check
:health_check
call :log_info "Performing health checks..."

REM Check if services are running
docker-compose -f %COMPOSE_FILE% ps | findstr "Up" >nul
if errorlevel 1 (
    call :log_error "No services are running"
    goto :eof
)

call :log_success "Services are running"

REM Check individual services
curl -s http://localhost:8080/metrics >nul 2>&1
if errorlevel 1 (
    call :log_warning "Backend health check failed"
) else (
    call :log_success "Backend is healthy"
)

curl -s http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    call :log_warning "AI Predictor health check failed"
) else (
    call :log_success "AI Predictor is healthy"
)

curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    call :log_warning "Frontend health check failed"
) else (
    call :log_success "Frontend is healthy"
)
goto :eof

REM Clean up
:cleanup
call :log_info "Cleaning up..."

REM Remove containers
docker-compose -f %COMPOSE_FILE% down --volumes --remove-orphans 2>nul
docker-compose -f %PROD_COMPOSE_FILE% down --volumes --remove-orphans 2>nul

REM Remove images
docker image prune -f

call :log_success "Cleanup completed"
goto :eof

REM Main script
if "%1"=="deploy" goto deploy
if "%1"=="deploy-prod" goto deploy_prod
if "%1"=="stop" goto stop_services
if "%1"=="logs" goto show_logs
if "%1"=="health" goto health_check
if "%1"=="cleanup" goto cleanup
if "%1"=="help" goto help
if "%1"=="-h" goto help
if "%1"=="--help" goto help
if "%1"=="" goto deploy

:deploy
call :check_docker
if errorlevel 1 exit /b 1
call :check_env
if errorlevel 1 exit /b 1
call :deploy_dev
goto :eof

:deploy_prod
call :check_docker
if errorlevel 1 exit /b 1
call :check_env
if errorlevel 1 exit /b 1
call :deploy_prod
goto :eof

:stop_services
call :stop_services
goto :eof

:show_logs
call :show_logs %2
goto :eof

:health_check
call :health_check
goto :eof

:cleanup
call :cleanup
goto :eof

:help
echo Usage: %0 [command]
echo.
echo Commands:
echo   deploy      Deploy in development mode (default)
echo   deploy-prod Deploy in production mode
echo   stop        Stop all services
echo   logs [service] Show logs (optionally for specific service)
echo   health      Perform health checks
echo   cleanup     Clean up containers and images
echo   help        Show this help message
goto :eof