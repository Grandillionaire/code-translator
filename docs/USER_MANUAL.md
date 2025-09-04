# Code Translator - User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Interface](#user-interface)
3. [Translation Features](#translation-features)
4. [Keyboard Shortcuts](#keyboard-shortcuts)
5. [Settings & Configuration](#settings--configuration)
6. [Advanced Features](#advanced-features)
7. [Tips & Tricks](#tips--tricks)
8. [FAQ](#faq)

## Getting Started

### First Launch
When you first start Code Translator, you'll see a semi-transparent overlay window that floats above other applications.

### Initial Setup
1. Click the **Settings** button (⚙) in the title bar
2. Navigate to the **API Keys** tab
3. Enter at least one API key (OpenAI, Anthropic, or Google)
4. Click **OK** to save

### Basic Translation
1. **Input Code**: Paste or type code in the left panel
2. **Select Languages**: Choose source and target languages (or use auto-detect)
3. **Translate**: Press `Ctrl+Enter` or click the "Translate" button
4. **View Result**: The translated code appears in the right panel

## User Interface

### Main Window Components

#### Title Bar
- **Window Title**: "Code Translator"
- **Minimize Button** (−): Minimize to taskbar
- **Click-through Toggle** (👁): Make window transparent to mouse clicks
- **History Button** (📋): Open translation history
- **Settings Button** (⚙): Open settings dialog
- **Close Button** (×): Close the application

#### Translation Area
- **Left Panel**: Source code input
- **Right Panel**: Translated code output
- **Language Selectors**: Dropdown menus for source/target languages
- **Translate Button**: Initiates translation
- **Swap Button** (⇄): Swap source and target languages
- **Favorite Button** (☆/★): Save/unsave current translation
- **Paste Button** (📋): Paste from clipboard

### Visual Indicators
- **Confidence Score**: Shows translation accuracy (e.g., "Confidence: 95%")
- **Syntax Highlighting**: Automatic code coloring based on language
- **Status Bar**: Shows current operation status

## Translation Features

### Supported Languages
- Python
- JavaScript
- Java
- C++
- Go
- Rust

### Language Auto-Detection
The translator can automatically detect the source programming language based on:
- Syntax patterns
- Keywords
- File extensions (when using drag & drop)

### Translation Modes

#### Online Translation (AI-Powered)
- Uses OpenAI GPT-4, Anthropic Claude, or Google Gemini
- Handles complex paradigm differences
- Provides high-quality, context-aware translations

#### Offline Translation
- Basic syntax conversion when no internet
- Limited but functional for simple translations
- Automatically activated when API is unavailable

### Drag & Drop
- Drop code files directly into the input area
- Supports: `.py`, `.js`, `.java`, `.cpp`, `.go`, `.rs`, `.txt`
- Automatically detects language from file extension

## Keyboard Shortcuts

### Global Shortcuts
| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+Shift+T` | Show/Hide | Toggle window visibility |
| `Ctrl+Enter` | Translate | Translate current code |
| `Ctrl+M` | Click-through | Toggle click-through mode |
| `Ctrl+D` | Theme | Toggle dark/light theme |
| `Ctrl+\` | Close | Close application |
| `Ctrl+H` | History | Open history dialog |
| `Ctrl+S` | Save Favorite | Save current translation |

### Window Navigation
| Shortcut | Action |
|----------|--------|
| `Ctrl+←` | Move left |
| `Ctrl+→` | Move right |
| `Ctrl+↑` | Move up |
| `Ctrl+↓` | Move down |

## Settings & Configuration

### General Settings
- **Auto-detect Language**: Automatically detect source code language
- **Save Translation History**: Keep record of translations
- **Real-time Translation**: Translate as you type (with delay)
- **History Limit**: Maximum number of saved translations
- **Start Minimized**: Start in system tray

### API Keys
- **OpenAI**: For GPT-4 translations
- **Anthropic**: For Claude translations
- **Google**: For Gemini translations

*Note: Keys are encrypted and stored locally*

### Appearance
- **Theme**: Dark or Light mode
- **Window Opacity**: Adjust transparency (30-100%)
- **Font Size**: Code editor font size

### Advanced Settings
- **Translation Timeout**: Maximum wait time for API
- **Cache Translations**: Store recent translations
- **Log Level**: Debugging verbosity

## Advanced Features

### Translation History
- Access with `Ctrl+H` or History button
- Search through past translations
- Filter by language or date
- Double-click to load any translation

### Favorites System
- Star important translations
- Quick access to frequently used code
- Organized separately from history
- Persistent across sessions

### Click-through Mode
When activated:
- Window becomes transparent to mouse clicks
- Can interact with applications behind
- Opacity automatically reduced
- Toggle with `Ctrl+M`

### Real-time Translation
When enabled:
- Translates as you type
- 1-second delay after stopping
- Useful for learning syntax differences
- Can be intensive on API usage

### Export/Import Settings
Export your configuration:
```bash
python3 -m code_translator export-settings my-settings.yaml
```

Import settings:
```bash
python3 -m code_translator import-settings my-settings.yaml
```

## Tips & Tricks

### Performance Tips
1. **Use Favorites**: Save commonly translated patterns
2. **Enable Caching**: Reduces API calls for repeated translations
3. **Offline Mode**: Use for simple syntax when API is slow
4. **Batch Operations**: Translate larger code blocks at once

### Quality Tips
1. **Complete Code**: Include full context for better translations
2. **Comments**: Include comments for clarity
3. **Clean Code**: Well-formatted input produces better output
4. **Review Output**: Always verify critical logic

### Workflow Tips
1. **Dual Monitor**: Place on second monitor for reference
2. **Opacity Setting**: Adjust for your background
3. **Keyboard Mastery**: Learn shortcuts for speed
4. **History Search**: Use keywords to find past work

## FAQ

### Q: Why is my translation taking long?
A: Check your internet connection and API provider status. You can switch providers in settings.

### Q: Can I use without internet?
A: Yes! Offline mode provides basic translation, though quality is reduced.

### Q: How secure are my API keys?
A: Keys are encrypted using industry-standard encryption and stored locally only.

### Q: Can I translate entire files?
A: Drag and drop files into the window. For batch processing, consider our CLI tool.

### Q: Why is the confidence score low?
A: Complex paradigm differences or ambiguous code can reduce confidence. Review carefully.

### Q: How do I report bugs?
A: Use the GitHub Issues page or run diagnostics with `python3 test_comprehensive.py`

### Q: Can I contribute?
A: Yes! See CONTRIBUTING.md for guidelines.

## Troubleshooting

### Common Issues

**Window not staying on top**
- Windows: Run as administrator
- macOS: Grant accessibility permissions
- Linux: Check window manager settings

**Translation errors**
- Verify API key is valid
- Check API usage limits
- Try a different provider
- Use offline mode temporarily

**Performance issues**
- Disable real-time translation
- Clear translation cache
- Reduce history limit
- Close unused applications

### Debug Mode
Run with debug logging:
```bash
python3 src/main.py --debug
```

Check logs at:
- Windows: `%APPDATA%\CodeTranslator\logs\`
- macOS/Linux: `~/.config/CodeTranslator/logs/`

---

For more help, visit our [GitHub repository](https://github.com/yourusername/code-translator) or check the [installation guide](../INSTALLATION.md).