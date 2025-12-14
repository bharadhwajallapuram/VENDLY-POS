#!/bin/bash
# ===========================================
# VENDLY POS - PRODUCTION DEPLOYMENT SCRIPT
# ===========================================
# Automates the deployment process
# Usage: bash scripts/deploy.sh
#
# This script:
# 1. Validates environment
# 2. Builds Docker images
# 3. Starts all services
# 4. Verifies health
# 5. Creates backups
# ===========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not installed"
        exit 1
    fi
    print_success "Docker installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose not installed"
        exit 1
    fi
    print_success "Docker Compose installed"
    
    # Check .env file
    if [ ! -f ".env" ]; then
        print_error ".env file not found"
        echo "Create .env from .env.production template"
        exit 1
    fi
    print_success ".env file exists"
    
    # Check SSL certificates
    if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
        print_warning "SSL certificates not found in nginx/ssl/"
        print_warning "Generate with: openssl req -x509 -newkey rsa:4096 ..."
    fi
    print_success "Prerequisite checks complete"
}

# Validate environment
validate_environment() {
    print_header "Validating Environment"
    
    if command -v python3 &> /dev/null; then
        python3 scripts/validate_env.py --env .env
        if [ $? -ne 0 ]; then
            print_error "Environment validation failed"
            exit 1
        fi
    else
        print_warning "Python3 not found, skipping env validation"
    fi
}

# Build images
build_images() {
    print_header "Building Docker Images"
    
    docker-compose build --no-cache
    if [ $? -ne 0 ]; then
        print_error "Docker build failed"
        exit 1
    fi
    print_success "Images built successfully"
}

# Start services
start_services() {
    print_header "Starting Services"
    
    # Stop any running containers
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Start services
    docker-compose up -d
    if [ $? -ne 0 ]; then
        print_error "Failed to start services"
        exit 1
    fi
    
    # Wait for services to stabilize
    echo "Waiting 30 seconds for services to stabilize..."
    sleep 30
    
    print_success "Services started"
}

# Verify health
verify_health() {
    print_header "Verifying Health"
    
    # Check container status
    docker-compose ps
    
    # Check backend health
    echo -e "\nChecking backend health..."
    for i in {1..10}; do
        if docker-compose exec -T backend curl -f http://localhost:8000/health 2>/dev/null; then
            print_success "Backend is healthy"
            break
        fi
        if [ $i -eq 10 ]; then
            print_error "Backend health check failed"
            exit 1
        fi
        echo "Attempt $i/10... retrying in 3 seconds"
        sleep 3
    done
    
    # Check database
    echo -e "\nChecking database..."
    if docker-compose exec -T postgres pg_isready -U vendly &>/dev/null; then
        print_success "Database is ready"
    else
        print_error "Database health check failed"
        exit 1
    fi
    
    # Check Redis
    echo -e "\nChecking Redis..."
    if docker-compose exec -T redis redis-cli ping &>/dev/null; then
        print_success "Redis is running"
    else
        print_error "Redis health check failed"
        exit 1
    fi
}

# Setup backups
setup_backups() {
    print_header "Setting Up Backups"
    
    mkdir -p backups
    chmod 700 backups
    
    echo "Creating initial backup..."
    docker-compose exec -T postgres pg_dump -U vendly vendly_db | \
        gzip > backups/initial_backup_$(date +%Y%m%d_%H%M%S).sql.gz
    
    if [ $? -eq 0 ]; then
        print_success "Initial backup created"
    else
        print_warning "Initial backup creation failed (but services are running)"
    fi
}

# Run migrations
run_migrations() {
    print_header "Running Database Migrations"
    
    docker-compose exec -T backend alembic upgrade head
    if [ $? -eq 0 ]; then
        print_success "Migrations completed"
    else
        print_error "Migrations failed"
        exit 1
    fi
}

# Display summary
display_summary() {
    print_header "Deployment Complete!"
    
    echo -e "${GREEN}✓ All services deployed successfully${NC}\n"
    
    echo -e "${BLUE}Access Points:${NC}"
    echo "  Frontend:  https://yourdomain.com"
    echo "  API Docs:  https://yourdomain.com/docs"
    echo "  Grafana:   https://yourdomain.com/grafana"
    echo "  Health:    https://yourdomain.com/health\n"
    
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  View logs:       docker-compose logs -f backend"
    echo "  Container stats: docker stats"
    echo "  Check status:    docker-compose ps"
    echo "  Stop services:   docker-compose down"
    echo "  Restart:         docker-compose restart\n"
    
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Access https://yourdomain.com/grafana"
    echo "  2. Change Grafana admin password"
    echo "  3. Change admin user password via UI"
    echo "  4. Enable 2FA for admin accounts"
    echo "  5. Monitor logs: docker-compose logs -f\n"
    
    echo -e "${BLUE}Documentation:${NC}"
    echo "  Deployment Guide: docs/PRODUCTION_DEPLOYMENT.md"
    echo "  API Docs:         https://yourdomain.com/docs"
    echo "  GitHub:           https://github.com/yourorg/vendly\n"
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════╗"
    echo "║  VENDLY POS - PRODUCTION DEPLOYMENT  ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Run deployment steps
    check_prerequisites
    validate_environment
    build_images
    start_services
    verify_health
    run_migrations
    setup_backups
    display_summary
    
    exit 0
}

# Run main function
main
