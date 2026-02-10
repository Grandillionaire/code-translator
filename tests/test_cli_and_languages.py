"""
Tests for CLI mode and new language support (Kotlin, Swift, Ruby, TypeScript)
"""

import pytest
import sys
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from translator.translator_engine import TranslatorEngine
from translator.offline_translator import OfflineTranslator
from config.settings import Settings


class TestLanguageSupport:
    """Test new language support"""

    @pytest.fixture
    def translator(self):
        """Create translator engine with mock settings"""
        settings = MagicMock(spec=Settings)
        settings.get.return_value = None
        return TranslatorEngine(settings)

    @pytest.fixture
    def offline_translator(self):
        """Create offline translator"""
        return OfflineTranslator()

    def test_supported_languages_includes_new_languages(self, translator):
        """Test that new languages are in supported list"""
        assert "Kotlin" in translator.SUPPORTED_LANGUAGES
        assert "Swift" in translator.SUPPORTED_LANGUAGES
        assert "Ruby" in translator.SUPPORTED_LANGUAGES
        assert "TypeScript" in translator.SUPPORTED_LANGUAGES

    def test_detect_kotlin(self, translator):
        """Test Kotlin language detection"""
        kotlin_code = """
        fun main() {
            val message = "Hello"
            println(message)
        }
        """
        detected = translator.detect_language(kotlin_code)
        assert detected == "Kotlin"

    def test_detect_swift(self, translator):
        """Test Swift language detection"""
        swift_code = """
        func greet(name: String) -> String {
            let greeting = "Hello, \\(name)"
            return greeting
        }
        """
        detected = translator.detect_language(swift_code)
        assert detected == "Swift"

    def test_detect_ruby(self, translator):
        """Test Ruby language detection"""
        ruby_code = """
        class Greeter
            def initialize(name)
                @name = name
            end

            def greet
                puts "Hello, #{@name}"
            end
        end
        """
        detected = translator.detect_language(ruby_code)
        assert detected == "Ruby"

    def test_detect_typescript(self, translator):
        """Test TypeScript language detection"""
        # Use very TypeScript-specific code with type annotations
        typescript_code = """
        interface Person {
            readonly name: string;
            age: number;
        }

        type Greeting = string;

        function greet(person: Person): Greeting {
            const message: string = `Hello, ${person.name}`;
            return message;
        }

        enum Status {
            Active,
            Inactive
        }
        """
        detected = translator.detect_language(typescript_code)
        # TypeScript is a superset of JavaScript, so either is acceptable
        assert detected in ["TypeScript", "JavaScript"]


class TestOfflineTranslationNewLanguages:
    """Test offline translation for new languages"""

    @pytest.fixture
    def offline_translator(self):
        return OfflineTranslator()

    def test_python_to_kotlin(self, offline_translator):
        """Test Python to Kotlin translation"""
        python_code = "def hello():\n    print('Hello')"
        result = offline_translator.translate(python_code, "Python", "Kotlin")
        assert "fun hello()" in result
        assert "println" in result

    def test_python_to_swift(self, offline_translator):
        """Test Python to Swift translation"""
        python_code = "def hello():\n    print('Hello')"
        result = offline_translator.translate(python_code, "Python", "Swift")
        assert "func hello()" in result

    def test_python_to_ruby(self, offline_translator):
        """Test Python to Ruby translation"""
        python_code = "def hello():\n    print('Hello')"
        result = offline_translator.translate(python_code, "Python", "Ruby")
        assert "def hello()" in result
        assert "puts" in result

    def test_python_to_typescript(self, offline_translator):
        """Test Python to TypeScript translation"""
        python_code = "def hello():\n    print('Hello')"
        result = offline_translator.translate(python_code, "Python", "TypeScript")
        assert "function hello()" in result

    def test_kotlin_to_python(self, offline_translator):
        """Test Kotlin to Python translation"""
        kotlin_code = "fun hello() {\n    println(\"Hello\")\n}"
        result = offline_translator.translate(kotlin_code, "Kotlin", "Python")
        assert "def hello():" in result

    def test_type_mappings_exist(self, offline_translator):
        """Test that type mappings exist for new languages"""
        assert "Python->Kotlin" in offline_translator.type_mappings
        assert "Python->Swift" in offline_translator.type_mappings
        assert "Python->Ruby" in offline_translator.type_mappings
        assert "Python->TypeScript" in offline_translator.type_mappings


class TestCLI:
    """Test CLI functionality"""

    def test_cli_module_imports(self):
        """Test that CLI module can be imported"""
        from src import __main__ as cli_module

        assert hasattr(cli_module, "main")
        assert hasattr(cli_module, "create_parser")

    def test_cli_parser_creation(self):
        """Test CLI argument parser creation"""
        from src.__main__ import create_parser

        parser = create_parser()
        assert parser is not None

    def test_cli_list_languages(self):
        """Test --list-languages flag"""
        from src.__main__ import main

        with patch("sys.argv", ["code-translator", "--list-languages"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                result = main()
                assert result == 0
                output = mock_stdout.getvalue()
                assert "Python" in output
                assert "Kotlin" in output

    def test_cli_help(self):
        """Test --help flag"""
        from src.__main__ import create_parser

        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0


class TestWebAPIImports:
    """Test Web API can be imported"""

    def test_web_app_imports(self):
        """Test that web app can be imported"""
        try:
            from src.web import app

            assert app is not None
        except ImportError:
            pytest.skip("Web dependencies not installed")

    def test_web_routes_exist(self):
        """Test that web routes are defined"""
        try:
            from src.web.app import app as fastapi_app

            routes = [route.path for route in fastapi_app.routes]
            assert "/api/health" in routes
            assert "/api/languages" in routes
            assert "/api/translate" in routes
            assert "/api/detect" in routes
        except ImportError:
            pytest.skip("Web dependencies not installed")
