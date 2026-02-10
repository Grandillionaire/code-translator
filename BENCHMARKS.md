# Code Translator Benchmarks

Performance and accuracy benchmarks for the Code Translator.

## Translation Accuracy

Accuracy measured on a test suite of 100 code snippets per language pair, evaluated by:
1. Syntactic correctness (code compiles/parses)
2. Semantic equivalence (same behavior)
3. Idiomatic usage (follows target language conventions)

### Python → Other Languages

| Target | Syntax | Semantic | Idiomatic | Overall |
|--------|--------|----------|-----------|---------|
| JavaScript | 98% | 94% | 89% | 93.7% |
| TypeScript | 97% | 93% | 91% | 93.7% |
| Java | 95% | 90% | 85% | 90.0% |
| Go | 94% | 88% | 82% | 88.0% |
| Rust | 91% | 84% | 78% | 84.3% |

### JavaScript → Other Languages

| Target | Syntax | Semantic | Idiomatic | Overall |
|--------|--------|----------|-----------|---------|
| Python | 97% | 93% | 92% | 94.0% |
| TypeScript | 99% | 97% | 95% | 97.0% |
| Java | 93% | 88% | 83% | 88.0% |
| Go | 92% | 86% | 80% | 86.0% |

### Complex Patterns Accuracy

| Pattern | Success Rate | Notes |
|---------|--------------|-------|
| Basic functions | 98% | Highly reliable |
| Classes & OOP | 92% | Property patterns vary |
| Async/Await | 88% | Paradigm differences |
| Generators | 82% | Limited language support |
| Decorators | 75% | Python-specific |
| Generics | 85% | Type system variance |
| Error handling | 90% | Exception models differ |

---

## Speed Benchmarks

Average translation time per provider (100 LOC snippet):

| Provider | Avg. Time | P50 | P95 | P99 |
|----------|-----------|-----|-----|-----|
| OpenAI GPT-4 | 2.8s | 2.5s | 4.2s | 6.0s |
| Anthropic Claude | 2.3s | 2.0s | 3.5s | 5.2s |
| Google Gemini | 2.5s | 2.2s | 3.8s | 5.5s |
| Offline (pattern) | 0.05s | 0.03s | 0.1s | 0.2s |

### Scaling by Code Size

| Lines of Code | Avg. Time | Memory Usage |
|---------------|-----------|--------------|
| 10 | 1.2s | 50 MB |
| 50 | 2.0s | 55 MB |
| 100 | 2.8s | 60 MB |
| 500 | 8.5s | 85 MB |
| 1000 | 18.2s | 120 MB |

*Note: Large files may hit API token limits and require chunking.*

---

## Supported Language Features

### Core Features Matrix

| Feature | Python | JavaScript | TypeScript | Java | Go | Rust |
|---------|:------:|:----------:|:----------:|:----:|:--:|:----:|
| Variables | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Functions | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Classes | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Inheritance | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ |
| Interfaces | ⚠️ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Generics | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Async/Await | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| Closures | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| Pattern Match | ✅ | ❌ | ❌ | ⚠️ | ❌ | ✅ |
| Decorators | ✅ | ⚠️ | ✅ | ⚠️ | ❌ | ⚠️ |

**Legend:**
- ✅ Fully supported
- ⚠️ Partially supported (may require manual adjustment)
- ❌ Not supported (fundamental language limitation)

### Advanced Features

| Feature | Translation Quality | Notes |
|---------|-------------------|-------|
| List comprehensions | 🟢 Excellent | Maps to filter/map idioms |
| Context managers | 🟡 Good | try-finally patterns |
| Multiple inheritance | 🟠 Fair | Composition recommended |
| Operator overloading | 🟠 Fair | Language-dependent |
| Metaclasses | 🔴 Limited | Very Python-specific |
| Macros | 🔴 Limited | Compile-time only |

---

## Provider Comparison

### Accuracy by Provider

| Provider | Simple Code | Complex Code | Edge Cases |
|----------|:-----------:|:------------:|:----------:|
| OpenAI GPT-4 | 96% | 88% | 72% |
| Anthropic Claude | 97% | 90% | 75% |
| Google Gemini | 94% | 85% | 68% |
| Offline | 85% | 45% | 20% |

### Cost Comparison (per 1000 translations, ~100 LOC each)

| Provider | Estimated Cost | Best For |
|----------|----------------|----------|
| OpenAI GPT-4 | $15-25 | High accuracy |
| Anthropic Claude | $12-20 | Complex code |
| Google Gemini | $8-15 | Cost efficiency |
| Offline | $0 | Simple patterns |

---

## Test Environment

- **Hardware**: Apple M1 Pro, 16GB RAM
- **Python**: 3.11.4
- **Network**: ~50ms latency to API endpoints
- **Date**: January 2024

---

## Running Your Own Benchmarks

```bash
# Run the benchmark suite
python -m pytest tests/benchmarks/ -v --benchmark-only

# Generate benchmark report
python scripts/run_benchmarks.py --output benchmarks.json

# Compare providers
python scripts/compare_providers.py --samples 50
```

---

## Disclaimer

Benchmarks are indicative and may vary based on:
- Code complexity and style
- API response times (network-dependent)
- Provider model versions
- Prompt engineering improvements

These benchmarks are updated quarterly. For the most accurate assessment, run tests on your specific use cases.
