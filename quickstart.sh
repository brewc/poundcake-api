#!/bin/bash
# Quick start script for PoundCake API

set -e

echo "Starting PoundCake API Setup..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "SUCCESS: Docker and Docker Compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "SUCCESS: Created .env file"
else
    echo "INFO: .env file already exists"
fi
echo ""

# Build Docker images
echo "Building Docker images..."
docker-compose build --no-cache

echo ""
# Start Docker services
echo "Starting Docker services..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 15

# Check service health
echo ""
echo "Checking service health..."

# Check API
if curl -s http://localhost:8000/api/v1/health/live > /dev/null 2>&1; then
    echo "SUCCESS: API is running"
else
    echo "WARNING: API is not responding"
fi

# Check Flower
if curl -s http://localhost:5555 > /dev/null 2>&1; then
    echo "SUCCESS: Flower dashboard is running"
else
    echo "WARNING: Flower dashboard is not responding"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Available services:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Flower Dashboard: http://localhost:5555"
echo "   - MariaDB: localhost:3306"
echo "   - Redis: localhost:6379"
echo ""
echo "Test the API with:"
echo "   curl http://localhost:8000/api/v1/health"
echo ""
echo "View logs with:"
echo "   docker-compose logs -f"
echo ""
echo "Stop services with:"
echo "   docker-compose down"
echo ""
