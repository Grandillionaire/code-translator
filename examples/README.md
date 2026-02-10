# Code Translator Examples

This folder contains example code files demonstrating Code Translator's capabilities.

## Files

### `python_example.py`
A Python function demonstrating basic translation to JavaScript. Shows how Python-specific features like list comprehensions and f-strings are converted to their JavaScript equivalents.

### `javascript_example.js`
A JavaScript module showing translation to Python. Demonstrates handling of async/await, arrow functions, and JavaScript idioms.

### `complex_class.py`
An advanced OOP example with inheritance, decorators, and Python-specific patterns. Tests the translator's ability to handle paradigm differences.

## Usage

### CLI Translation
```bash
# Translate Python to JavaScript
python -m code_translator --from python --to javascript examples/python_example.py

# Translate with output file
python -m code_translator --from python --to typescript examples/python_example.py -o output.ts

# Translate JavaScript to Python
python -m code_translator --from javascript --to python examples/javascript_example.js
```

### API Translation
```bash
# Using curl
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "code": "$(cat examples/python_example.py)",
  "source_lang": "Python",
  "target_lang": "JavaScript"
}
EOF
```

### Python SDK
```python
from translator.translator_engine import TranslatorEngine
from config.settings import Settings

# Initialize
engine = TranslatorEngine(Settings())

# Read and translate
with open("examples/python_example.py") as f:
    code = f.read()

translated, confidence = engine.translate(code, "Python", "JavaScript")
print(f"Confidence: {confidence:.0%}")
print(translated)
```

## Expected Outputs

Each example includes comments showing the expected translation output for reference.
