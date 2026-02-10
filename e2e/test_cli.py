"""
End-to-end tests for Code Translator CLI
"""

import subprocess
import sys
import tempfile
from pathlib import Path
import pytest


def run_cli(*args: str, input_text: str = None) -> subprocess.CompletedProcess:
    """Run the CLI with given arguments"""
    cmd = [sys.executable, "-m", "src"] + list(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        input=input_text,
        cwd=Path(__file__).parent.parent,
        timeout=30
    )


class TestCLIBasics:
    """Test basic CLI functionality"""

    def test_version(self):
        """Test --version flag"""
        result = run_cli("--version")
        assert result.returncode == 0
        assert "1.2.0" in result.stdout

    def test_help(self):
        """Test --help flag"""
        result = run_cli("--help")
        assert result.returncode == 0
        assert "code-translator" in result.stdout.lower()
        assert "--from" in result.stdout
        assert "--to" in result.stdout

    def test_list_languages(self):
        """Test --list-languages flag"""
        result = run_cli("--list-languages")
        assert result.returncode == 0
        assert "Python" in result.stdout
        assert "JavaScript" in result.stdout
        assert "TypeScript" in result.stdout


class TestCLITranslation:
    """Test CLI translation functionality"""

    def test_translate_python_to_javascript(self):
        """Test basic Python to JavaScript translation"""
        python_code = '''
def greet(name):
    return f"Hello, {name}!"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            f.flush()
            
            result = run_cli(
                "--from", "python",
                "--to", "javascript",
                "--offline",
                f.name
            )
            
            Path(f.name).unlink()
        
        assert result.returncode == 0
        # Should contain function-like syntax
        assert "function" in result.stdout.lower() or "=>" in result.stdout

    def test_translate_with_output_file(self):
        """Test translation with output file"""
        python_code = 'print("hello")'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.py"
            output_path = Path(tmpdir) / "output.js"
            
            input_path.write_text(python_code)
            
            result = run_cli(
                "--from", "python",
                "--to", "javascript",
                "--offline",
                "-o", str(output_path),
                str(input_path)
            )
            
            assert result.returncode == 0
            assert output_path.exists()
            content = output_path.read_text()
            assert len(content) > 0

    def test_translate_auto_detect(self):
        """Test translation with auto-detected source language"""
        python_code = '''
def add(a, b):
    return a + b

if __name__ == "__main__":
    print(add(1, 2))
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            f.flush()
            
            result = run_cli(
                "--to", "go",
                "--offline",
                "-v",
                f.name
            )
            
            Path(f.name).unlink()
        
        assert result.returncode == 0
        assert "Auto-detected" in result.stderr


class TestCLILanguageDetection:
    """Test CLI language detection"""

    def test_detect_python(self):
        """Test detecting Python code"""
        code = 'def hello(): print("world")'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            result = run_cli("--detect", f.name)
            Path(f.name).unlink()
        
        assert result.returncode == 0
        assert "Python" in result.stdout

    def test_detect_javascript(self):
        """Test detecting JavaScript code"""
        code = 'function hello() { console.log("world"); }'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            f.flush()
            
            result = run_cli("--detect", f.name)
            Path(f.name).unlink()
        
        assert result.returncode == 0
        assert "JavaScript" in result.stdout


class TestCLIExplain:
    """Test CLI explain functionality"""

    def test_explain_code(self):
        """Test explaining code"""
        code = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            result = run_cli("--explain", f.name)
            Path(f.name).unlink()
        
        assert result.returncode == 0
        # Should contain some explanation
        assert len(result.stdout) > 50

    def test_explain_lines(self):
        """Test line-by-line explanation"""
        code = '''
x = 10
y = 20
print(x + y)
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            result = run_cli("--explain-lines", f.name)
            Path(f.name).unlink()
        
        assert result.returncode == 0
        # Should contain comments
        assert "#" in result.stdout


class TestCLIAnalyze:
    """Test CLI analyze functionality"""

    def test_analyze_code(self):
        """Test code analysis"""
        code = '''
def complex_function(x):
    if x > 10:
        if x > 20:
            if x > 30:
                return "very high"
            return "high"
        return "medium"
    return "low"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            result = run_cli("--analyze", "--from", "python", f.name)
            Path(f.name).unlink()
        
        assert result.returncode == 0
        assert "complexity" in result.stdout.lower()


class TestCLIGenerateTests:
    """Test CLI test generation functionality"""

    def test_generate_pytest(self):
        """Test generating pytest tests"""
        code = '''
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            result = run_cli(
                "--generate-tests",
                "--test-framework", "pytest",
                f.name
            )
            Path(f.name).unlink()
        
        assert result.returncode == 0
        assert "import pytest" in result.stdout
        assert "def test_" in result.stdout

    def test_generate_jest(self):
        """Test generating Jest tests"""
        code = '''
function add(a, b) {
    return a + b;
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            f.flush()
            
            result = run_cli(
                "--generate-tests",
                "--test-framework", "jest",
                "--from", "javascript",
                f.name
            )
            Path(f.name).unlink()
        
        assert result.returncode == 0
        assert "test(" in result.stdout or "describe(" in result.stdout


class TestCLINotebook:
    """Test CLI notebook functionality"""

    def test_translate_notebook(self):
        """Test translating a Jupyter notebook"""
        notebook_json = '''
{
  "cells": [
    {
      "cell_type": "code",
      "source": ["def hello():\\n", "    print(\\"Hello, World!\\")"],
      "metadata": {},
      "outputs": [],
      "execution_count": 1
    },
    {
      "cell_type": "markdown",
      "source": ["# This is a title"],
      "metadata": {}
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            f.write(notebook_json)
            f.flush()
            
            result = run_cli(
                "--notebook",
                "--from", "python",
                "--to", "javascript",
                f.name
            )
            Path(f.name).unlink()
        
        assert result.returncode == 0
        # Should return valid JSON
        assert '"cells"' in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling"""

    def test_missing_target_language(self):
        """Test error when target language is missing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')")
            f.flush()
            
            result = run_cli(f.name)
            Path(f.name).unlink()
        
        assert result.returncode != 0
        assert "--to" in result.stderr or "target" in result.stderr.lower()

    def test_invalid_language(self):
        """Test error with invalid language"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')")
            f.flush()
            
            result = run_cli(
                "--from", "python",
                "--to", "cobol",
                f.name
            )
            Path(f.name).unlink()
        
        assert result.returncode != 0
        assert "unsupported" in result.stderr.lower()

    def test_file_not_found(self):
        """Test error when file doesn't exist"""
        result = run_cli(
            "--from", "python",
            "--to", "javascript",
            "/nonexistent/file.py"
        )
        
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
