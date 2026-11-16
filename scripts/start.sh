#!/usr/bin/env bash
set -e

echo "============================================="
echo "Starting CloudPulse Platform"
echo "============================================="

# Start backend in background or foreground
echo "[1/2] Starting CloudPulse Flask API on http://localhost:5000..."
python -m backend.app.main &
BACKEND_PID=$!

sleep 2

echo "[2/2] Starting CloudPulse Monitoring Agent daemon..."
python agent/main.py --daemon &
AGENT_PID=$!

echo "CloudPulse is running!"
echo "Backend API: http://localhost:5000/api"
echo "Health:      http://localhost:5000/api/health"
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $AGENT_PID 2>/dev/null" EXIT INT TERM
wait
