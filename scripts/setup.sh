#!/usr/bin/env bash
set -e

echo "============================================="
echo "CloudPulse Environment Setup"
echo "============================================="

# Ensure directories
mkdir -p data/test_temp docs infrastructure/terraform logs

# Setup virtual environment if not present
if [ ! -d "venv" ]; then
    echo "[1/3] Creating Python virtual environment..."
    python3 -m venv venv || python -m venv venv
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

echo "[2/3] Installing Python dependencies..."
pip install -r backend/requirements.txt

echo "[3/3] Initializing CloudPulse SQLite Database..."
python -c "from backend.app.models.database import init_db; init_db(); print('Database schema ready.')"

echo "Setup completed successfully!"
