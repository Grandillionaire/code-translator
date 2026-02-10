# Code Translator API Reference

Complete API documentation for the Code Translator web service.

## Base URL

```
http://localhost:8000
```

For production deployments, use your configured domain.

## Authentication

Currently, the API does not require authentication. API key authentication is planned for future releases.

---

## Endpoints

### Health Check

Check API status and available providers.

```http
GET /api/health
```

#### Response

```json
{
  "status": "healthy",
  "version": "1.2.0",
  "providers_available": ["openai", "anthropic", "google", "offline"]
}
```

#### Example

```bash
curl http://localhost:8000/api/health
```

---

### List Languages

Get all supported programming languages.

```http
GET /api/languages
```

#### Response

```json
{
  "languages": [
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "Kotlin",
    "Swift",
    "C++",
    "Go",
    "Rust",
    "Ruby"
  ]
}
```

#### Example

```bash
curl http://localhost:8000/api/languages
```

---

### Detect Language

Auto-detect the programming language of a code snippet.

```http
POST /api/detect
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Source code to analyze |

#### Response

```json
{
  "detected_language": "Python",
  "confidence": 0.85
}
```

#### Example

```bash
curl -X POST http://localhost:8000/api/detect \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello():\n    print(\"Hello, World!\")"
  }'
```

---

### Translate Code

Translate code between programming languages.

```http
POST /api/translate
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Source code to translate |
| `source_lang` | string | No | Source language (auto-detected if not provided) |
| `target_lang` | string | Yes | Target language |
| `provider` | string | No | AI provider: `openai`, `anthropic`, `google`, `offline` |

#### Response

```json
{
  "translated_code": "function hello() {\n  console.log(\"Hello, World!\");\n}",
  "source_lang": "Python",
  "target_lang": "JavaScript",
  "confidence": 0.95,
  "provider_used": "anthropic"
}
```

#### Examples

**Basic Translation**
```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello():\n    print(\"Hello, World!\")",
    "source_lang": "Python",
    "target_lang": "JavaScript"
  }'
```

**With Auto-Detection**
```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "code": "console.log(\"Hello!\");",
    "target_lang": "Python"
  }'
```

**Specific Provider**
```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "code": "fn main() { println!(\"Hello\"); }",
    "source_lang": "Rust",
    "target_lang": "Go",
    "provider": "openai"
  }'
```

**Translate a File**
```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d "{
    \"code\": \"$(cat myfile.py)\",
    \"source_lang\": \"Python\",
    \"target_lang\": \"TypeScript\"
  }"
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid input (unsupported language, missing field) |
| `422` | Validation Error - Request body parsing failed |
| `500` | Internal Server Error - Translation failed |

### Common Errors

**Unsupported Language**
```json
{
  "detail": "Unsupported target language: Cobol. Supported: Python, JavaScript, TypeScript, Java, Kotlin, Swift, C++, Go, Rust, Ruby"
}
```

**Auto-Detection Failed**
```json
{
  "detail": "Could not auto-detect source language. Please specify source_lang."
}
```

**Unknown Provider**
```json
{
  "detail": "Unknown provider: azure. Available: openai, anthropic, google, offline"
}
```

---

## Rate Limiting

Currently no rate limiting is enforced. For production deployments, consider adding rate limiting via a reverse proxy (nginx, Traefik) or API gateway.

---

## OpenAPI Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

---

## SDK Examples

### Python

```python
import requests

API_URL = "http://localhost:8000"

def translate_code(code: str, source_lang: str, target_lang: str) -> dict:
    response = requests.post(
        f"{API_URL}/api/translate",
        json={
            "code": code,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
    )
    response.raise_for_status()
    return response.json()

# Usage
result = translate_code(
    code="print('Hello')",
    source_lang="Python",
    target_lang="JavaScript"
)
print(result["translated_code"])
```

### JavaScript / Node.js

```javascript
const API_URL = 'http://localhost:8000';

async function translateCode(code, sourceLang, targetLang) {
    const response = await fetch(`${API_URL}/api/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            code,
            source_lang: sourceLang,
            target_lang: targetLang
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
    }
    
    return response.json();
}

// Usage
translateCode("console.log('Hello')", "JavaScript", "Python")
    .then(result => console.log(result.translated_code))
    .catch(console.error);
```

### cURL One-Liners

```bash
# Quick translate
curl -sX POST localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"code":"print(1+1)","target_lang":"JavaScript"}' | jq .translated_code

# Check health
curl -s localhost:8000/api/health | jq

# List languages
curl -s localhost:8000/api/languages | jq .languages
```

---

## Webhooks (Coming Soon)

Future releases will support webhooks for:
- Translation completion notifications
- Provider availability changes
- Usage alerts
