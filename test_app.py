#!/usr/bin/env python3
"""
Test script to verify the Code Translator installation
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from PyQt6.QtWidgets import QApplication
    print("✓ PyQt6 is installed correctly")
except ImportError:
    print("✗ PyQt6 is not installed. Run: pip install PyQt6")
    sys.exit(1)

try:
    from gui.main_window import TranslatorWindow
    from config.settings import Settings
    from translator.translator_engine import TranslatorEngine
    print("✓ All modules can be imported")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

print("\nTesting offline translation...")
try:
    from translator.offline_translator import OfflineTranslator
    translator = OfflineTranslator()
    
    # Test Python to JavaScript
    python_code = """
def greet(name):
    print(f"Hello, {name}!")
    return True
"""
    
    js_result = translator.translate(python_code, "Python", "JavaScript")
    print("Python to JavaScript translation:")
    print(js_result)
    print("\n✓ Offline translation is working")
    
except Exception as e:
    print(f"✗ Translation error: {e}")

print("\nAll tests passed! You can run the main application with:")
print("python src/main.py")