# Code Translator 🔄

A professional desktop code translator application that intelligently translates code between programming languages using AI. Built with Python and PyQt6, featuring a transparent overlay interface for seamless workflow integration.

## 📚 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get running in 5 minutes
- **[Installation Guide](INSTALLATION.md)** - Detailed setup instructions
- **[User Manual](docs/USER_MANUAL.md)** - Complete feature documentation

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

### 🤖 AI-Powered Translation
- **Multiple AI Providers**: Support for OpenAI GPT-4, Anthropic Claude, and Google Gemini
- **OpenAI Compatibility**: Automatic support for both old (<1.0) and new (>=1.0) OpenAI library versions
- **Intelligent Translation**: Handles paradigm differences between languages, not just syntax
- **Auto-Detection**: Automatically detects source programming language
- **Confidence Scores**: Shows translation confidence levels
- **Automatic Fallback**: Seamlessly switches between providers if one fails

### 🖥️ Modern UI
- **Transparent Overlay**: Always-on-top window with adjustable transparency
- **Dark/Light Themes**: Toggle between dark and light modes
- **Syntax Highlighting**: Full syntax highlighting for all supported languages
- **Resizable & Draggable**: Position the window anywhere on your screen

### ⚡ Productivity Features
- **Global Keyboard Shortcuts**: Quick access from anywhere
- **Translation History**: Save and search through past translations
- **Favorites System**: Star and save frequently used translations
- **Clipboard Integration**: Paste code directly from clipboard
- **Drag & Drop**: Drop code files directly into the translator
- **Real-time Translation**: Translate as you type (optional)
- **Click-through Mode**: Make window transparent to mouse clicks

### 🌐 Language Support
- Python
- JavaScript
- Java
- C++
- Go
- Rust

### 🔐 Security & Privacy
- **Encrypted API Keys**: All API keys stored locally with encryption
- **Local Storage**: All data stored locally by default
- **Privacy Mode**: Option to disable history for sensitive code

## 📦 Installation

### Requirements
- Python 3.8 or higher
- Git (for downloading the project)
- API key for at least one AI provider (OpenAI, Anthropic, or Google)

### Quick Start (3 Steps)

```bash
# 1. Download the project
git clone https://github.com/yourusername/code-translator.git
cd code-translator

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Run the application
python3 src/main.py
```

**📖 Need detailed instructions?** See [INSTALLATION.md](INSTALLATION.md) for a complete step-by-step guide including:
- How to install Python
- Getting API keys
- Troubleshooting common issues
- Platform-specific setup

### Platform-Specific Notes

#### Windows
```bash
# Full functionality with transparent windows
python src/main.py
```

#### macOS
```bash
# Install with global hotkey support
pip install -e ".[ai,global-hotkeys]"

# Grant accessibility permissions when prompted
python src/main.py
```

#### Linux
```bash
# Requires X11 for transparency
python src/main.py
```

## 🚀 Usage

### First-Time Setup
1. Launch the application
2. Click the settings button (⚙)
3. Add at least one API key in the "API Keys" tab
4. Configure your preferences

### Basic Translation
1. Paste or type code in the left panel
2. Select source and target languages (or use auto-detect)
3. Press `Ctrl+Enter` or click "Translate"
4. View translated code in the right panel

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+T` | Show/Hide window |
| `Ctrl+Enter` | Translate code |
| `Ctrl+M` | Toggle click-through mode |
| `Ctrl+D` | Toggle dark/light theme |
| `Ctrl+\` | Close window |
| `Ctrl+Arrow Keys` | Move window |
| `Ctrl+H` | Show history |
| `Ctrl+S` | Save to favorites |

## 🛠️ Configuration

### API Keys
Add your API keys in Settings → API Keys:
- **OpenAI**: Get from [platform.openai.com](https://platform.openai.com)
- **Anthropic**: Get from [console.anthropic.com](https://console.anthropic.com)
- **Google**: Get from [makersuite.google.com](https://makersuite.google.com)

### Settings Location
- **Windows**: `%APPDATA%\CodeTranslator\settings.json`
- **macOS/Linux**: `~/.config/CodeTranslator/settings.json`

### Export/Import Settings
```python
# Export settings (without API keys)
python -m code_translator export-settings settings.yaml

# Import settings
python -m code_translator import-settings settings.yaml
```

## 🧩 Advanced Features

### Offline Mode
When no internet connection is available, the app automatically falls back to basic syntax translation using built-in rules.

### Translation Cache
Recent translations are cached locally for faster access and offline availability.

### Custom Providers
You can add custom translation providers by implementing the provider interface. See [docs/custom-providers.md](docs/custom-providers.md).

## 🔧 Development

### Setup Development Environment
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Type checking
mypy src/

# Linting
flake8 src/
```

### Project Structure
```
code-translator/
├── src/
│   ├── main.py                 # Application entry point
│   ├── gui/                    # GUI components
│   │   ├── main_window.py      # Main window implementation
│   │   └── widgets.py          # Custom widgets
│   ├── translator/             # Translation engine
│   │   ├── translator_engine.py # AI translation logic
│   │   └── offline_translator.py # Offline translation
│   ├── config/                 # Configuration management
│   │   └── settings.py         # Settings handler
│   └── utils/                  # Utility functions
│       ├── logger.py           # Logging configuration
│       └── shortcuts.py        # Keyboard shortcuts
├── tests/                      # Test suite
├── docs/                       # Documentation
├── requirements.txt            # Python dependencies
├── setup.py                    # Installation script
├── README.md                   # This file
└── LICENSE                     # MIT License
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- AI translation powered by OpenAI, Anthropic, and Google
- Syntax highlighting inspired by VS Code themes

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/code-translator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/code-translator/discussions)
- **Wiki**: [Project Wiki](https://github.com/yourusername/code-translator/wiki)

## 🗺️ Roadmap

- [ ] Support for more programming languages (TypeScript, Swift, Kotlin)
- [ ] Real-time collaborative translation
- [ ] VS Code extension
- [ ] Web version with similar functionality
- [ ] Custom translation rules editor
- [ ] Integration with popular IDEs
- [ ] Batch file translation
- [ ] Translation quality metrics

---

Made with ❤️ by the Code Translator Team