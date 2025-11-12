#!/bin/bash
# Startup script for Zabbix SNMP Template Generator Web Interface

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   Zabbix SNMP Template Generator - Web Interface         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✓ Docker and Docker Compose detected"
    echo ""
    echo "Starting with Docker..."
    echo ""

    # Build and start containers
    docker-compose up --build -d

    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                    ✓ SUCCESS!                            ║"
    echo "╠═══════════════════════════════════════════════════════════╣"
    echo "║  Web Interface: http://localhost:5000                    ║"
    echo "║  API Health:    http://localhost:5000/api/health         ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Commands:"
    echo "  View logs:    docker-compose logs -f"
    echo "  Stop:         docker-compose down"
    echo "  Restart:      docker-compose restart"
    echo ""

else
    echo "⚠ Docker not detected. Starting in development mode..."
    echo ""

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 not found. Please install Python 3.9 or higher."
        exit 1
    fi

    echo "✓ Python detected: $(python3 --version)"

    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js not found. Please install Node.js 18 or higher."
        exit 1
    fi

    echo "✓ Node.js detected: $(node --version)"
    echo ""

    # Install Python dependencies
    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt

    # Install frontend dependencies
    echo "Installing frontend dependencies..."
    cd frontend
    npm install --silent
    cd ..

    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║              Starting Development Servers...             ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""

    # Start backend in background
    echo "Starting Flask API (backend)..."
    python3 api.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"

    # Wait for backend to start
    sleep 3

    # Start frontend in foreground
    echo "Starting React dev server (frontend)..."
    echo ""
    cd frontend
    npm run dev

    # Cleanup on exit
    kill $BACKEND_PID 2>/dev/null || true
fi
