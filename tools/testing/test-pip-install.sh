#!/bin/bash
set -e

echo "🐳 Testing pip installation in clean Docker environment..."

# Quick test to verify pip installation works
docker run --rm -v $(pwd):/app -w /app python:3.13-slim bash -c "
    echo '📦 Installing with pip...'
    python -m pip install --upgrade pip
    pip install -e .[dev]
    echo ''
    echo '✅ Testing pytest availability:'
    python -c 'import pytest; print(f\"pytest version: {pytest.__version__}\")'
    echo ''
    echo '✅ Testing imports:'
    python -c 'import sys; sys.path.insert(0, \"src\"); from file_manager import FileManager; print(\"FileManager import successful\")'
    echo ''
    echo '🎉 All checks passed!'
"