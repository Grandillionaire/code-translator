# Code Translator Pre-commit Hooks

Integrate Code Translator into your development workflow with pre-commit hooks.

## Installation

### 1. Install pre-commit

```bash
pip install pre-commit
```

### 2. Add to your `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/your-org/code-translator
    rev: v1.2.0
    hooks:
      - id: code-translator-validate
        name: Validate Translations
        
      - id: code-translator-analyze
        name: Analyze Complexity
        args: ['--max-complexity', '15']
        
      - id: code-translator-sync
        name: Sync Translations
```

### 3. Install the hooks

```bash
pre-commit install
```

## Available Hooks

### code-translator-validate

Validates that code translations are consistent and complete.

**Checks:**
- No failed translation markers
- No incomplete translation markers (TODO, FIXME)
- Files are readable

**Usage:**
```yaml
- id: code-translator-validate
```

### code-translator-analyze

Analyzes code complexity and optionally fails if thresholds are exceeded.

**Options:**
- `--max-complexity`: Maximum cyclomatic complexity (default: 15)
- `--strict`: Fail on complexity issues

**Usage:**
```yaml
- id: code-translator-analyze
  args: ['--max-complexity', '10', '--strict']
```

### code-translator-sync

Automatically syncs translations when source files change.

**Configuration:**

Create a `.translation-config.json` file in your repository:

```json
{
  "mappings": [
    {
      "source": "src/python/*.py",
      "target": "src/javascript/*.js",
      "source_lang": "Python",
      "target_lang": "JavaScript"
    },
    {
      "source": "lib/*.py",
      "target": "lib-ts/*.ts",
      "source_lang": "Python",
      "target_lang": "TypeScript"
    }
  ]
}
```

## Example `.pre-commit-config.yaml`

```yaml
# See https://pre-commit.com for more information
repos:
  # Standard hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  # Code Translator hooks
  - repo: https://github.com/your-org/code-translator
    rev: v1.2.0
    hooks:
      # Validate all code translations
      - id: code-translator-validate
        files: \.(py|js|ts|java)$
        
      # Analyze complexity with strict mode
      - id: code-translator-analyze
        args: ['--max-complexity', '12', '--strict']
        files: \.py$
        
      # Auto-sync Python to TypeScript
      - id: code-translator-sync
        files: ^src/python/.*\.py$

  # Language-specific linters
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.(js|ts)$
```

## Local Development

To test hooks locally without committing:

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run code-translator-analyze --all-files

# Run on specific files
pre-commit run code-translator-validate --files src/main.py
```

## CI Integration

Add to your CI pipeline:

```yaml
# GitHub Actions
- name: Run pre-commit
  uses: pre-commit/action@v3.0.0
```

## Troubleshooting

### Hook not running on expected files

Check the `files` pattern in your config. The default pattern includes common code extensions.

### Complexity threshold too strict

Adjust `--max-complexity` or remove `--strict` to make it advisory only.

### Translation sync not working

Ensure `.translation-config.json` exists and has correct path patterns.

## License

MIT License - See [LICENSE](../LICENSE) for details.
