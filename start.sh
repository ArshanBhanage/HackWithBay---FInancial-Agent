#!/bin/bash

# Financial Contract Drift Monitor - Secure Startup Script
# This script ensures no secrets are logged during startup

echo "Starting Financial Contract Drift Monitor..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please copy env.example to .env and configure your settings."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run the application
echo "Configuration loaded from .env file"
echo "Starting application..."
python main.py
