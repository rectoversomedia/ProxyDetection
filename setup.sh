#!/bin/bash

# =============================================================================
# ProxyDetection Setup Script
# =============================================================================

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   ProxyDetection - Lead Submission Automation Setup       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
step() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    error "Python not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check if version >= 3.10
if [[ $(echo "$PYTHON_VERSION >= 3.10" | bc -l) != 1 ]]; then
    warn "Python 3.10+ recommended. Found $PYTHON_VERSION"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    step "Virtual environment created"
else
    warn "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
step "pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -e ".[dev]" 2>&1 | tail -5
step "Dependencies installed"

# Install Playwright (optional but recommended)
echo ""
echo "Installing Playwright browser..."
pip install playwright > /dev/null 2>&1
python -m playwright install chromium 2>&1 | tail -3
step "Playwright installed"

# Initialize database
echo ""
echo "Initializing database..."
pd init 2>&1 || warn "Some init steps may have failed"

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    step ".env file created"
    warn "Please edit .env and add your API keys"
fi

# Summary
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   Setup Complete!                                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add API keys:"
echo "     - DAT_IMPULSE_API_KEY"
echo "     - DECODO_API_KEY (optional)"
echo ""
echo "  2. Add proxies:"
echo "     pd proxy add --provider dat_impulse"
echo ""
echo "  3. Create a campaign:"
echo "     pd campaign create \\"
echo "       --name 'My Campaign' \\"
echo "       --sheet 'https://docs.google.com/spreadsheets/d/xxx/edit' \\"
echo "       --target 'https://example.com/form'"
echo ""
echo "  4. Run the campaign:"
echo "     pd campaign run my_campaign"
echo ""
echo "For help:"
echo "  pd --help"
echo "  pd campaign --help"
echo ""
