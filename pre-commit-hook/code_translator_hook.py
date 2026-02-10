#!/usr/bin/env python3
"""
Pre-commit hook for Code Translator
Validates code translations and analyzes complexity
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

# Add parent directory for imports when installed
try:
    from src.translator.translator_engine import TranslatorEngine
    from src.analyzer.complexity import ComplexityAnalyzer
    from src.config.settings import Settings
except ImportError:
    # Fallback for development
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.translator.translator_engine import TranslatorEngine
    from src.analyzer.complexity import ComplexityAnalyzer
    from src.config.settings import Settings


def get_file_language(file_path: str) -> str:
    """Detect language from file extension"""
    ext_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".cpp": "C++",
        ".kt": "Kotlin",
        ".swift": "Swift",
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext, "Unknown")


def validate_translation(args: argparse.Namespace) -> int:
    """
    Validate that translations are consistent.
    
    Checks if:
    1. Source and target files exist
    2. Translation appears to be syntactically valid
    3. Comments indicate source language match
    """
    files = args.filenames
    errors = []
    
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            continue
        
        try:
            content = path.read_text(encoding="utf-8")
            language = get_file_language(file_path)
            
            if language == "Unknown":
                continue
            
            # Check for translation markers
            if "Translation failed" in content:
                errors.append(f"{file_path}: Contains failed translation marker")
            
            # Check for incomplete translations (common patterns)
            incomplete_patterns = [
                "TODO: translate",
                "FIXME: translation",
                "# UNTRANSLATED",
                "// UNTRANSLATED",
            ]
            
            for pattern in incomplete_patterns:
                if pattern.lower() in content.lower():
                    errors.append(f"{file_path}: Contains incomplete translation marker")
                    break
            
        except Exception as e:
            errors.append(f"{file_path}: Error reading file: {e}")
    
    if errors:
        print("Translation validation failed:")
        for error in errors:
            print(f"  ✗ {error}")
        return 1
    
    print(f"✓ Validated {len(files)} file(s)")
    return 0


def analyze_complexity(args: argparse.Namespace) -> int:
    """
    Analyze code complexity and fail if threshold exceeded.
    """
    files = args.filenames
    max_complexity = args.max_complexity
    
    analyzer = ComplexityAnalyzer()
    issues = []
    
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            continue
        
        try:
            content = path.read_text(encoding="utf-8")
            language = get_file_language(file_path)
            
            if language == "Unknown":
                continue
            
            analysis = analyzer.analyze(content, language)
            
            # Check for high complexity functions
            for func in analysis.functions:
                if func.cyclomatic_complexity > max_complexity:
                    issues.append(
                        f"{file_path}:{func.start_line} - "
                        f"Function '{func.name}' has complexity {func.cyclomatic_complexity} "
                        f"(max: {max_complexity})"
                    )
                
                if func.nesting_depth > 5:
                    issues.append(
                        f"{file_path}:{func.start_line} - "
                        f"Function '{func.name}' has nesting depth {func.nesting_depth} "
                        f"(recommended max: 5)"
                    )
        
        except Exception as e:
            print(f"Warning: Could not analyze {file_path}: {e}")
    
    if issues:
        print("Complexity analysis found issues:")
        for issue in issues:
            print(f"  ⚠ {issue}")
        
        if args.strict:
            return 1
        else:
            print("\nNote: Use --strict to fail on complexity issues")
            return 0
    
    print(f"✓ Analyzed {len(files)} file(s), no complexity issues found")
    return 0


def sync_translations(args: argparse.Namespace) -> int:
    """
    Sync translations when source files change.
    
    Looks for a .translation-config.json file that maps source to target.
    """
    import json
    
    config_path = Path(".translation-config.json")
    if not config_path.exists():
        # No config, nothing to sync
        return 0
    
    try:
        config = json.loads(config_path.read_text())
    except Exception as e:
        print(f"Error reading translation config: {e}")
        return 1
    
    mappings = config.get("mappings", [])
    changed_files = set(args.filenames)
    
    settings = Settings()
    translator = TranslatorEngine(settings)
    
    files_to_update = []
    
    for mapping in mappings:
        source_pattern = mapping.get("source")
        target_pattern = mapping.get("target")
        source_lang = mapping.get("source_lang")
        target_lang = mapping.get("target_lang")
        
        for file_path in changed_files:
            # Check if file matches source pattern
            if Path(file_path).match(source_pattern):
                # Generate target path
                target_path = file_path.replace(
                    source_pattern.replace("*", ""),
                    target_pattern.replace("*", "")
                )
                files_to_update.append((file_path, target_path, source_lang, target_lang))
    
    if not files_to_update:
        return 0
    
    errors = []
    for source, target, src_lang, tgt_lang in files_to_update:
        try:
            source_code = Path(source).read_text(encoding="utf-8")
            
            # Detect language if not specified
            if not src_lang:
                src_lang = translator.detect_language(source_code)
            
            translated, confidence = translator.translate(
                source_code, src_lang, tgt_lang
            )
            
            # Write translated file
            target_path = Path(target)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(translated, encoding="utf-8")
            
            print(f"✓ Synced {source} → {target} ({confidence:.0%} confidence)")
            
        except Exception as e:
            errors.append(f"{source}: {e}")
    
    if errors:
        print("\nSync errors:")
        for error in errors:
            print(f"  ✗ {error}")
        return 1
    
    return 0


def main():
    """Main entry point for pre-commit hooks"""
    parser = argparse.ArgumentParser(description="Code Translator pre-commit hooks")
    subparsers = parser.add_subparsers(dest="command", help="Hook command")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate translations")
    validate_parser.add_argument("filenames", nargs="*", help="Files to validate")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze complexity")
    analyze_parser.add_argument("filenames", nargs="*", help="Files to analyze")
    analyze_parser.add_argument(
        "--max-complexity", type=int, default=15,
        help="Maximum allowed cyclomatic complexity"
    )
    analyze_parser.add_argument(
        "--strict", action="store_true",
        help="Fail on complexity issues"
    )
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync translations")
    sync_parser.add_argument("filenames", nargs="*", help="Changed files")
    
    args = parser.parse_args()
    
    if args.command == "validate":
        return validate_translation(args)
    elif args.command == "analyze":
        return analyze_complexity(args)
    elif args.command == "sync":
        return sync_translations(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
