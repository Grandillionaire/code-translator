# Code Translator VS Code Extension

> ⚠️ **Coming Soon** - This VS Code extension is currently in development.

This folder contains the foundation for a VS Code extension that will integrate Code Translator directly into your editor.

## 🎯 Planned Features

- **Inline Translation** - Right-click any selection to translate to another language
- **Command Palette** - Quick access to translation commands
- **Status Bar** - Shows detected language and translation status
- **Side Panel** - Dedicated translation workspace
- **Keyboard Shortcuts** - Fast translation with customizable hotkeys
- **Multi-file Support** - Translate entire files or selections

## 📦 Building the Extension

### Prerequisites

- Node.js 18+
- npm or yarn
- VS Code 1.80+

### Development Setup

```bash
# Navigate to extension folder
cd vscode-extension

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch mode for development
npm run watch

# Package the extension
npm run package
```

### Testing

```bash
# Run extension tests
npm test

# Launch Extension Development Host
# Press F5 in VS Code with this folder open
```

## 🔧 Configuration

The extension will support the following settings:

```json
{
  "codeTranslator.defaultTargetLanguage": "JavaScript",
  "codeTranslator.provider": "auto",
  "codeTranslator.apiKeys.openai": "",
  "codeTranslator.apiKeys.anthropic": "",
  "codeTranslator.apiKeys.google": "",
  "codeTranslator.showConfidence": true,
  "codeTranslator.autoDetectLanguage": true
}
```

## 📚 Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines)
- [Publishing Extensions](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
- [VS Code Extension Samples](https://github.com/microsoft/vscode-extension-samples)

## 🤝 Contributing

We welcome contributions to the VS Code extension! Please check the main repository's [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## 📝 Roadmap

1. **Phase 1**: Basic translation commands and context menu
2. **Phase 2**: Side panel UI with preview
3. **Phase 3**: Multi-provider support and settings
4. **Phase 4**: Marketplace publication

---

Check back soon for updates!
