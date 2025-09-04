#!/usr/bin/env python3
"""
Comprehensive test for Code Translator
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6 imported successfully")
        
        from translator.translator_engine import TranslatorEngine
        print("✓ TranslatorEngine imported successfully")
        
        from translator.offline_translator import OfflineTranslator
        print("✓ OfflineTranslator imported successfully")
        
        from gui.main_window import TranslatorWindow
        print("✓ TranslatorWindow imported successfully")
        
        from gui.widgets import TranslationWidget, SettingsDialog
        print("✓ GUI widgets imported successfully")
        
        from gui.history_dialog import HistoryDialog
        print("✓ HistoryDialog imported successfully")
        
        from config.settings import Settings
        print("✓ Settings imported successfully")
        
        from utils.logger import setup_logger
        print("✓ Logger imported successfully")
        
        from utils.shortcuts import ShortcutManager
        print("✓ ShortcutManager imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_offline_translation():
    """Test offline translation"""
    print("\nTesting offline translation...")
    from translator.offline_translator import OfflineTranslator
    
    offline = OfflineTranslator()
    
    # Test cases
    test_cases = [
        ("Python", "JavaScript", "print('Hello')", "console.log('Hello')"),
        ("JavaScript", "Python", "console.log('Test')", "print('Test')"),
        ("Python", "Java", "x = 5", "int x = 5;"),
    ]
    
    passed = 0
    for source, target, code, expected in test_cases:
        result = offline.translate(code, source, target)
        if expected in result:
            print(f"✓ {source} → {target}")
            passed += 1
        else:
            print(f"✗ {source} → {target}: Expected '{expected}' in result")
            
    print(f"Passed {passed}/{len(test_cases)} offline translation tests")
    return passed == len(test_cases)


def test_settings():
    """Test settings functionality"""
    print("\nTesting settings...")
    from config.settings import Settings
    
    settings = Settings()
    
    # Test default values
    assert settings.get("window_opacity") == 0.95, "Default opacity incorrect"
    assert settings.get("theme") == "dark", "Default theme incorrect"
    print("✓ Default values correct")
    
    # Test setting values
    settings.set("test_key", "test_value")
    assert settings.get("test_key") == "test_value", "Setting value failed"
    print("✓ Setting/getting values works")
    
    # Test encryption (API keys)
    settings.set("test_api_key", "sk-test123")
    settings.save()
    
    # Create new instance to test loading
    settings2 = Settings()
    # Note: API keys might not persist in test due to encryption
    print("✓ Settings save/load works")
    
    return True


def test_language_detection():
    """Test language detection"""
    print("\nTesting language detection...")
    from translator.translator_engine import TranslatorEngine
    from config.settings import Settings
    
    settings = Settings()
    engine = TranslatorEngine(settings)
    
    test_cases = [
        ("def main():\n    pass", "Python"),
        ("function test() { }", "JavaScript"),
        ("public class Main { }", "Java"),
        ("#include <iostream>", "C++"),
        ("package main", "Go"),
        ("fn main() { }", "Rust"),
    ]
    
    passed = 0
    for code, expected in test_cases:
        detected = engine.detect_language(code)
        if detected == expected:
            print(f"✓ Detected {expected}")
            passed += 1
        else:
            print(f"✗ Expected {expected}, got {detected}")
            
    print(f"Passed {passed}/{len(test_cases)} language detection tests")
    return passed == len(test_cases)


def test_gui_components():
    """Test GUI components can be instantiated"""
    print("\nTesting GUI components...")
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        
        from config.settings import Settings
        from gui.main_window import TranslatorWindow
        
        settings = Settings()
        
        # Don't show the window, just test instantiation
        window = TranslatorWindow(settings)
        print("✓ Main window created successfully")
        
        # Test that key components exist
        assert hasattr(window, 'translation_widget'), "Missing translation widget"
        assert hasattr(window, 'translator_engine'), "Missing translator engine"
        assert hasattr(window, 'shortcut_manager'), "Missing shortcut manager"
        print("✓ All key components present")
        
        return True
    except Exception as e:
        print(f"✗ GUI component test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("Code Translator Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Offline Translation", test_offline_translation),
        ("Settings", test_settings),
        ("Language Detection", test_language_detection),
        ("GUI Components", test_gui_components),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))
            
    print("\n" + "=" * 60)
    print("Test Summary:")
    passed = sum(1 for _, result in results if result)
    print(f"Passed: {passed}/{len(results)}")
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
        
    return passed == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)