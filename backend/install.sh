#!/bin/bash
# Installation script for Book Translation API

set -e  # Exit on any error

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Make sure we're in the backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}=== Book Translation API Installer ===${NC}"
echo

# Check Python version
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python not found. Please install Python 3.8 or newer.${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
echo -e "${GREEN}Using Python version:${NC} $PYTHON_VERSION"

# Create virtual environment
echo -e "\n${BLUE}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists. Skipping creation.${NC}"
fi

# Activate virtual environment
echo -e "\n${BLUE}Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix/MacOS
    source venv/bin/activate
fi
echo -e "${GREEN}Virtual environment activated.${NC}"

# Install dependencies
echo -e "\n${BLUE}Installing dependencies...${NC}"
echo -e "${YELLOW}This may take a few minutes...${NC}"

# First try to uninstall openai to avoid version conflicts
pip uninstall -y openai 2>/dev/null || true

# Install the package in development mode
pip install -e .
echo -e "${GREEN}Dependencies installed.${NC}"

# Create necessary directories
echo -e "\n${BLUE}Creating necessary directories...${NC}"
mkdir -p output
mkdir -p temp_uploads
echo -e "${GREEN}Directories created.${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "\n${BLUE}Creating .env file...${NC}"
    cat > .env << EOL
# OpenAI API Key
OPENAI_API_KEY=

# Server settings
PORT=8000
LOG_LEVEL=INFO
RELOAD=True

# Application settings
USE_BACKGROUND_TASKS=1
MAX_FILE_SIZE=10485760  # 10MB in bytes
MAX_CHAPTERS=100
EOL
    echo -e "${GREEN}.env file created. Please edit it to add your OpenAI API key.${NC}"
    echo -e "${YELLOW}Important: You need to add your OpenAI API key to the .env file.${NC}"
else
    echo -e "\n${YELLOW}.env file already exists. Skipping creation.${NC}"
fi

echo
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Installation completed successfully!${NC}"
echo
echo -e "To start the server, run:${NC}"
echo -e "${BLUE}source venv/bin/activate  # If not already activated${NC}"
echo -e "${BLUE}python -m app.main${NC}"
echo
echo -e "Visit http://localhost:8000/docs to access the API documentation."
echo -e "${GREEN}=====================================${NC}" 