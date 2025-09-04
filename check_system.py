#!/usr/bin/env python3
"""
System requirements checker for Code Translator
Uses the comprehensive dependency checker for detailed analysis
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from utils.dependency_checker import check_dependencies, DependencyChecker
except ImportError:
    # Fallback if dependency checker can't be imported
    print("Code Translator - System Requirements Check")
    print("=" * 50)
    print(f"\n✓ Python Version: {sys.version.split()[0]}")
    print(f"  Executable: {sys.executable}")
    
    if sys.version_info < (3, 8):
        print("  ❌ ERROR: Python 3.8 or newer required!")
        print("  Download from: https://www.python.org/downloads/")
        sys.exit(1)
    
    print("\n❌ ERROR: Cannot import dependency checker")
    print("This might mean core files are missing or Python path is incorrect")
    print("\nTry running one of these commands:")
    print(f"  {sys.executable} -m pip install -r requirements.txt")
    
    # Suggest alternative commands
    if os.name != 'nt':  # Unix-like systems
        print("  python3 -m pip install -r requirements.txt")
        print("  pip3 install -r requirements.txt")
    else:  # Windows
        print("  python -m pip install -r requirements.txt")
        print("  pip install -r requirements.txt")
    
    sys.exit(1)

# Run comprehensive dependency check
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check Code Translator system requirements",
        epilog="For detailed setup instructions, see INSTALLATION.md"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed information about each dependency'
    )
    parser.add_argument(
        '-s', '--save',
        help='Save detailed report to specified file'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Show commands to fix missing dependencies'
    )
    
    args = parser.parse_args()
    
    # Run the check
    save_path = Path(args.save) if args.save else None
    report = DependencyChecker.check_all_dependencies()
    
    # Print the report
    DependencyChecker.print_report(report, verbose=args.verbose)
    
    # Save report if requested
    if save_path:
        DependencyChecker.save_report(report, save_path)
        print(f"\nDetailed report saved to: {save_path}")
    
    # Show fix commands if requested
    if args.fix and report['missing_packages']:
        print("\n" + "="*60)
        print("FIX COMMANDS:")
        print("="*60)
        
        cmd = DependencyChecker.generate_install_command(report['missing_packages'])
        print(f"\n1. Install missing packages:\n   {cmd}")
        
        if report['incompatible_packages']:
            print("\n2. Upgrade incompatible packages:")
            for pkg in report['incompatible_packages']:
                print(f"   pip install --upgrade {pkg['package']}>={pkg['required']}")
    
    # Exit with appropriate code
    success = report['all_core_satisfied']
    sys.exit(0 if success else 1)