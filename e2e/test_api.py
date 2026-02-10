"""
End-to-end tests for Code Translator API
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create a test client for the API"""
    from src.web.app import app
    return TestClient(app)


class TestAPIHealth:
    """Test API health endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "providers_available" in data

    def test_get_languages(self, client):
        """Test languages endpoint"""
        response = client.get("/api/languages")
        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert "Python" in data["languages"]
        assert "JavaScript" in data["languages"]


class TestAPIDetection:
    """Test API language detection"""

    def test_detect_python(self, client):
        """Test detecting Python code"""
        response = client.post(
            "/api/detect",
            json={"code": "def hello(): print('world')"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["detected_language"] == "Python"
        assert data["confidence"] > 0

    def test_detect_javascript(self, client):
        """Test detecting JavaScript code"""
        response = client.post(
            "/api/detect",
            json={"code": "function hello() { console.log('world'); }"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["detected_language"] == "JavaScript"

    def test_detect_unknown(self, client):
        """Test with undetectable code"""
        response = client.post(
            "/api/detect",
            json={"code": "hello world"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] == 0


class TestAPITranslation:
    """Test API translation endpoints"""

    def test_translate_python_to_javascript(self, client):
        """Test basic translation"""
        response = client.post(
            "/api/translate",
            json={
                "code": "def add(a, b): return a + b",
                "source_lang": "Python",
                "target_lang": "JavaScript",
                "provider": "offline"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "translated_code" in data
        assert data["source_lang"] == "Python"
        assert data["target_lang"] == "JavaScript"
        assert data["confidence"] > 0

    def test_translate_with_auto_detect(self, client):
        """Test translation with auto-detection"""
        response = client.post(
            "/api/translate",
            json={
                "code": "def greet(name): return f'Hello, {name}'",
                "target_lang": "Go",
                "provider": "offline"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source_lang"] == "Python"

    def test_translate_invalid_language(self, client):
        """Test translation with invalid target language"""
        response = client.post(
            "/api/translate",
            json={
                "code": "print('hello')",
                "source_lang": "Python",
                "target_lang": "COBOL"
            }
        )
        assert response.status_code == 400
        assert "unsupported" in response.json()["detail"].lower()


class TestAPIExplanation:
    """Test API explanation endpoints"""

    def test_explain_code(self, client):
        """Test code explanation"""
        response = client.post(
            "/api/explain",
            json={
                "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
                "language": "Python",
                "line_by_line": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert len(data["explanation"]) > 0

    def test_explain_line_by_line(self, client):
        """Test line-by-line explanation"""
        response = client.post(
            "/api/explain",
            json={
                "code": "x = 10\ny = 20\nprint(x + y)",
                "language": "Python",
                "line_by_line": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "#" in data["explanation"]  # Should have comments


class TestAPIAnalysis:
    """Test API analysis endpoints"""

    def test_analyze_code(self, client):
        """Test code analysis"""
        response = client.post(
            "/api/analyze",
            json={
                "code": """
def complex_func(x, y, z):
    if x > 0:
        if y > 0:
            for i in range(z):
                print(i)
    return x + y + z
""",
                "language": "Python"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "Python"
        assert data["total_lines"] > 0
        assert data["functions_count"] >= 1
        assert "overall_big_o" in data

    def test_analyze_auto_detect(self, client):
        """Test analysis with language auto-detection"""
        response = client.post(
            "/api/analyze",
            json={
                "code": "function test() { for (let i = 0; i < 10; i++) { console.log(i); } }"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "JavaScript"


class TestAPITestGeneration:
    """Test API test generation endpoints"""

    def test_generate_pytest(self, client):
        """Test generating pytest tests"""
        response = client.post(
            "/api/generate-tests",
            json={
                "code": "def add(a, b): return a + b",
                "language": "Python",
                "framework": "pytest"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "tests" in data
        assert "pytest" in data["tests"]
        assert data["framework"] == "pytest"

    def test_generate_jest(self, client):
        """Test generating Jest tests"""
        response = client.post(
            "/api/generate-tests",
            json={
                "code": "function multiply(a, b) { return a * b; }",
                "language": "JavaScript",
                "framework": "jest"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "test(" in data["tests"]
        assert data["framework"] == "jest"

    def test_generate_auto_framework(self, client):
        """Test auto-selecting test framework"""
        response = client.post(
            "/api/generate-tests",
            json={
                "code": "public class Calc { public int add(int a, int b) { return a + b; } }",
                "language": "Java"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["framework"] == "junit"


class TestAPINotebook:
    """Test API notebook endpoints"""

    def test_translate_notebook(self, client):
        """Test translating a notebook"""
        notebook_json = '''
{
  "cells": [
    {
      "cell_type": "code",
      "source": ["x = 10\\n", "print(x)"],
      "metadata": {},
      "outputs": [],
      "execution_count": 1
    }
  ],
  "metadata": {},
  "nbformat": 4,
  "nbformat_minor": 5
}
'''
        response = client.post(
            "/api/notebook/translate",
            json={
                "notebook_json": notebook_json,
                "source_lang": "Python",
                "target_lang": "JavaScript"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "notebook" in data
        assert "stats" in data
        assert data["stats"]["total_cells"] >= 1


class TestAPIFrontend:
    """Test API frontend serving"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_api_docs(self, client):
        """Test API docs are available"""
        response = client.get("/api/docs")
        assert response.status_code == 200


class TestAPIErrorHandling:
    """Test API error handling"""

    def test_missing_required_field(self, client):
        """Test error with missing required field"""
        response = client.post(
            "/api/translate",
            json={"code": "print('hello')"}
        )
        assert response.status_code == 422  # Validation error

    def test_empty_code(self, client):
        """Test with empty code"""
        response = client.post(
            "/api/detect",
            json={"code": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] == 0

    def test_invalid_json(self, client):
        """Test with invalid JSON"""
        response = client.post(
            "/api/translate",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
