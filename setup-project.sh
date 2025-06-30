#!/bin/bash

# Book Translator Project Setup Script
# This script sets up the entire project with updated dependencies and configuration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Book Translator Project Setup${NC}"
echo "================================="

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo -e "\n${BLUE}🔍 Checking required tools...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is required but not installed${NC}"
    exit 1
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js ${NODE_VERSION} found${NC}"
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is required but not installed${NC}"
    exit 1
else
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm ${NPM_VERSION} found${NC}"
fi

# Setup Backend
echo -e "\n${BLUE}🐍 Setting up Backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p output
mkdir -p temp_uploads

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file template...${NC}"
    cat > .env << EOL
# OpenAI API Key (REQUIRED - Get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=

# Server Configuration
PORT=8000
LOG_LEVEL=INFO
RELOAD=False

# Application Settings
USE_BACKGROUND_TASKS=1
MAX_FILE_SIZE=10485760  # 10MB in bytes
MAX_CHAPTERS=100
OUTPUT_DIR=output
EOL
    echo -e "${YELLOW}⚠️  Please edit backend/.env and add your OpenAI API key${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

echo -e "${GREEN}✅ Backend setup complete${NC}"

# Setup Frontend
echo -e "\n${BLUE}⚛️  Setting up Frontend...${NC}"
cd ../frontend

# Remove old node_modules if it exists (to avoid conflicts)
if [ -d "node_modules" ]; then
    echo -e "${YELLOW}Removing old node_modules...${NC}"
    rm -rf node_modules
fi

# Install dependencies
echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
npm install

echo -e "${GREEN}✅ Frontend setup complete${NC}"

# Create development scripts
echo -e "\n${BLUE}📝 Creating development scripts...${NC}"
cd ..

# Backend dev script
cat > start-backend.sh << 'EOL'
#!/bin/bash
cd backend
source venv/bin/activate
echo "🚀 Starting Backend Server..."
echo "📖 API Documentation: http://localhost:8000/docs"
python -m app.main
EOL
chmod +x start-backend.sh

# Frontend dev script
cat > start-frontend.sh << 'EOL'
#!/bin/bash
cd frontend
echo "🚀 Starting Frontend Development Server..."
echo "🌐 Frontend URL: http://localhost:3000"
npm run dev
EOL
chmod +x start-frontend.sh

# Combined dev script
cat > start-dev.sh << 'EOL'
#!/bin/bash
echo "🚀 Starting Book Translator in Development Mode..."
echo ""
echo "This will start both backend and frontend servers."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping all servers..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM

# Start backend in background
cd backend
source venv/bin/activate
python -m app.main &
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Start frontend in background
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
EOL
chmod +x start-dev.sh

# Test runner script
cat > run-tests.sh << 'EOL'
#!/bin/bash
echo "🧪 Running Backend Tests..."
cd backend
source venv/bin/activate
python run_tests.py "$@"
EOL
chmod +x run-tests.sh

echo -e "${GREEN}✅ Development scripts created${NC}"

# Final instructions
echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
echo "=================="
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo -e "1. ${YELLOW}Add your OpenAI API key:${NC}"
echo "   Edit backend/.env and add your OpenAI API key"
echo ""
echo -e "2. ${YELLOW}Start development:${NC}"
echo "   ./start-dev.sh    # Start both backend and frontend"
echo "   ./start-backend.sh  # Start only backend"
echo "   ./start-frontend.sh # Start only frontend"
echo ""
echo -e "3. ${YELLOW}Run tests:${NC}"
echo "   ./run-tests.sh    # Run all tests"
echo "   ./run-tests.sh --unit    # Run only unit tests"
echo ""
echo -e "4. ${YELLOW}Access the application:${NC}"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo -e "5. ${YELLOW}Deploy with Docker:${NC}"
echo "   docker-compose up -d"
echo ""
echo -e "${BLUE}📚 For more information, see the README.md files${NC}" 