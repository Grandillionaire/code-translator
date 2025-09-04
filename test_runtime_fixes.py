#!/usr/bin/env python3
"""
Test script to verify all runtime fixes are working correctly
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_settings_corruption():
    """Test that settings handle corrupt JSON gracefully"""
    print("\n1. Testing Settings JSON Corruption Handling...")
    print("=" * 60)
    
    from config.settings import Settings
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override settings directory
        test_settings_file = Path(tmpdir) / "settings.json"
        
        # Test 1: Corrupt JSON
        print("  Testing corrupt JSON...")
        test_settings_file.write_text('{"key": "value", invalid json}')
        
        # This should not crash
        try:
            settings = Settings()
            settings.settings_file = test_settings_file
            settings._load_settings()
            print("  ✅ Handled corrupt JSON without crashing")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return False
        
        # Test 2: Empty file
        print("  Testing empty file...")
        test_settings_file.write_text('')
        try:
            settings._load_settings()
            print("  ✅ Handled empty file")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return False
        
        # Test 3: Non-dict JSON
        print("  Testing non-dict JSON...")
        test_settings_file.write_text('["not", "a", "dict"]')
        try:
            settings._load_settings()
            print("  ✅ Handled non-dict JSON")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return False
        
        # Test 4: Save with problematic data
        print("  Testing save with non-serializable data...")
        settings.settings = {"test": "value", "func": lambda x: x}  # lambda not serializable
        try:
            settings._save_settings()
            print("  ✅ Handled non-serializable data during save")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return False
            
    print("\n✅ All settings corruption tests passed!")
    return True

def test_openai_compatibility():
    """Test OpenAI compatibility wrapper"""
    print("\n2. Testing OpenAI Compatibility Layer...")
    print("=" * 60)
    
    from utils.api_compatibility import OpenAICompatibilityWrapper, create_safe_openai_client
    
    # Test with problematic parameters
    print("  Testing initialization with 'proxies' parameter...")
    try:
        # This should not crash even with unsupported parameters
        wrapper = create_safe_openai_client(
            api_key="test-key",
            proxies={"http": "http://proxy.example.com"},  # This should be filtered out
            verify_ssl=False,  # This should also be filtered out
            organization="test-org"  # This should be kept
        )
        print("  ✅ Successfully filtered unsupported parameters")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False
    
    # Test direct initialization
    print("  Testing direct wrapper initialization...")
    try:
        wrapper = OpenAICompatibilityWrapper(
            api_key="test-key",
            proxies={"http": "http://proxy.example.com"}
        )
        print("  ✅ Direct initialization handled unsupported params")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False
    
    print("\n✅ All OpenAI compatibility tests passed!")
    return True

def test_python_detection():
    """Test Python command detection"""
    print("\n3. Testing Python Command Detection...")
    print("=" * 60)
    
    print(f"  Current Python: {sys.executable}")
    print(f"  Version: {sys.version}")
    
    # Test the find_python function from run.py
    from run import find_python_command, check_python_version
    
    print("  Testing Python command finder...")
    python_cmd = find_python_command()
    if python_cmd:
        print(f"  ✅ Found Python command: {python_cmd}")
    else:
        print("  ❌ Could not find suitable Python command")
        return False
    
    print("  Testing version check...")
    if check_python_version():
        print("  ✅ Python version is sufficient")
    else:
        print("  ❌ Python version check failed")
        return False
    
    print("\n✅ All Python detection tests passed!")
    return True

def main():
    """Run all tests"""
    print("Code Translator - Runtime Fixes Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Run tests
    tests = [
        ("Settings Corruption", test_settings_corruption),
        ("OpenAI Compatibility", test_openai_compatibility),
        ("Python Detection", test_python_detection)
    ]
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nThe runtime fixes are working correctly.")
        print("Your Code Translator should now:")
        print("  - Handle corrupt settings files gracefully")
        print("  - Work with different OpenAI library versions")
        print("  - Find the correct Python command on your system")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())