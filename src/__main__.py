#!/usr/bin/env python3
"""
Code Translator CLI
Run with: python -m code_translator [options]
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from translator.translator_engine import TranslatorEngine
from config.settings import Settings


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for CLI"""
    parser = argparse.ArgumentParser(
        prog="code-translator",
        description="AI-powered code translation between programming languages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate a file
  python -m code_translator --from python --to javascript input.py

  # Translate with output to file
  python -m code_translator --from python --to java input.py -o output.java

  # Translate from stdin
  echo "print('hello')" | python -m code_translator --from python --to javascript

  # Auto-detect source language
  python -m code_translator --to rust input.py

  # List supported languages
  python -m code_translator --list-languages

Supported Languages:
  Python, JavaScript, TypeScript, Java, Kotlin, Swift, C++, Go, Rust, Ruby
        """,
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        type=str,
        help="Input file to translate (use - for stdin)",
    )

    parser.add_argument(
        "-f",
        "--from",
        dest="source_lang",
        type=str,
        help="Source programming language (auto-detected if not specified)",
    )

    parser.add_argument(
        "-t",
        "--to",
        dest="target_lang",
        type=str,
        required=False,
        help="Target programming language",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file (prints to stdout if not specified)",
    )

    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "anthropic", "google", "offline"],
        default=None,
        help="AI provider to use (default: best available)",
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use offline translation only (no API calls)",
    )

    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List all supported languages",
    )

    parser.add_argument(
        "--detect",
        action="store_true",
        help="Detect the language of the input code",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.2.0",
    )

    return parser


def read_input(input_file: Optional[str]) -> str:
    """Read input from file or stdin"""
    if input_file is None or input_file == "-":
        if sys.stdin.isatty():
            print("Enter code to translate (Ctrl+D to finish):", file=sys.stderr)
        return sys.stdin.read()
    else:
        path = Path(input_file)
        if not path.exists():
            print(f"Error: File not found: {input_file}", file=sys.stderr)
            sys.exit(1)
        return path.read_text()


def write_output(content: str, output_file: Optional[str]) -> None:
    """Write output to file or stdout"""
    if output_file:
        Path(output_file).write_text(content)
        print(f"Output written to: {output_file}", file=sys.stderr)
    else:
        print(content)


def main() -> int:
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # List languages
    if args.list_languages:
        print("Supported Languages:")
        print("-" * 40)
        for lang in TranslatorEngine.SUPPORTED_LANGUAGES:
            print(f"  • {lang}")
        return 0

    # Initialize settings and translator
    settings = Settings()
    translator = TranslatorEngine(settings)

    # Detect language mode
    if args.detect:
        if not args.input_file:
            print("Error: Input file required for language detection", file=sys.stderr)
            return 1
        code = read_input(args.input_file)
        detected = translator.detect_language(code)
        if detected:
            print(f"Detected language: {detected}")
            return 0
        else:
            print("Could not detect language", file=sys.stderr)
            return 1

    # Translation mode
    if not args.target_lang:
        parser.print_help()
        print("\nError: --to (target language) is required for translation", file=sys.stderr)
        return 1

    # Validate target language
    target_lang = args.target_lang.title()
    if target_lang == "Typescript":
        target_lang = "TypeScript"
    elif target_lang == "C++":
        target_lang = "C++"

    if target_lang not in TranslatorEngine.SUPPORTED_LANGUAGES:
        print(f"Error: Unsupported target language: {args.target_lang}", file=sys.stderr)
        print(
            f"Supported languages: {', '.join(TranslatorEngine.SUPPORTED_LANGUAGES)}",
            file=sys.stderr,
        )
        return 1

    # Read input code
    code = read_input(args.input_file)

    if not code.strip():
        print("Error: No input code provided", file=sys.stderr)
        return 1

    # Determine source language
    source_lang = args.source_lang
    if source_lang:
        source_lang = source_lang.title()
        if source_lang == "Typescript":
            source_lang = "TypeScript"
        elif source_lang == "C++":
            source_lang = "C++"
    else:
        # Auto-detect
        source_lang = translator.detect_language(code)
        if not source_lang:
            print(
                "Error: Could not auto-detect source language. Please specify with --from",
                file=sys.stderr,
            )
            return 1
        if args.verbose:
            print(f"Auto-detected source language: {source_lang}", file=sys.stderr)

    if source_lang not in TranslatorEngine.SUPPORTED_LANGUAGES:
        print(f"Error: Unsupported source language: {source_lang}", file=sys.stderr)
        print(
            f"Supported languages: {', '.join(TranslatorEngine.SUPPORTED_LANGUAGES)}",
            file=sys.stderr,
        )
        return 1

    # Determine provider
    provider = None
    if args.offline:
        from translator.translator_engine import TranslationProvider

        provider = TranslationProvider.OFFLINE
    elif args.provider:
        from translator.translator_engine import TranslationProvider

        provider_map = {
            "openai": TranslationProvider.OPENAI,
            "anthropic": TranslationProvider.ANTHROPIC,
            "google": TranslationProvider.GOOGLE,
            "offline": TranslationProvider.OFFLINE,
        }
        provider = provider_map[args.provider]

    # Translate
    if args.verbose:
        print(f"Translating from {source_lang} to {target_lang}...", file=sys.stderr)

    try:
        translated, confidence = translator.translate(code, source_lang, target_lang, provider)

        if args.verbose:
            print(f"Translation confidence: {confidence:.0%}", file=sys.stderr)

        write_output(translated, args.output)
        return 0

    except Exception as e:
        print(f"Error during translation: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
