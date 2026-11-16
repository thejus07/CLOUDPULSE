#!/usr/bin/env bash
set -e

echo "============================================="
echo "Running CloudPulse Test Suite"
echo "============================================="

python -m pytest backend/tests -v --durations=10

echo ""
echo "Running End-to-End Failure Simulation Scenario Checks..."
python scripts/simulate_scenario.py --scenario all

echo ""
echo "All CloudPulse tests and failure simulations verified!"
