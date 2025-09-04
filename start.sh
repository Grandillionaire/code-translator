#!/bin/bash
# Code Translator launcher for macOS/Linux

echo "Starting Code Translator..."

# Function to find the best Python command
find_python() {
    # Check for python3 first (preferred)
    if command -v python3 &> /dev/null; then
        echo "python3"
        return 0
    fi
    
    # Check if 'python' points to Python 3.x
    if command -v python &> /dev/null; then
        # Check if it's Python 3
        if python -c "import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)" 2>/dev/null; then
            echo "python"
            return 0
        fi
    fi
    
    # Try specific versions
    for version in python3.12 python3.11 python3.10 python3.9 python3.8; do
        if command -v $version &> /dev/null; then
            echo "$version"
            return 0
        fi
    done
    
    # No suitable Python found
    return 1
}

# Find Python command
PYTHON_CMD=$(find_python)
if [ $? -ne 0 ]; then
    echo "Error: Python 3.8 or newer is not installed!"
    echo "Please install Python from https://www.python.org"
    echo ""
    echo "Searched for: python3, python, python3.12, python3.11, python3.10, python3.9, python3.8"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"

# Get Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo "Python version: $PYTHON_VERSION"

# Check Python version is >= 3.8
$PYTHON_CMD -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"
if [ $? -ne 0 ]; then
    echo "Error: Python 3.8 or newer is required (found $PYTHON_VERSION)"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo "Error: Cannot find src/main.py"
    echo "Please run this script from the code-translator directory"
    exit 1
fi

# Find pip command
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif $PYTHON_CMD -m pip --version &> /dev/null; then
    PIP_CMD="$PYTHON_CMD -m pip"
else
    echo "Warning: pip not found. Cannot check dependencies."
    echo "Attempting to run anyway..."
    PIP_CMD=""
fi

# Check if dependencies are installed
$PYTHON_CMD -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    if [ -n "$PIP_CMD" ]; then
        echo "Dependencies not installed. Installing now..."
        $PIP_CMD install -r requirements.txt
    else
        echo "Error: PyQt6 not installed and pip not available."
        echo "Please install dependencies manually:"
        echo "  $PYTHON_CMD -m pip install -r requirements.txt"
        exit 1
    fi
fi

# Launch the application
echo "Launching Code Translator..."
exec $PYTHON_CMD src/main.py "$@"