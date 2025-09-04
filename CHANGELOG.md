# Changelog

All notable changes to Code Translator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2024-01-30

### Added
- **OpenAI API Compatibility Layer**: Automatic support for both old (<1.0) and new (>=1.0) OpenAI library versions
- **Comprehensive Dependency Checker**: Advanced runtime dependency validation with detailed reports
- **Installation Scripts**: Automated installers for Windows (install.bat) and Unix/macOS (install.sh)
- **GitHub Actions CI/CD**: Complete continuous integration pipeline with multi-platform testing
- **Enhanced Error Handling**: Better error messages and automatic fallback mechanisms
- **Version Range Support**: Flexible dependency versioning with proper constraints

### Changed
- **Updated requirements.txt**: Now supports version ranges instead of fixed versions
- **Improved setup.py**: Better package metadata and platform-specific dependencies
- **Enhanced main.py**: Added runtime dependency validation before startup
- **Refactored translator_engine.py**: Uses new API compatibility wrapper for OpenAI

### Fixed
- Fixed OpenAI API calls to work with both old and new library versions
- Fixed dependency version conflicts
- Improved error handling for missing API providers

### Security
- All API keys are validated at runtime
- Better error messages that don't expose sensitive information

## [1.0.0] - 2024-01-15

### Added
- Initial release with core functionality
- Support for 6 programming languages (Python, JavaScript, Java, C++, Go, Rust)
- Integration with OpenAI, Anthropic, and Google AI providers
- Offline translation capabilities
- Modern PyQt6-based GUI
- Translation history and favorites
- Syntax highlighting
- Dark/light theme support
- Global keyboard shortcuts
- Transparent overlay mode

### Known Issues
- OpenAI library version 1.0+ requires different API syntax (fixed in 1.2.0)

---

[1.2.0]: https://github.com/yourusername/code-translator/compare/v1.0.0...v1.2.0
[1.0.0]: https://github.com/yourusername/code-translator/releases/tag/v1.0.0