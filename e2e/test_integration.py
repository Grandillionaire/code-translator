"""
Integration tests for Code Translator components
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTranslatorEngine:
    """Test TranslatorEngine integration"""

    @pytest.fixture
    def translator(self):
        """Create translator instance"""
        from src.config.settings import Settings
        from src.translator.translator_engine import TranslatorEngine
        
        settings = Settings()
        return TranslatorEngine(settings)

    def test_translate_and_detect_roundtrip(self, translator):
        """Test that translated code is detected as target language"""
        python_code = '''
def greet(name):
    message = f"Hello, {name}!"
    return message
'''
        # Translate Python to JavaScript
        translated, confidence = translator.translate(
            python_code, "Python", "JavaScript"
        )
        
        # Detect language of translated code
        detected = translator.detect_language(translated)
        
        assert detected == "JavaScript"
        assert confidence > 0

    def test_explain_detected_language(self, translator):
        """Test explaining code with auto-detected language"""
        code = '''
function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}
'''
        # Should auto-detect JavaScript
        explanation = translator.explain_code(code)
        
        assert len(explanation) > 0
        assert "JavaScript" in explanation or "function" in explanation.lower()


class TestComplexityAnalyzer:
    """Test ComplexityAnalyzer integration"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        from src.analyzer.complexity import ComplexityAnalyzer
        return ComplexityAnalyzer()

    def test_analyze_high_complexity(self, analyzer):
        """Test analyzing code with high complexity"""
        complex_code = '''
def process(data, config, options):
    if data:
        if config.enabled:
            if options.validate:
                for item in data:
                    if item.valid:
                        if item.type == "A":
                            handle_a(item)
                        elif item.type == "B":
                            handle_b(item)
                        else:
                            handle_other(item)
'''
        analysis = analyzer.analyze(complex_code, "Python")
        
        assert analysis.max_complexity > 5
        assert analysis.overall_big_o.value != "O(1)"
        assert len(analysis.suggestions) > 0

    def test_analyze_recursive_function(self, analyzer):
        """Test detecting recursion"""
        recursive_code = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''
        analysis = analyzer.analyze(recursive_code, "Python")
        
        recursive_funcs = [f for f in analysis.functions if f.has_recursion]
        assert len(recursive_funcs) > 0


class TestTestGenerator:
    """Test TestGenerator integration"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        from src.translator.test_generator import TestGenerator
        return TestGenerator()

    def test_generate_tests_for_class(self, generator):
        """Test generating tests for a class"""
        code = '''
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
'''
        tests = generator.generate_tests(code, "Python")
        
        assert "TestCalculator" in tests
        assert "test_add" in tests
        assert "test_subtract" in tests
        assert "test_multiply" in tests
        assert "@pytest.fixture" in tests

    def test_generate_tests_for_async(self, generator):
        """Test generating tests for async functions"""
        code = '''
async def fetch_data(url):
    return await make_request(url)
'''
        tests = generator.generate_tests(code, "Python")
        
        assert "pytest.mark.asyncio" in tests
        assert "async def test_" in tests


class TestNotebookHandler:
    """Test NotebookHandler integration"""

    @pytest.fixture
    def handler(self):
        """Create handler instance"""
        from src.translator.notebook_handler import NotebookHandler
        return NotebookHandler()

    def test_parse_and_serialize_roundtrip(self, handler):
        """Test parsing and serializing notebook"""
        notebook_json = '''
{
  "cells": [
    {
      "cell_type": "code",
      "source": ["print('hello')"],
      "metadata": {},
      "outputs": [],
      "execution_count": 1
    },
    {
      "cell_type": "markdown",
      "source": ["# Title"],
      "metadata": {}
    }
  ],
  "metadata": {},
  "nbformat": 4,
  "nbformat_minor": 5
}
'''
        notebook = handler.parse_notebook(notebook_json)
        serialized = handler.notebook_to_json(notebook)
        reparsed = handler.parse_notebook(serialized)
        
        assert len(reparsed.cells) == len(notebook.cells)
        assert reparsed.cells[0].cell_type == "code"
        assert reparsed.cells[1].cell_type == "markdown"

    def test_extract_code_cells(self, handler):
        """Test extracting code cells"""
        notebook_json = '''
{
  "cells": [
    {"cell_type": "code", "source": ["x = 1"], "metadata": {}, "outputs": [], "execution_count": 1},
    {"cell_type": "markdown", "source": ["# Note"], "metadata": {}},
    {"cell_type": "code", "source": ["y = 2"], "metadata": {}, "outputs": [], "execution_count": 2}
  ],
  "metadata": {},
  "nbformat": 4,
  "nbformat_minor": 5
}
'''
        notebook = handler.parse_notebook(notebook_json)
        code_cells = handler.extract_code_cells(notebook)
        
        assert len(code_cells) == 2
        assert "x = 1" in code_cells[0]
        assert "y = 2" in code_cells[1]


class TestPreCommitHook:
    """Test pre-commit hook functionality"""

    def test_validate_clean_file(self, tmp_path):
        """Test validating a clean translation"""
        from pre_commit_hook.code_translator_hook import get_file_language
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello(): print('world')")
        
        language = get_file_language(str(test_file))
        assert language == "Python"

    def test_validate_multiple_languages(self, tmp_path):
        """Test language detection for multiple file types"""
        from pre_commit_hook.code_translator_hook import get_file_language
        
        extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
        }
        
        for ext, expected_lang in extensions.items():
            test_file = tmp_path / f"test{ext}"
            test_file.write_text("// test")
            assert get_file_language(str(test_file)) == expected_lang


class TestEndToEndWorkflow:
    """Test complete workflows"""

    def test_full_translation_workflow(self):
        """Test complete translation workflow"""
        from src.config.settings import Settings
        from src.translator.translator_engine import TranslatorEngine
        from src.translator.test_generator import TestGenerator
        from src.analyzer.complexity import ComplexityAnalyzer
        
        # Original Python code
        python_code = '''
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
'''
        # Step 1: Analyze complexity
        analyzer = ComplexityAnalyzer()
        analysis = analyzer.analyze(python_code, "Python")
        
        assert analysis.overall_big_o.value == "O(log n)"
        
        # Step 2: Translate to JavaScript
        settings = Settings()
        translator = TranslatorEngine(settings)
        js_code, confidence = translator.translate(python_code, "Python", "JavaScript")
        
        assert "function" in js_code.lower() or "const" in js_code.lower()
        
        # Step 3: Generate tests for translated code
        generator = TestGenerator()
        tests = generator.generate_tests(js_code, "JavaScript")
        
        assert "test(" in tests
        
        # Step 4: Explain the code
        explanation = translator.explain_code(python_code, "Python")
        
        assert len(explanation) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
