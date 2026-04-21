#!/bin/bash
# Quick start script for Saulo

set -e

echo "🦞 Starting Saulo v4..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies if needed
if ! pip show fastapi > /dev/null 2>&1; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "Creating .env from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

# Check Ollama
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama not running. Please start it first:"
    echo "    ollama serve"
    exit 1
fi

echo "✅ Starting server on http://localhost:8090"
uvicorn main:app --host 0.0.0.0 --port 8090
