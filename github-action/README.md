# Code Translator GitHub Action

Automatically translate code between programming languages in your CI/CD pipeline.

## Features

- 🔄 Translate code between 10+ languages
- 🤖 Multiple AI provider support (OpenAI, Anthropic, Google)
- 📁 Batch file processing with glob patterns
- 🔍 Auto-detect source language
- 📊 Detailed translation reports
- 💾 Offline mode for air-gapped environments

## Usage

### Basic Example

```yaml
name: Translate Code

on:
  push:
    paths:
      - 'src/**/*.py'

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Translate Python to JavaScript
        uses: your-org/code-translator-action@v1
        with:
          source-lang: Python
          target-lang: JavaScript
          files: 'src/**/*.py'
          output-dir: 'translated/js'
```

### With AI Provider

```yaml
- name: Translate with OpenAI
  uses: your-org/code-translator-action@v1
  with:
    target-lang: TypeScript
    files: 'lib/**/*.py'
    provider: openai
    openai-api-key: ${{ secrets.OPENAI_API_KEY }}
```

### Pull Request Translation

```yaml
name: Translate on PR

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Translate changed Python files
        uses: your-org/code-translator-action@v1
        id: translate
        with:
          source-lang: auto
          target-lang: Go
          files: 'src/**/*.py'
          output-dir: 'go-translations'

      - name: Upload translations
        uses: actions/upload-artifact@v4
        with:
          name: translated-code
          path: go-translations/
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `source-lang` | Source language (or "auto") | No | `auto` |
| `target-lang` | Target programming language | Yes | - |
| `files` | Glob pattern for source files | Yes | - |
| `output-dir` | Output directory | No | `translated` |
| `provider` | AI provider (openai, anthropic, google, offline) | No | `offline` |
| `openai-api-key` | OpenAI API key | No | - |
| `anthropic-api-key` | Anthropic API key | No | - |
| `google-api-key` | Google API key | No | - |
| `fail-on-error` | Fail if any translation errors | No | `true` |
| `generate-report` | Generate job summary report | No | `true` |

## Outputs

| Output | Description |
|--------|-------------|
| `translated-files` | JSON array of translated file paths |
| `success-count` | Number of successful translations |
| `error-count` | Number of failed translations |
| `report-path` | Path to the translation report |

## Supported Languages

- Python
- JavaScript
- TypeScript
- Java
- Kotlin
- Swift
- C++
- Go
- Rust
- Ruby

## Example Workflow: Multi-Language SDK Generation

```yaml
name: Generate Multi-Language SDK

on:
  release:
    types: [published]

jobs:
  generate-sdks:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        target: [JavaScript, TypeScript, Go, Rust, Java]

    steps:
      - uses: actions/checkout@v4

      - name: Translate to ${{ matrix.target }}
        uses: your-org/code-translator-action@v1
        with:
          source-lang: Python
          target-lang: ${{ matrix.target }}
          files: 'sdk/python/**/*.py'
          output-dir: 'sdk/${{ matrix.target }}'
          provider: anthropic
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Publish SDK
        run: |
          echo "Publishing ${{ matrix.target }} SDK..."
          # Add your publish logic here
```

## License

MIT License - See [LICENSE](../LICENSE) for details.
