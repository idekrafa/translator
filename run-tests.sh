#!/bin/bash
echo "🧪 Running Backend Tests..."
cd backend
source venv/bin/activate
python run_tests.py "$@"
