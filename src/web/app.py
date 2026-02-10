"""
FastAPI Web API for Code Translator
Run with: uvicorn src.web.app:app --reload
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import os

from translator.translator_engine import TranslatorEngine, TranslationProvider
from config.settings import Settings


# Initialize app
app = FastAPI(
    title="Code Translator API",
    description="AI-powered code translation between programming languages",
    version="1.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize translator
settings = Settings()
translator = TranslatorEngine(settings)


# Request/Response models
class TranslateRequest(BaseModel):
    """Translation request body"""

    code: str = Field(..., description="Source code to translate")
    source_lang: Optional[str] = Field(
        None, description="Source language (auto-detected if not provided)"
    )
    target_lang: str = Field(..., description="Target programming language")
    provider: Optional[str] = Field(
        None, description="AI provider (openai, anthropic, google, offline)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": "def hello():\n    print('Hello, World!')",
                "source_lang": "Python",
                "target_lang": "JavaScript",
                "provider": None,
            }
        }


class TranslateResponse(BaseModel):
    """Translation response"""

    translated_code: str
    source_lang: str
    target_lang: str
    confidence: float
    provider_used: str


class DetectRequest(BaseModel):
    """Language detection request"""

    code: str


class DetectResponse(BaseModel):
    """Language detection response"""

    detected_language: Optional[str]
    confidence: float


class LanguagesResponse(BaseModel):
    """Supported languages response"""

    languages: List[str]


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    providers_available: List[str]


class ExplainRequest(BaseModel):
    """Code explanation request"""

    code: str = Field(..., description="Source code to explain")
    language: Optional[str] = Field(None, description="Programming language")
    line_by_line: bool = Field(False, description="Add line-by-line comments")


class ExplainResponse(BaseModel):
    """Code explanation response"""

    explanation: str
    language: str


class AnalyzeRequest(BaseModel):
    """Code analysis request"""

    code: str = Field(..., description="Source code to analyze")
    language: Optional[str] = Field(None, description="Programming language")


class AnalyzeResponse(BaseModel):
    """Code analysis response"""

    language: str
    total_lines: int
    code_lines: int
    comment_lines: int
    functions_count: int
    average_complexity: float
    max_complexity: int
    overall_big_o: str
    suggestions: List[str]
    functions: List[dict]


class GenerateTestsRequest(BaseModel):
    """Test generation request"""

    code: str = Field(..., description="Source code to generate tests for")
    language: Optional[str] = Field(None, description="Programming language")
    framework: Optional[str] = Field(None, description="Test framework (pytest, jest, junit)")


class GenerateTestsResponse(BaseModel):
    """Test generation response"""

    tests: str
    framework: str
    language: str


class NotebookRequest(BaseModel):
    """Notebook translation request"""

    notebook_json: str = Field(..., description="Jupyter notebook JSON content")
    source_lang: str = Field("Python", description="Source programming language")
    target_lang: str = Field(..., description="Target programming language")


# API Routes
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health and available providers"""
    available_providers = []
    for provider in TranslationProvider:
        if provider in translator.providers:
            available_providers.append(provider.value)

    return HealthResponse(
        status="healthy",
        version="1.2.0",
        providers_available=available_providers,
    )


@app.get("/api/languages", response_model=LanguagesResponse, tags=["Languages"])
async def get_languages():
    """Get list of supported programming languages"""
    return LanguagesResponse(languages=TranslatorEngine.SUPPORTED_LANGUAGES)


@app.post("/api/detect", response_model=DetectResponse, tags=["Detection"])
async def detect_language(request: DetectRequest):
    """Auto-detect the programming language of code"""
    detected = translator.detect_language(request.code)
    return DetectResponse(
        detected_language=detected,
        confidence=0.85 if detected else 0.0,
    )


@app.post("/api/translate", response_model=TranslateResponse, tags=["Translation"])
async def translate_code(request: TranslateRequest):
    """Translate code between programming languages"""

    # Validate target language
    if request.target_lang not in TranslatorEngine.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported target language: {request.target_lang}. "
            f"Supported: {', '.join(TranslatorEngine.SUPPORTED_LANGUAGES)}",
        )

    # Detect or validate source language
    source_lang = request.source_lang
    if not source_lang:
        source_lang = translator.detect_language(request.code)
        if not source_lang:
            raise HTTPException(
                status_code=400,
                detail="Could not auto-detect source language. Please specify source_lang.",
            )

    if source_lang not in TranslatorEngine.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source language: {source_lang}. "
            f"Supported: {', '.join(TranslatorEngine.SUPPORTED_LANGUAGES)}",
        )

    # Determine provider
    provider = None
    provider_name = "auto"
    if request.provider:
        provider_map = {
            "openai": TranslationProvider.OPENAI,
            "anthropic": TranslationProvider.ANTHROPIC,
            "google": TranslationProvider.GOOGLE,
            "offline": TranslationProvider.OFFLINE,
        }
        if request.provider.lower() not in provider_map:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown provider: {request.provider}. "
                f"Available: {', '.join(provider_map.keys())}",
            )
        provider = provider_map[request.provider.lower()]
        provider_name = request.provider.lower()

    try:
        translated, confidence = translator.translate(
            request.code, source_lang, request.target_lang, provider
        )

        return TranslateResponse(
            translated_code=translated,
            source_lang=source_lang,
            target_lang=request.target_lang,
            confidence=confidence,
            provider_used=provider_name,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@app.post("/api/explain", response_model=ExplainResponse, tags=["Explanation"])
async def explain_code(request: ExplainRequest):
    """Explain code in plain English"""
    language = request.language
    if not language:
        language = translator.detect_language(request.code)
        if not language:
            language = "Unknown"

    try:
        explanation = translator.explain_code(
            request.code,
            language,
            line_by_line=request.line_by_line
        )
        return ExplainResponse(
            explanation=explanation,
            language=language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@app.post("/api/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_code(request: AnalyzeRequest):
    """Analyze code complexity"""
    from analyzer.complexity import ComplexityAnalyzer
    
    analyzer = ComplexityAnalyzer()
    
    language = request.language
    if not language:
        language = translator.detect_language(request.code)
        if not language:
            raise HTTPException(
                status_code=400,
                detail="Could not detect language. Please specify language."
            )

    try:
        analysis = analyzer.analyze(request.code, language)
        
        return AnalyzeResponse(
            language=analysis.language,
            total_lines=analysis.total_lines,
            code_lines=analysis.code_lines,
            comment_lines=analysis.comment_lines,
            functions_count=len(analysis.functions),
            average_complexity=analysis.average_complexity,
            max_complexity=analysis.max_complexity,
            overall_big_o=analysis.overall_big_o.value,
            suggestions=analysis.suggestions,
            functions=[
                {
                    "name": f.name,
                    "start_line": f.start_line,
                    "end_line": f.end_line,
                    "cyclomatic_complexity": f.cyclomatic_complexity,
                    "big_o": f.estimated_big_o.value,
                    "nesting_depth": f.nesting_depth,
                    "has_recursion": f.has_recursion,
                    "suggestions": f.suggestions
                }
                for f in analysis.functions
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/generate-tests", response_model=GenerateTestsResponse, tags=["Testing"])
async def generate_tests(request: GenerateTestsRequest):
    """Generate unit tests for code"""
    from translator.test_generator import TestGenerator, TestFramework
    
    generator = TestGenerator()
    
    language = request.language
    if not language:
        language = translator.detect_language(request.code)
        if not language:
            raise HTTPException(
                status_code=400,
                detail="Could not detect language. Please specify language."
            )

    framework = None
    framework_name = "auto"
    if request.framework:
        framework_map = {
            "pytest": TestFramework.PYTEST,
            "jest": TestFramework.JEST,
            "junit": TestFramework.JUNIT,
        }
        if request.framework.lower() not in framework_map:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown framework: {request.framework}. Available: pytest, jest, junit"
            )
        framework = framework_map[request.framework.lower()]
        framework_name = request.framework.lower()

    try:
        tests = generator.generate_tests(request.code, language, framework)
        
        # Determine framework name if auto
        if framework_name == "auto":
            if language == "Python":
                framework_name = "pytest"
            elif language in ["JavaScript", "TypeScript"]:
                framework_name = "jest"
            elif language in ["Java", "Kotlin"]:
                framework_name = "junit"
            else:
                framework_name = "pytest"
        
        return GenerateTestsResponse(
            tests=tests,
            framework=framework_name,
            language=language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@app.post("/api/notebook/translate", tags=["Notebook"])
async def translate_notebook(request: NotebookRequest):
    """Translate a Jupyter notebook"""
    from translator.notebook_handler import NotebookHandler
    
    handler = NotebookHandler(translator)
    
    if request.target_lang not in TranslatorEngine.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported target language: {request.target_lang}"
        )

    try:
        notebook = handler.parse_notebook(request.notebook_json)
        translated_nb, stats = handler.translate_notebook(
            notebook,
            request.source_lang,
            request.target_lang
        )
        
        return {
            "notebook": handler.notebook_to_json(translated_nb),
            "stats": {
                "total_cells": stats["total_cells"],
                "code_cells": stats["code_cells"],
                "translated_cells": stats["translated_cells"],
                "failed_cells": stats["failed_cells"],
                "errors": stats["errors"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notebook translation failed: {str(e)}")


# Serve static files and frontend
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def serve_frontend():
    """Serve the web frontend"""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text())
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Code Translator</title></head>
                <body>
                    <h1>Code Translator API</h1>
                    <p>Frontend not found. Visit <a href="/api/docs">/api/docs</a> for API documentation.</p>
                </body>
            </html>
            """
        )


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
