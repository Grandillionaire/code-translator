#!/bin/bash
# Code Translator Installation Script for Unix/macOS
# Ensures proper setup of the application with all dependencies

set -e

echo "===================================================="
echo "Code Translator - Unix/macOS Installation Script"
echo "===================================================="
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python installation
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or newer:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
    echo -e "${GREEN}Python $PYTHON_VERSION OK${NC}"
else
    echo -e "${RED}ERROR: Python $REQUIRED_VERSION or newer is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Check for venv module
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${RED}ERROR: Python venv module not installed${NC}"
    echo "Please install it:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-venv"
    echo "  Fedora: sudo dnf install python3-venv"
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo
echo "Installing dependencies..."
echo "This may take a few minutes..."
echo

# Core dependencies
if pip install -r requirements.txt; then
    echo -e "${GREEN}Core dependencies installed successfully${NC}"
else
    echo -e "${RED}ERROR: Failed to install core dependencies${NC}"
    exit 1
fi

# Optional AI dependencies (continue on error)
echo
echo "Installing optional AI providers..."
pip install openai anthropic google-generativeai 2>/dev/null || true

# Install the package
echo
echo "Installing Code Translator..."
if pip install -e .; then
    echo -e "${GREEN}Code Translator installed successfully${NC}"
else
    echo -e "${RED}ERROR: Failed to install Code Translator${NC}"
    exit 1
fi

# Check installation
echo
echo "Verifying installation..."
python check_system.py

# Create desktop entry for Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    DESKTOP_FILE="$HOME/.local/share/applications/code-translator.desktop"
    mkdir -p "$HOME/.local/share/applications"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Code Translator
Comment=Professional code translation tool
Exec=$PWD/start.sh
Icon=$PWD/src/assets/icon.png
Terminal=false
Categories=Development;Utility;
EOF
    
    chmod +x "$DESKTOP_FILE"
    echo -e "${GREEN}Desktop entry created${NC}"
fi

# Create macOS app bundle
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Creating macOS app..."
    # This would create a proper .app bundle, but for now we'll use the start script
    if [ -f "start.sh" ]; then
        chmod +x start.sh
    fi
fi

# Make start script executable
if [ -f "start.sh" ]; then
    chmod +x start.sh
fi

echo
echo "===================================================="
echo -e "${GREEN}Installation completed successfully!${NC}"
echo "===================================================="
echo
echo "To run Code Translator:"
echo "  1. Run: ./start.sh"
echo "  2. Or run: source venv/bin/activate && python src/main.py"
echo
echo "Don't forget to add your API keys in the settings!"
echo
echo "For global command line access, add to PATH:"
echo "  export PATH=\"$PWD/venv/bin:\$PATH\""
echo