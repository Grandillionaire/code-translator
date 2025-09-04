"""
Setup script for Code Translator
Professional code translation tool with AI integration
"""

from setuptools import setup, find_packages
from pathlib import Path
import sys

# Ensure minimum Python version
if sys.version_info < (3, 8):
    print("ERROR: Code Translator requires Python 3.8 or newer")
    print(f"You are using Python {sys.version}")
    sys.exit(1)

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')

# Read version from package
version = "1.2.0"  # Updated version with compatibility fixes

setup(
    name="code-translator-pro",
    version=version,
    author="Code Translator Team",
    author_email="contact@codetranslator.io",
    description="A professional desktop code translator with AI integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/code-translator",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/code-translator/issues",
        "Documentation": "https://github.com/yourusername/code-translator/wiki",
        "Changelog": "https://github.com/yourusername/code-translator/blob/main/CHANGELOG.md",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.5.0,<7.0.0",
        "requests>=2.31.0,<3.0.0",
        "cryptography>=41.0.0,<42.0.0",
        "pyyaml>=6.0.1,<7.0.0",
        "pyperclip>=1.8.2,<2.0.0",
        "keyring>=24.2.0,<25.0.0",
    ],
    extras_require={
        "ai": [
            "openai>=0.27.0",  # Supports both old and new versions
            "anthropic>=0.7.0,<1.0.0",
            "google-generativeai>=0.3.0,<1.0.0",
        ],
        "dev": [
            "pytest>=7.4.0,<8.0.0",
            "black>=23.7.0,<24.0.0",
            "mypy>=1.4.1,<2.0.0",
            "flake8>=6.1.0,<7.0.0",
            "build>=0.10.0",  # For building distributions
            "twine>=4.0.0",   # For uploading to PyPI
        ],
        "global-hotkeys": [
            "pynput>=1.7.6,<2.0.0 ; sys_platform == 'darwin'",  # macOS only
        ],
        "all": [
            "openai>=0.27.0",
            "anthropic>=0.7.0,<1.0.0",
            "google-generativeai>=0.3.0,<1.0.0",
            "pynput>=1.7.6,<2.0.0 ; sys_platform == 'darwin'",
        ],
    },
    entry_points={
        "console_scripts": [
            "code-translator=main:main",
        ],
        "gui_scripts": [
            "code-translator-gui=main:main",
        ],
    },
    package_data={
        "": ["*.yaml", "*.json", "*.png", "*.ico"],
    },
)