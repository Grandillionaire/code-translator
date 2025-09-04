# Code Translator - Complete Installation Guide

This guide will walk you through downloading, installing, and running the Code Translator application on your computer.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Download the Project](#download-the-project)
3. [Installation Steps](#installation-steps)
4. [First Launch](#first-launch)
5. [Getting API Keys](#getting-api-keys)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
1. **Python 3.8 or newer**
   - Check if installed: `python3 --version`
   - Download from: https://www.python.org/downloads/
   
2. **Git** (for cloning the repository)
   - Check if installed: `git --version`
   - Download from: https://git-scm.com/downloads

### System Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux (with X11)
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 500MB free space

## Download the Project

### Option 1: Using Git (Recommended)

1. Open Terminal (macOS/Linux) or Command Prompt (Windows)
2. Navigate to where you want to install:
   ```bash
   cd ~/Desktop  # or any folder you prefer
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/code-translator.git
   ```
4. Enter the project directory:
   ```bash
   cd code-translator
   ```

### Option 2: Download ZIP

1. Go to https://github.com/yourusername/code-translator
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file to your desired location
5. Open Terminal/Command Prompt and navigate to the extracted folder

## Installation Steps

### 1. Create Virtual Environment (Recommended)

This keeps the project dependencies isolated from your system Python.

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required packages including:
- PyQt6 (GUI framework)
- AI provider libraries (OpenAI, Anthropic, Google)
- Security libraries for API key encryption

### 3. Verify Installation

Run the test suite to ensure everything is working:
```bash
python test_comprehensive.py
```

You should see all tests passing with green checkmarks ✓.

## First Launch

### Starting the Application

**Method 1: Direct Launch**
```bash
python src/main.py
```

**Method 2: Using the Run Script**
```bash
python run.py
```

**Method 3: Make it Executable (macOS/Linux)**
```bash
chmod +x run.py
./run.py
```

### Initial Setup

1. **Main Window**: A transparent overlay window will appear
2. **Settings**: Click the gear icon (⚙) in the title bar
3. **API Keys**: Navigate to the "API Keys" tab
4. **Add Keys**: Enter at least one API key (see next section)
5. **Save**: Click OK to save settings

## Getting API Keys

You need at least ONE of these API keys for AI-powered translation:

### OpenAI (GPT-4)
1. Visit https://platform.openai.com/signup
2. Create an account or sign in
3. Go to https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. Paste into the OpenAI field in settings

### Anthropic (Claude)
1. Visit https://console.anthropic.com
2. Create an account or sign in
3. Go to "API Keys" section
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)
6. Paste into the Anthropic field in settings

### Google (Gemini)
1. Visit https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key
5. Paste into the Google field in settings

## Using the Application

### Basic Usage
1. **Paste or type** code in the left panel
2. **Select languages** or use auto-detect
3. **Press Ctrl+Enter** or click "Translate"
4. **View results** in the right panel

### Keyboard Shortcuts
- `Ctrl+Shift+T`: Show/hide window
- `Ctrl+Enter`: Translate
- `Ctrl+M`: Toggle click-through mode
- `Ctrl+D`: Toggle dark/light theme
- `Ctrl+H`: Show history
- `Ctrl+\`: Close window

### Features
- **Drag & Drop**: Drop code files directly into the window
- **History**: Access previous translations with Ctrl+H
- **Favorites**: Star translations for quick access
- **Real-time**: Enable in settings for as-you-type translation

## Troubleshooting

### Common Issues

**"No module named 'PyQt6'"**
```bash
pip install --upgrade PyQt6
```

**"API key invalid"**
- Ensure you've entered the key correctly
- Check if your API account has available credits
- Try a different provider

**Window not appearing**
- Check if Python has screen recording permissions (macOS)
- Try running with administrator privileges (Windows)
- Ensure no antivirus is blocking the app

**Transparent window issues (Linux)**
- Ensure you're using X11, not Wayland
- Install compositor if needed: `sudo apt install compton`

### Platform-Specific Issues

**macOS**
- Grant accessibility permissions when prompted
- If window doesn't stay on top: System Preferences → Security & Privacy → Accessibility

**Windows**
- Run as Administrator if overlay doesn't work
- Disable Windows Defender temporarily if flagged

**Linux**
- Install additional dependencies if needed:
  ```bash
  sudo apt-get install python3-pyqt6 libxcb-xinerama0
  ```

### Getting Help

1. **Check logs**: Look in `~/.config/CodeTranslator/logs/`
2. **Run tests**: `python test_comprehensive.py`
3. **Debug mode**: `python src/main.py --debug`
4. **GitHub Issues**: Report bugs at the repository

## Uninstallation

1. **Remove virtual environment**: Delete the `venv` folder
2. **Remove settings**: 
   - Windows: `%APPDATA%\CodeTranslator`
   - macOS/Linux: `~/.config/CodeTranslator`
3. **Delete project folder**: Remove the `code-translator` directory

## Next Steps

- Read the [User Guide](docs/user-guide.md) for detailed features
- Check [API Documentation](docs/api-docs.md) for advanced usage
- Join our [Discord](https://discord.gg/codetranslator) community

---

Happy translating! 🚀