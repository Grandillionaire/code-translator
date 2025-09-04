"""
Runtime dependency checker for Code Translator
Ensures all required dependencies are available and compatible
"""

import sys
import importlib
import importlib.metadata
import subprocess
import platform
from typing import Dict, List, Tuple, Optional, Any
import json
from pathlib import Path


class DependencyChecker:
    """Check and validate runtime dependencies"""
    
    CORE_DEPENDENCIES = {
        'PyQt6': {'min_version': '6.5.0', 'package': 'PyQt6'},
        'requests': {'min_version': '2.31.0', 'package': 'requests'},
        'cryptography': {'min_version': '41.0.0', 'package': 'cryptography'},
        'yaml': {'min_version': '6.0.1', 'package': 'pyyaml', 'import_name': 'yaml'},
        'pyperclip': {'min_version': '1.8.2', 'package': 'pyperclip'},
        'keyring': {'min_version': '24.2.0', 'package': 'keyring'}
    }
    
    AI_DEPENDENCIES = {
        'openai': {
            'min_version': '0.27.0',  # Support both old and new versions
            'package': 'openai',
            'optional': True
        },
        'anthropic': {
            'min_version': '0.7.0',
            'package': 'anthropic',
            'optional': True
        },
        'google.generativeai': {
            'min_version': '0.3.0',
            'package': 'google-generativeai',
            'import_name': 'google.generativeai',
            'optional': True
        }
    }
    
    @classmethod
    def check_python_version(cls) -> Tuple[bool, str]:
        """Check if Python version is compatible"""
        required = (3, 8)
        current = sys.version_info[:2]
        
        if current >= required:
            return True, f"Python {'.'.join(map(str, current))} (OK)"
        else:
            return False, f"Python {'.'.join(map(str, current))} (Required: {'.'.join(map(str, required))}+)"
    
    @classmethod
    def get_installed_version(cls, package_name: str) -> Optional[str]:
        """Get the installed version of a package"""
        try:
            return importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            return None
    
    @classmethod
    def compare_versions(cls, installed: str, required: str) -> bool:
        """Compare version strings"""
        def version_tuple(v):
            return tuple(map(int, (v.split("."))))
        
        try:
            return version_tuple(installed) >= version_tuple(required)
        except:
            return True  # If we can't parse, assume it's ok
    
    @classmethod
    def check_dependency(cls, import_name: str, info: Dict[str, Any]) -> Dict[str, Any]:
        """Check a single dependency"""
        package_name = info.get('package', import_name)
        actual_import = info.get('import_name', import_name)
        
        result = {
            'name': import_name,
            'package': package_name,
            'required_version': info.get('min_version', 'any'),
            'installed': False,
            'version': None,
            'compatible': False,
            'optional': info.get('optional', False),
            'error': None
        }
        
        try:
            # Try to import the module
            if '.' in actual_import:
                parts = actual_import.split('.')
                importlib.import_module('.'.join(parts[:-1]))
            else:
                importlib.import_module(actual_import)
            
            result['installed'] = True
            
            # Get version
            version = cls.get_installed_version(package_name)
            if version:
                result['version'] = version
                result['compatible'] = cls.compare_versions(
                    version, info.get('min_version', '0.0.0')
                )
            else:
                result['compatible'] = True  # If we can't get version, assume OK
                
        except ImportError as e:
            result['error'] = str(e)
            
        return result
    
    @classmethod
    def check_all_dependencies(cls) -> Dict[str, Any]:
        """Check all dependencies and return comprehensive report"""
        report = {
            'python': cls.check_python_version(),
            'core': {},
            'ai': {},
            'all_core_satisfied': True,
            'ai_providers_available': 0,
            'missing_packages': [],
            'incompatible_packages': [],
            'platform': platform.platform()
        }
        
        # Check core dependencies
        for dep_name, info in cls.CORE_DEPENDENCIES.items():
            result = cls.check_dependency(dep_name, info)
            report['core'][dep_name] = result
            
            if not result['installed']:
                report['all_core_satisfied'] = False
                report['missing_packages'].append(info['package'])
            elif not result['compatible']:
                report['incompatible_packages'].append({
                    'package': info['package'],
                    'installed': result['version'],
                    'required': info['min_version']
                })
        
        # Check AI dependencies
        for dep_name, info in cls.AI_DEPENDENCIES.items():
            result = cls.check_dependency(dep_name, info)
            report['ai'][dep_name] = result
            
            if result['installed'] and result['compatible']:
                report['ai_providers_available'] += 1
            elif not result['installed'] and not result['optional']:
                report['missing_packages'].append(info['package'])
        
        return report
    
    @classmethod
    def generate_install_command(cls, missing_packages: List[str]) -> str:
        """Generate pip install command for missing packages"""
        if not missing_packages:
            return ""
        
        pip_cmd = "pip3" if platform.system() != "Windows" else "pip"
        return f"{pip_cmd} install {' '.join(missing_packages)}"
    
    @classmethod
    def save_report(cls, report: Dict[str, Any], filepath: Path):
        """Save dependency report to file"""
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
    
    @classmethod
    def print_report(cls, report: Dict[str, Any], verbose: bool = False):
        """Print a formatted dependency report"""
        print("\n" + "="*60)
        print("Code Translator - Dependency Check Report")
        print("="*60)
        
        # Python version
        py_ok, py_msg = report['python']
        symbol = "✅" if py_ok else "❌"
        print(f"\n{symbol} Python: {py_msg}")
        
        # Core dependencies
        print("\nCore Dependencies:")
        for name, info in report['core'].items():
            symbol = "✅" if info['installed'] and info['compatible'] else "❌"
            version = info['version'] or 'not installed'
            print(f"  {symbol} {name}: {version} (required: {info['required_version']})")
            if verbose and info['error']:
                print(f"     Error: {info['error']}")
        
        # AI providers
        print("\nAI Providers (optional):")
        for name, info in report['ai'].items():
            if info['installed']:
                symbol = "✅" if info['compatible'] else "⚠️"
                version = info['version'] or 'unknown'
                print(f"  {symbol} {name}: {version}")
            else:
                print(f"  ⭕ {name}: not installed")
        
        # Summary
        print(f"\nAI Providers Available: {report['ai_providers_available']}")
        
        # Actions needed
        if report['missing_packages']:
            print("\n❌ Missing packages:")
            for pkg in report['missing_packages']:
                print(f"   - {pkg}")
            print(f"\nTo install: {cls.generate_install_command(report['missing_packages'])}")
        
        if report['incompatible_packages']:
            print("\n⚠️  Incompatible versions:")
            for pkg in report['incompatible_packages']:
                print(f"   - {pkg['package']}: {pkg['installed']} (need {pkg['required']}+)")
        
        if report['all_core_satisfied'] and report['ai_providers_available'] > 0:
            print("\n✅ System ready to run Code Translator!")
        elif report['all_core_satisfied']:
            print("\n⚠️  Core dependencies satisfied, but no AI providers installed.")
            print("   The app will work with offline translation only.")
        else:
            print("\n❌ Please install missing core dependencies first.")
        
        print("="*60)


def check_dependencies(verbose: bool = False, save_report_path: Optional[Path] = None):
    """Main function to check dependencies"""
    report = DependencyChecker.check_all_dependencies()
    
    DependencyChecker.print_report(report, verbose)
    
    if save_report_path:
        DependencyChecker.save_report(report, save_report_path)
        print(f"\nReport saved to: {save_report_path}")
    
    return report['all_core_satisfied']


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Code Translator dependencies")
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed information')
    parser.add_argument('-s', '--save', help='Save report to file')
    
    args = parser.parse_args()
    
    save_path = Path(args.save) if args.save else None
    success = check_dependencies(args.verbose, save_path)
    
    sys.exit(0 if success else 1)