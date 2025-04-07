#!/bin/bash
# Setup script for the Book Translation API backend

# Make sure we're in the backend directory
cd "$(dirname "$0")" || exit

# Check if a virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p output
mkdir -p test_output

# Set environment variables
export OPENAI_API_KEY="sk-test-key-for-pytest"
export PYTHONPATH=$(pwd)

echo "Setup complete!"

# Ask if the user wants to run tests
read -p "Do you want to run tests now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python run_tests.py
fi

# Ask if the user wants to start the server
read -p "Do you want to start the server? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    uvicorn app.main:app --reload
fi 