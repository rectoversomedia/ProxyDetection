# Proxy Detection - Lead Submission Automation

Automated lead submission system with advanced anti-detection capabilities.

## Features

- 🎭 **Advanced Fingerprint Spoofing** - Canvas, WebGL, Audio, Fonts with C++-level accuracy
- 🌐 **Smart Proxy Rotation** - Residential proxies with automatic health checking
- 🤖 **Human-like Behavior** - Bezier curve mouse movements, realistic typing patterns
- 🔄 **Multi-Layer Anti-Detection** - Network, Protocol, Browser, and Behavioral layers
- 💾 **Flexible Data Storage** - SQLite with async support
- 🖥️ **CLI Interface** - Easy to use command-line interface

## Installation

```bash
# Clone the repository
git clone https://github.com/rectoversomedia/ProxyDetection.git
cd ProxyDetection

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .

# Install optional browser automation (choose one)
pip install -e ".[camoufox]"  # Recommended
# or
pip install -e ".[playwright]"
```

## Quick Start

```bash
# Configure API keys
pd config set proxy.dat_impulse.api_key YOUR_API_KEY

# Import leads from CSV
pd leads import --source data/leads.csv

# Submit leads
pd submit --leads data/leads.csv --target https://example.com/form

# Or with custom settings
pd submit --leads data/leads.csv --parallel 3 --delay 5 --profile windows_chrome
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Interface                           │
├─────────────────────────────────────────────────────────────────┤
│                      Core Engine                                │
├─────────────────────────────────────────────────────────────────┤
│                   Anti-Detection Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │ Fingerprint │  │  Behavioral │  │   Proxy     │  │ Browser ││
│  │  Generator  │  │  Simulator  │  │  Rotator    │  │ Launcher││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘│
├─────────────────────────────────────────────────────────────────┤
│                     Browser Engine                              │
├─────────────────────────────────────────────────────────────────┤
│                       Data Layer                                │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration

Create a `.env` file or use the CLI:

```bash
# Proxy Provider API Keys
DAT_IMPULSE_API_KEY=your_dat_impulse_key
DECODO_API_KEY=your_decodo_key

# Browser Settings
BROWSER_TYPE=camoufox
BROWSER_HEADLESS=true

# Submission Settings
DEFAULT_DELAY=5
MAX_PARALLEL=3
```

## CLI Commands

### Lead Management
```bash
pd leads import --source data/leads.csv --format csv
pd leads validate --file data/leads.csv
pd leads generate --count 100 --country US
pd leads list --status pending
```

### Proxy Management
```bash
pd proxy add --file proxies.txt
pd proxy test --count 10
pd proxy list --filter healthy
pd proxy stats
```

### Configuration
```bash
pd config set browser.headless true
pd config get proxy.provider
pd config show
```

### Profile Management
```bash
pd profile create --name custom --os windows --browser chrome
pd profile list
pd profile test --name windows_chrome
```

### Submission
```bash
pd submit --leads data/leads.csv --target https://example.com
pd submit --leads data/leads.csv --parallel 3 --delay 5
```

## Anti-Detection Layers

### Layer 1 - Network
- Residential proxy rotation
- GeoIP-based proxy selection
- Automatic proxy health monitoring

### Layer 2 - Protocol
- TLS fingerprint matching (JA3/JA4)
- HTTP/2 fingerprint consistency
- Perfect handshake simulation

### Layer 3 - Browser
- Canvas fingerprint spoofing with seeded noise
- WebGL vendor/renderer spoofing
- Audio context hash randomization
- Font list matching OS/locale
- Timezone auto-sync with IP

### Layer 4 - Behavioral
- Bezier curve mouse movements
- Log-normal typing distribution
- Natural scroll patterns
- Random delays and pauses

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Lint code
ruff check src/

# Format code
ruff format src/
```

## Requirements

- Python 3.10+
- SQLite 3
- Residential proxy provider (DataImpulse, Decodo, or custom)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

This software is for educational and legitimate automation purposes only. Users are responsible for ensuring their use complies with applicable terms of service and laws.
