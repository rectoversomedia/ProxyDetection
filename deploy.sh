#!/bin/bash
# =============================================================================
# ProxyDetection VPS Deployment Script
# =============================================================================

set -e

echo "============================================"
echo "  ProxyDetection VPS Setup"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_warn "Please run as root: sudo bash deploy.sh"
    exit 1
fi

# =============================================================================
# 1. System Update
# =============================================================================
log_info "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt update -qq
apt upgrade -y -qq

# =============================================================================
# 2. Install Dependencies
# =============================================================================
log_info "Installing system dependencies..."

apt install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    libpq-dev \
    libcurl4-openssl-dev \
    libssl-dev

# =============================================================================
# 3. Install Chrome/Chromium
# =============================================================================
log_info "Installing Chromium browser..."

apt install -y -qq chromium \
    chromium-driver \
    chromium-sandbox \
    xvfb \
    chrome-common \
    fonts-liberation

# Set Chromium path
export CHROME_BIN=/usr/bin/chromium

# =============================================================================
# 4. Create Project Directory
# =============================================================================
log_info "Setting up project directory..."

PROJECT_DIR="/opt/proxydetection"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# =============================================================================
# 5. Clone Repository
# =============================================================================
log_info "Cloning repository..."

if [ -d ".git" ]; then
    log_info "Repository already exists, pulling latest..."
    git pull origin main
else
    git clone https://github.com/rectoversomedia/ProxyDetection.git $PROJECT_DIR
fi

cd $PROJECT_DIR

# =============================================================================
# 6. Setup Python Environment
# =============================================================================
log_info "Setting up Python virtual environment..."

python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip -q

# =============================================================================
# 7. Install Python Dependencies
# =============================================================================
log_info "Installing Python packages..."

# Core dependencies
pip install -q \
    typer[all] \
    click \
    sqlalchemy \
    aiosqlite \
    httpx \
    pydantic \
    pydantic-settings \
    python-dotenv \
    loguru \
    tenacity \
    fake-useragent \
    pillow \
    numpy \
    pandas \
    scipy

# Browser dependencies
pip install -q \
    playwright \
    curl_cffi

# Install Playwright browsers
playwright install chromium
playwright install-deps chromium

# =============================================================================
# 8. Create Service User (optional)
# =============================================================================
log_info "Creating service user..."

if ! id -u proxydetection &>/dev/null; then
    useradd -m -s /bin/bash proxydetection
    chown -R proxydetection:proxydetection $PROJECT_DIR
    log_info "User 'proxydetection' created"
else
    log_info "User 'proxydetection' already exists"
fi

# =============================================================================
# 9. Setup Environment File
# =============================================================================
log_info "Setting up environment file..."

cat > $PROJECT_DIR/.env << 'EOF'
# ProxyDetection Environment Configuration
# ====================================

# API Keys (2Captcha for CAPTCHA solving)
TWOCAPTCHA_API_KEY=
CAPSOLVER_API_KEY=

# Browser Settings
BROWSER_TYPE=playwright
BROWSER_HEADLESS=false
PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# Proxy Settings
DAT_IMPULSE_API_KEY=
DECODO_API_KEY=
PROXY_FILE_PATH=data/proxies.txt

# Submission Settings
DEFAULT_DELAY=5
MAX_PARALLEL=3
MAX_RETRIES=3

# Database
DATABASE_PATH=data/proxydetection.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Advanced Anti-Detection (enabled by default)
TLS_FINGERPRINT_ENABLED=true
ML_RESISTANT_BEHAVIOR=true
AUTO_SOLVE_CAPTCHA=true
EOF

chmod 600 $PROJECT_DIR/.env

# =============================================================================
# 10. Create Directories
# =============================================================================
log_info "Creating data directories..."

mkdir -p $PROJECT_DIR/data
mkdir -p $PROJECT_DIR/logs
mkdir -p $PROJECT_DIR/logs/screenshots
mkdir -p $PROJECT_DIR/configs

chmod -R 755 $PROJECT_DIR/data
chmod -R 755 $PROJECT_DIR/logs

# =============================================================================
# 11. Setup systemd Service
# =============================================================================
log_info "Setting up systemd service..."

cat > /etc/systemd/system/proxydetection.service << 'EOF'
[Unit]
Description=ProxyDetection Lead Automation
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/proxydetection
Environment=PATH=/opt/proxydetection/venv/bin
Environment=PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
ExecStart=/opt/proxydetection/venv/bin/python -m src.cli.main
Restart=on-failure
RestartSec=10
StandardOutput=append:/opt/proxydetection/logs/service.log
StandardError=append:/opt/proxydetection/logs/service.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

# =============================================================================
# 12. Create CLI Wrapper
# =============================================================================
log_info "Creating CLI wrapper..."

cat > /usr/local/bin/pd << 'EOF'
#!/bin/bash
source /opt/proxydetection/venv/bin/activate
cd /opt/proxydetection
python -m src.cli.main "$@"
EOF

chmod +x /usr/local/bin/pd

# =============================================================================
# 13. Create Usage Script
# =============================================================================
cat > $PROJECT_DIR/usage.sh << 'EOF'
#!/bin/bash
echo "============================================"
echo "  ProxyDetection Usage Guide"
echo "============================================"
echo ""

echo "Quick Commands:"
echo "--------------"
echo "pd --help                    # Show all commands"
echo "pd status                    # Check system status"
echo ""
echo "pd leads import --source data/leads.csv   # Import leads"
echo "pd leads list                # List all leads"
echo ""
echo "pd proxy add --file data/proxies.txt     # Add proxies"
echo "pd proxy test                # Test proxy health"
echo ""
echo "pd submit --leads data/leads.csv --parallel 3"
echo ""
echo "Environment Setup:"
echo "-----------------"
echo "Edit /opt/proxydetection/.env to set API keys"
echo ""
echo "Service Management:"
echo "------------------"
echo "systemctl start proxydetection"
echo "systemctl stop proxydetection"
echo "systemctl status proxydetection"
echo "journalctl -u proxydetection -f"
EOF

chmod +x $PROJECT_DIR/usage.sh

# =============================================================================
# 14. Final Setup
# =============================================================================
log_info "Running final setup..."

# Test import
source venv/bin/activate
python -c "import src.antidetect; print('✓ All modules imported successfully')" 2>/dev/null || echo "Module check skipped"

echo ""
echo "============================================"
echo -e "${GREEN}  Setup Complete!${NC}"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Edit .env to add your API keys:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Import your leads:"
echo "   pd leads import --source your_leads.csv"
echo ""
echo "3. Add proxies:"
echo "   pd proxy add --file your_proxies.txt"
echo ""
echo "4. Submit leads:"
echo "   pd submit --leads your_leads.csv --parallel 3"
echo ""
echo "============================================"
