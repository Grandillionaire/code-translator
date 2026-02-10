# Code Translator 🔄

[![CI/CD](https://github.com/Grandillionaire/code-translator/actions/workflows/ci.yml/badge.svg)](https://github.com/Grandillionaire/code-translator/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5.0+-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A professional code translator that intelligently translates code between programming languages using AI. Features a modern desktop GUI, web API, and CLI interface.

![Code Translator Demo](docs/demo.gif)

## ✨ Features

### 🤖 AI-Powered Translation
- **Multiple AI Providers**: OpenAI GPT-4, Anthropic Claude, Google Gemini
- **Intelligent Translation**: Handles paradigm differences, not just syntax
- **Confidence Scores**: Know how reliable each translation is
- **Automatic Fallback**: Seamlessly switches providers if one fails

### 🌐 10+ Languages Supported
- Python
- JavaScript / TypeScript
- Java / Kotlin
- Swift
- C++
- Go
- Rust
- Ruby

### 🖥️ Multiple Interfaces
- **Desktop GUI** - Beautiful PyQt6 app with transparency support
- **Web API** - FastAPI backend with interactive frontend
- **CLI** - Command-line tool for scripts and pipelines

### ⚡ Smart Features
- Auto-detect source language
- Syntax highlighting
- Translation history
- Clipboard integration
- Offline mode with basic translations

## 🚀 Quick Start

### Desktop GUI
```bash
# Clone and install
git clone https://github.com/Grandillionaire/code-translator.git
cd code-translator
pip install -r requirements.txt

# Run the desktop app
python src/main.py
```

### CLI Mode
```bash
# Translate a file
python -m code_translator --from python --to javascript input.py

# Auto-detect source language
python -m code_translator --to rust input.py -o output.rs

# Translate from stdin
echo "print('hello')" | python -m code_translator --from python --to java

# List supported languages
python -m code_translator --list-languages
```

### Web API
```bash
# Install web dependencies
pip install fastapi uvicorn

# Run the server
uvicorn src.web.app:app --reload

# Open http://localhost:8000 in your browser
```

## 📦 Installation

### Requirements
- Python 3.9 or higher
- pip (Python package manager)

### Full Installation
```bash
# Clone repository
git clone https://github.com/Grandillionaire/code-translator.git
cd code-translator

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Set up API keys (optional - for AI providers)
# Add to environment or use the settings dialog in GUI
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

### Platform-Specific Notes

#### macOS
```bash
# Global hotkeys require accessibility permissions
# Grant permission when prompted on first run
```

#### Linux
```bash
# Requires X11 for transparency features
sudo apt-get install libxkbcommon-x11-0 libxcb-cursor0
```

## 🔧 Configuration

### API Keys
Configure in Settings dialog or via environment variables:
- `OPENAI_API_KEY` - Get from [platform.openai.com](https://platform.openai.com)
- `ANTHROPIC_API_KEY` - Get from [console.anthropic.com](https://console.anthropic.com)
- `GOOGLE_API_KEY` - Get from [makersuite.google.com](https://makersuite.google.com)

### Settings Location
- **Windows**: `%APPDATA%\CodeTranslator\settings.json`
- **macOS/Linux**: `~/.config/CodeTranslator/settings.json`

## 🌐 Web API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/languages` | List supported languages |
| POST | `/api/detect` | Detect language |
| POST | `/api/translate` | Translate code |

### Example: Translate Code
```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello(): print(\"Hello!\")",
    "source_lang": "Python",
    "target_lang": "JavaScript"
  }'
```

### Response
```json
{
  "translated_code": "function hello() {\n  console.log(\"Hello!\");\n}",
  "source_lang": "Python",
  "target_lang": "JavaScript",
  "confidence": 0.95,
  "provider_used": "anthropic"
}
```

## ☁️ Deployment

### Deploy to Railway
```bash
# Login to Railway CLI
railway login

# Initialize and deploy
railway init
railway up

# Set environment variables
railway variables set OPENAI_API_KEY=your-key
```

### Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy (create vercel.json first)
vercel deploy
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 Development

### Setup Development Environment
```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Format code
black src/ tests/

# Type checking
mypy src/

# Lint
flake8 src/
```

### Project Structure
```
code-translator/
├── src/
│   ├── __main__.py          # CLI entry point
│   ├── main.py              # Desktop app entry point
│   ├── gui/                 # PyQt6 GUI components
│   ├── translator/          # Translation engine
│   │   ├── translator_engine.py
│   │   └── offline_translator.py
│   ├── web/                 # FastAPI web app
│   │   ├── app.py
│   │   └── templates/
│   ├── config/              # Configuration management
│   ├── providers/           # AI provider implementations
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── .github/workflows/       # CI/CD pipelines
├── requirements.txt
└── README.md
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_api_compatibility.py -v
```

## ⌨️ Keyboard Shortcuts (Desktop)

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+T` | Show/Hide window |
| `Ctrl+Enter` | Translate code |
| `Ctrl+D` | Toggle dark/light theme |
| `Ctrl+H` | Show history |
| `Ctrl+S` | Save to favorites |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [PyQt6](https://riverbankcomputing.com/software/pyqt/)
- Web API powered by [FastAPI](https://fastapi.tiangolo.com)
- AI translation by OpenAI, Anthropic, and Google

---

Made with ❤️ by [Grandillionaire](https://github.com/Grandillionaire)
