#!/usr/bin/env python3
"""
Test script to verify OpenAI API compatibility
Run this to ensure the compatibility layer works with your installed OpenAI version
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_openai_compatibility():
    """Test OpenAI compatibility layer"""
    print("Testing OpenAI API Compatibility...")
    print("="*50)
    
    # Check OpenAI installation
    from utils.api_compatibility import check_openai_compatibility
    
    compat_info = check_openai_compatibility()
    
    print(f"OpenAI Installed: {compat_info['installed']}")
    if compat_info['installed']:
        print(f"OpenAI Version: {compat_info['version']}")
        print(f"Using New API (>=1.0): {compat_info['is_new_version']}")
    else:
        print(f"Import Error: {compat_info['import_error']}")
        print("\nPlease install OpenAI: pip install openai>=0.27.0")
        return False
    
    # Test API key handling (with dummy key)
    print("\nTesting API wrapper initialization...")
    try:
        from utils.api_compatibility import OpenAICompatibilityWrapper
        
        # Use a dummy key for testing
        wrapper = OpenAICompatibilityWrapper("sk-dummy-test-key")
        print(f"✅ Wrapper initialized successfully")
        print(f"   Version: {wrapper.version}")
        print(f"   New API: {wrapper.is_new_version}")
        
    except Exception as e:
        print(f"❌ Error initializing wrapper: {e}")
        return False
    
    print("\n✅ OpenAI compatibility layer is working correctly!")
    print("\nNote: To test actual translations, add a real API key in the application settings.")
    
    return True

def test_translator_engine():
    """Test that translator engine can initialize with compatibility layer"""
    print("\nTesting Translator Engine initialization...")
    print("="*50)
    
    try:
        from config.settings import Settings
        from translator.translator_engine import TranslatorEngine
        
        # Create settings instance
        settings = Settings()
        
        # Create translator engine
        engine = TranslatorEngine(settings)
        
        print("✅ Translator Engine initialized successfully")
        print(f"   Available providers: {list(engine.providers.keys())}")
        
        # Test language detection
        test_code = "def hello():\n    print('Hello, World!')"
        detected_lang = engine.detect_language(test_code)
        print(f"   Language detection test: {detected_lang} (expected: Python)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Translator Engine: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Code Translator - OpenAI Compatibility Test")
    print("="*50)
    print()
    
    # Run tests
    openai_ok = test_openai_compatibility()
    print()
    
    if openai_ok:
        engine_ok = test_translator_engine()
    else:
        engine_ok = False
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary:")
    print(f"  OpenAI Compatibility: {'✅ PASS' if openai_ok else '❌ FAIL'}")
    print(f"  Translator Engine: {'✅ PASS' if engine_ok else '❌ FAIL'}")
    
    if openai_ok and engine_ok:
        print("\n✅ All tests passed! The application should work correctly.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    sys.exit(0 if (openai_ok and engine_ok) else 1)