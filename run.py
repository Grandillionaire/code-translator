#!/usr/bin/env python3
"""
Simple launcher for Code Translator
Handles different Python configurations robustly
"""

import subprocess
import sys
import os
import shutil
import platform

def find_python_command():
    """Find the best Python command to use"""
    # Use the current interpreter first
    current_python = sys.executable
    if current_python and os.path.exists(current_python):
        return current_python
    
    # Try common Python commands
    commands = ['python3', 'python']
    
    # Add version-specific commands
    for minor in range(12, 7, -1):  # 3.12 down to 3.8
        commands.append(f'python3.{minor}')
    
    # Find first available command
    for cmd in commands:
        if shutil.which(cmd):
            # Verify it's Python 3.8+
            try:
                result = subprocess.run(
                    [cmd, '-c', 'import sys; print(sys.version_info[:2])'],
                    capture_output=True, text=True, check=True
                )
                version = eval(result.stdout.strip())
                if version >= (3, 8):
                    return cmd
            except:
                continue
    
    return None

def check_python_version():
    """Check if Python version is sufficient"""
    if sys.version_info < (3, 8):
        print(f"Error: Python 3.8 or newer is required (you have {sys.version})")
        print("Please download from: https://www.python.org/downloads/")
        return False
    return True

def ensure_dependencies():
    """Check and install dependencies if needed"""
    try:
        import PyQt6
        return True
    except ImportError:
        print("PyQt6 not found. Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install dependencies.")
            print(f"Please run manually: {sys.executable} -m pip install -r requirements.txt")
            return False

if __name__ == "__main__":
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Verify we're in the right directory
    if not os.path.exists("src/main.py"):
        print("Error: Cannot find src/main.py")
        print(f"Current directory: {os.getcwd()}")
        print("Please run this script from the code-translator directory")
        sys.exit(1)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    print(f"Code Translator Launcher")
    print(f"Python: {sys.executable} ({platform.python_version()})")
    print(f"Platform: {platform.platform()}")
    
    # Ensure dependencies
    if not ensure_dependencies():
        sys.exit(1)
    
    # Launch the application
    print("\nLaunching Code Translator...")
    try:
        subprocess.run([sys.executable, "src/main.py"] + sys.argv[1:])
    except KeyboardInterrupt:
        print("\nCode Translator closed.")
    except Exception as e:
        print(f"Error launching application: {e}")
        sys.exit(1)