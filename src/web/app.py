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
