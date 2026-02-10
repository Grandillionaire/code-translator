#!/usr/bin/env python3
"""
GitHub Action entrypoint for Code Translator
Translates files based on input configuration
"""

import os
import sys
import glob
import json
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, "/app")

from src.translator.translator_engine import TranslatorEngine, TranslationProvider
from src.config.settings import Settings


def get_input(name: str, default: str = "") -> str:
    """Get input from environment variable"""
    return os.environ.get(f"INPUT_{name.upper().replace('-', '_')}", default)


def set_output(name: str, value: str) -> None:
    """Set output for GitHub Actions"""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{name}={value}\n")


def add_summary(content: str) -> None:
    """Add content to GitHub Actions job summary"""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(content + "\n")


def get_extension_for_language(lang: str) -> str:
    """Get file extension for a programming language"""
    extensions = {
        "Python": ".py",
        "JavaScript": ".js",
        "TypeScript": ".ts",
        "Java": ".java",
        "Kotlin": ".kt",
        "Swift": ".swift",
        "C++": ".cpp",
        "Go": ".go",
        "Rust": ".rs",
        "Ruby": ".rb",
    }
    return extensions.get(lang, ".txt")


def main():
    """Main entrypoint"""
    print("🚀 Code Translator GitHub Action")
    print("=" * 50)

    # Get inputs
    source_lang = get_input("source-lang", "auto")
    target_lang = get_input("target-lang")
    files_pattern = get_input("files")
    output_dir = get_input("output-dir", "translated")
    provider = get_input("provider", "offline")
    fail_on_error = get_input("fail-on-error", "true").lower() == "true"
    generate_report = get_input("generate-report", "true").lower() == "true"

    # Validate inputs
    if not target_lang:
        print("❌ Error: target-lang is required")
        sys.exit(1)

    if not files_pattern:
        print("❌ Error: files pattern is required")
        sys.exit(1)

    # Initialize settings with API keys from environment
    settings = Settings()
    if get_input("openai-api-key"):
        settings.set("openai_api_key", get_input("openai-api-key"))
    if get_input("anthropic-api-key"):
        settings.set("anthropic_api_key", get_input("anthropic-api-key"))
    if get_input("google-api-key"):
        settings.set("google_api_key", get_input("google-api-key"))

    # Initialize translator
    translator = TranslatorEngine(settings)

    # Map provider string to enum
    provider_map = {
        "openai": TranslationProvider.OPENAI,
        "anthropic": TranslationProvider.ANTHROPIC,
        "google": TranslationProvider.GOOGLE,
        "offline": TranslationProvider.OFFLINE,
    }
    selected_provider = provider_map.get(provider.lower(), TranslationProvider.OFFLINE)

    # Find files to translate
    files = glob.glob(files_pattern, recursive=True)
    print(f"📁 Found {len(files)} files matching pattern: {files_pattern}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Translation results
    results: List[Dict[str, Any]] = []
    success_count = 0
    error_count = 0

    # Process each file
    for file_path in files:
        print(f"\n📄 Translating: {file_path}")
        try:
            # Read source code
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            # Detect source language if auto
            actual_source_lang = source_lang
            if source_lang.lower() == "auto":
                detected = translator.detect_language(code)
                if detected:
                    actual_source_lang = detected
                    print(f"   Detected language: {detected}")
                else:
                    print(f"   ⚠️ Could not detect language, skipping")
                    error_count += 1
                    results.append({
                        "file": file_path,
                        "status": "error",
                        "error": "Could not detect source language"
                    })
                    continue

            # Translate
            translated, confidence = translator.translate(
                code, actual_source_lang, target_lang, selected_provider
            )

            # Generate output filename
            source_file = Path(file_path)
            output_ext = get_extension_for_language(target_lang)
            output_file = output_path / f"{source_file.stem}{output_ext}"

            # Write translated code
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(translated)

            print(f"   ✅ Translated to {output_file} (confidence: {confidence:.0%})")
            success_count += 1
            results.append({
                "file": file_path,
                "output": str(output_file),
                "source_lang": actual_source_lang,
                "target_lang": target_lang,
                "confidence": confidence,
                "status": "success"
            })

        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_count += 1
            results.append({
                "file": file_path,
                "status": "error",
                "error": str(e)
            })

    # Set outputs
    translated_files = [r["output"] for r in results if r["status"] == "success"]
    set_output("translated-files", json.dumps(translated_files))
    set_output("success-count", str(success_count))
    set_output("error-count", str(error_count))

    # Generate report
    if generate_report:
        report = f"""
## 🔄 Code Translation Report

| Metric | Value |
|--------|-------|
| Files Processed | {len(files)} |
| Successful | {success_count} |
| Errors | {error_count} |
| Target Language | {target_lang} |
| Provider | {provider} |

### Results

| Source File | Status | Output | Confidence |
|-------------|--------|--------|------------|
"""
        for r in results:
            if r["status"] == "success":
                report += f"| {r['file']} | ✅ Success | {r['output']} | {r['confidence']:.0%} |\n"
            else:
                report += f"| {r['file']} | ❌ Error | - | {r.get('error', 'Unknown')} |\n"

        add_summary(report)

        # Save report file
        report_path = output_path / "translation-report.md"
        with open(report_path, "w") as f:
            f.write(report)
        set_output("report-path", str(report_path))

    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Summary: {success_count} succeeded, {error_count} failed")

    # Exit with error if any failures and fail_on_error is true
    if error_count > 0 and fail_on_error:
        print("❌ Exiting with error due to translation failures")
        sys.exit(1)

    print("✅ Translation complete!")


if __name__ == "__main__":
    main()
