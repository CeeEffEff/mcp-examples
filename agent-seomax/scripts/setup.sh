#!/bin/bash
# Development Environment Setup Script for agent-seomax
# This script creates a project-specific Python virtual environment and installs all dependencies

set -e  # Exit on error

echo "========================================="
echo "GCP Digital Twin Agent Setup"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    echo -e "${RED}Error: Python 3.9 or higher is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Warning: venv directory already exists${NC}"
    read -p "Remove existing venv and create new one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}✓ New virtual environment created${NC}"
    else
        echo "Using existing venv"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip wheel setuptools
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
echo -e "${GREEN}✓ All dependencies installed${NC}"
echo ""

# Create .env from template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env and add your configuration${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi
echo ""

# Run basic import test
echo "Verifying installation..."
python3 -c "from ingestion_pipeline import graph_queries; print('Import successful')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Package imports working correctly${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Package imports failed (this is expected if GCP credentials not configured)${NC}"
fi
echo ""

echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo -e "   ${GREEN}source venv/bin/activate${NC}"
echo ""
echo "2. Configure your .env file with GCP credentials"
echo ""
echo "3. Run tests:"
echo -e "   ${GREEN}pytest tests/ -v${NC}"
echo ""
echo "4. Run specific test suite:"
echo -e "   ${GREEN}pytest tests/test_graph_queries.py -v --cov${NC}"
echo ""
echo "To deactivate the virtual environment later:"
echo -e "   ${GREEN}deactivate${NC}"
echo ""
