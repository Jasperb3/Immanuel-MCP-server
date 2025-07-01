#!/bin/bash

# Setup script for Immanuel MCP Server
# This script helps with initial setup and configuration

set -e

echo "========================================="
echo "Immanuel MCP Server Setup"
echo "========================================="

# Check Python version
echo -n "Checking Python version... "
python_version=$(python3 --version 2>&1 | awk '{print $2}')
major=$(echo $python_version | cut -d. -f1)
minor=$(echo $python_version | cut -d. -f2)

if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
    echo "OK (Python $python_version)"
else
    echo "ERROR"
    echo "Python 3.11 or higher is required. Found: Python $python_version"
    exit 1
fi

# Check if uv is installed
echo -n "Checking for uv... "
if command -v uv &> /dev/null; then
    echo "OK ($(uv --version))"
else
    echo "NOT FOUND"
    echo ""
    echo "uv is not installed. Would you like to install it? (y/n)"
    read -r install_uv
    
    if [ "$install_uv" = "y" ]; then
        echo "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # Add to PATH if needed
        export PATH="$HOME/.cargo/bin:$PATH"
        
        echo "uv installed successfully!"
    else
        echo "Please install uv manually from: https://github.com/astral-sh/uv"
        exit 1
    fi
fi

# Create virtual environment
echo ""
echo "Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    uv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate || . .venv/Scripts/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
uv pip install -r requirements.txt

# Create directories
echo ""
echo "Creating necessary directories..."
mkdir -p ~/.immanuel/ephemeris
mkdir -p ~/.immanuel/cache
mkdir -p logs

# Download ephemeris files
echo ""
echo "Checking Swiss Ephemeris data files..."
EPHE_DIR="$HOME/.immanuel/ephemeris"

if [ ! -f "$EPHE_DIR/semo_18.se1" ] || [ ! -f "$EPHE_DIR/sepl_18.se1" ]; then
    echo "Ephemeris files not found. Would you like to download them? (y/n)"
    read -r download_ephe
    
    if [ "$download_ephe" = "y" ]; then
        echo "Downloading ephemeris files..."
        cd "$EPHE_DIR"
        
        # Main ephemeris files
        wget -q https://www.astro.com/ftp/swisseph/ephe/semo_18.se1
        wget -q https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1
        
        # Optional: Additional asteroids
        echo "Download asteroid ephemeris files? (y/n)"
        read -r download_asteroids
        
        if [ "$download_asteroids" = "y" ]; then
            wget -q https://www.astro.com/ftp/swisseph/ephe/seas_18.se1
        fi
        
        cd - > /dev/null
        echo "Ephemeris files downloaded successfully!"
    else
        echo "WARNING: Ephemeris files are required for accurate calculations."
        echo "You can download them manually from: https://www.astro.com/ftp/swisseph/ephe/"
    fi
else
    echo "Ephemeris files found."
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env configuration file..."
    cat > .env << EOF
# Immanuel MCP Server Configuration

# Server settings
IMMANUEL_SERVER_NAME=immanuel-mcp
IMMANUEL_LOG_LEVEL=INFO

# Cache settings
IMMANUEL_ENABLE_CACHE=true
IMMANUEL_CACHE_MAX_SIZE=1000
IMMANUEL_CACHE_TTL=3600

# Ephemeris path
IMMANUEL_EPHEMERIS_PATH=$HOME/.immanuel/ephemeris

# Default calculation settings
IMMANUEL_DEFAULT_HOUSE_SYSTEM=placidus
IMMANUEL_DEFAULT_ORB_CONJUNCTION=8.0
IMMANUEL_DEFAULT_ORB_OPPOSITION=8.0
IMMANUEL_DEFAULT_ORB_TRINE=8.0
IMMANUEL_DEFAULT_ORB_SQUARE=8.0
IMMANUEL_DEFAULT_ORB_SEXTILE=6.0
IMMANUEL_DEFAULT_ORB_MINOR=3.0

# Timezone settings
IMMANUEL_FALLBACK_TIMEZONE=UTC

# Performance settings
IMMANUEL_MAX_BATCH_SIZE=100
IMMANUEL_CALCULATION_TIMEOUT=30
EOF
    echo ".env file created."
else
    echo ""
    echo ".env file already exists."
fi

# Configure Claude Desktop
echo ""
echo "========================================="
echo "Claude Desktop Configuration"
echo "========================================="
echo ""
echo "To use this MCP server with Claude Desktop, add the following"
echo "to your Claude Desktop configuration file:"
echo ""
echo "macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "immanuel": {'
echo '      "command": "uv",'
echo '      "args": ["run", "python", "-m", "immanuel_mcp.main"],'
echo '      "cwd": "'$(pwd)'"'
echo '    }'
echo '  }'
echo '}'
echo ""

# Test the installation
echo "========================================="
echo "Testing Installation"
echo "========================================="
echo ""
echo "Running basic tests..."

# Test imports
python3 -c "
try:
    import immanuel
    print('✓ immanuel-python imported successfully')
except ImportError as e:
    print('✗ Failed to import immanuel-python:', e)
    
try:
    import mcp
    print('✓ MCP imported successfully')
except ImportError as e:
    print('✗ Failed to import MCP:', e)
    
try:
    from immanuel_mcp import ChartService
    print('✓ Immanuel MCP modules imported successfully')
except ImportError as e:
    print('✗ Failed to import Immanuel MCP:', e)
"

# Run a quick test calculation
echo ""
echo "Running test chart calculation..."
python3 cli.py example > /dev/null 2>&1 && echo "✓ Test calculation successful" || echo "✗ Test calculation failed"

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure Claude Desktop with the settings shown above"
echo "2. Restart Claude Desktop"
echo "3. The Immanuel MCP server should now be available"
echo ""
echo "You can also:"
echo "- Run 'python cli.py example' for a demo"
echo "- Run 'python cli.py interactive' for interactive mode"
echo "- Run 'python -m immanuel_mcp.api' to start the HTTP API server"
echo "- Run 'python examples.py' to see usage examples"
echo ""
echo "For more information, see README.md"