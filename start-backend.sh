#!/bin/bash
cd backend
source venv/bin/activate
echo "🚀 Starting Backend Server..."
echo "📖 API Documentation: http://localhost:8000/docs"
python -m app.main
