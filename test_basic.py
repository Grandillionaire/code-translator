#!/usr/bin/env python3
"""
Basic test script for Code Translator application
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from translator.offline_translator import OfflineTranslator
from config.settings import Settings


def test_offline_translation():
    """Test offline translation capabilities"""
    print("Testing offline translation...")
    offline = OfflineTranslator()
    
    # Test Python to JavaScript
    python_code = """def greet(name):
    return f"Hello, {name}!"
    
print(greet("World"))"""
    
    js_result = offline.translate(python_code, "Python", "JavaScript")
    print(f"\nPython to JavaScript:\nOriginal:\n{python_code}\n\nTranslated:\n{js_result}")
    
    # Test JavaScript to Python
    js_code = """function add(a, b) {
    return a + b;
}

console.log(add(5, 3));"""
    
    py_result = offline.translate(js_code, "JavaScript", "Python")
    print(f"\nJavaScript to Python:\nOriginal:\n{js_code}\n\nTranslated:\n{py_result}")


def test_settings():
    """Test settings management"""
    print("\nTesting settings...")
    settings = Settings()
    
    # Test setting and getting values
    settings.set("test_value", "hello")
    assert settings.get("test_value") == "hello", "Failed to set/get value"
    
    # Test defaults
    assert settings.get("window_opacity") == 0.95, "Default value not applied"
    
    print("Settings tests passed!")


if __name__ == "__main__":
    print("Code Translator Test Suite")
    print("=" * 50)
    
    test_offline_translation()
    test_settings()
    
    print("\n" + "=" * 50)
    print("All tests completed!")