"""
Translation engine with AI integration and offline capabilities
"""

import asyncio
from typing import Dict, Optional, List, Tuple
from enum import Enum
import re
import json
from concurrent.futures import ThreadPoolExecutor

# AI providers
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from config.settings import Settings
from translator.offline_translator import OfflineTranslator
from utils.logger import get_logger
from utils.api_compatibility import OpenAICompatibilityWrapper


class TranslationProvider(Enum):
    """Available translation providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OFFLINE = "offline"


class TranslatorEngine:
    """Main translation engine with AI and offline capabilities"""

    SUPPORTED_LANGUAGES = [
        "Python",
        "JavaScript",
        "TypeScript",
        "Java",
        "Kotlin",
        "Swift",
        "C++",
        "Go",
        "Rust",
        "Ruby",
    ]

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(__name__)
        self.offline_translator = OfflineTranslator()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._cache: Dict[str, str] = {}
        self._init_providers()

    def _init_providers(self):
        """Initialize AI providers based on available API keys"""
        self.providers = {}

        # OpenAI
        if openai and self.settings.get("openai_api_key"):
            try:
                # Use compatibility wrapper for OpenAI
                openai_wrapper = OpenAICompatibilityWrapper(
                    api_key=self.settings.get("openai_api_key")
                )
                self.providers[TranslationProvider.OPENAI] = openai_wrapper
                self.logger.info("OpenAI provider initialized with compatibility wrapper")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI: {e}")

        # Anthropic
        if anthropic and self.settings.get("anthropic_api_key"):
            try:
                self.providers[TranslationProvider.ANTHROPIC] = anthropic.Anthropic(
                    api_key=self.settings.get("anthropic_api_key")
                )
                self.logger.info("Anthropic provider initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Anthropic: {e}")

        # Google
        if genai and self.settings.get("google_api_key"):
            try:
                genai.configure(api_key=self.settings.get("google_api_key"))
                self.providers[TranslationProvider.GOOGLE] = genai
                self.logger.info("Google provider initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Google: {e}")

        # Always have offline translator
        self.providers[TranslationProvider.OFFLINE] = self.offline_translator

    def reload_settings(self):
        """Reload settings and reinitialize providers"""
        self._init_providers()

    async def translate_async(
        self,
        code: str,
        source_lang: str,
        target_lang: str,
        provider: Optional[TranslationProvider] = None,
    ) -> Tuple[str, float]:
        """
        Translate code asynchronously
        Returns: (translated_code, confidence_score)
        """
        # Check cache
        cache_key = f"{source_lang}:{target_lang}:{hash(code)}"
        if cache_key in self._cache:
            return self._cache[cache_key], 1.0

        # Validate languages
        if source_lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported source language: {source_lang}")
        if target_lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported target language: {target_lang}")

        # Select provider
        if provider is None:
            provider = self._select_best_provider()

        try:
            result = await self._translate_with_provider(code, source_lang, target_lang, provider)

            # Cache result
            self._cache[cache_key] = result[0]
            if len(self._cache) > 100:  # Simple cache limit
                self._cache.pop(next(iter(self._cache)))

            return result

        except Exception as e:
            self.logger.error(f"Translation failed with {provider}: {e}")

            # Fallback to offline
            if provider != TranslationProvider.OFFLINE:
                self.logger.info("Falling back to offline translation")
                return await self._translate_with_provider(
                    code, source_lang, target_lang, TranslationProvider.OFFLINE
                )
            raise

    def translate(
        self,
        code: str,
        source_lang: str,
        target_lang: str,
        provider: Optional[TranslationProvider] = None,
    ) -> Tuple[str, float]:
        """Synchronous translation wrapper"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.translate_async(code, source_lang, target_lang, provider)
            )
        finally:
            loop.close()

    def _select_best_provider(self) -> TranslationProvider:
        """Select the best available provider"""
        # Priority order
        priority = [
            TranslationProvider.ANTHROPIC,
            TranslationProvider.OPENAI,
            TranslationProvider.GOOGLE,
            TranslationProvider.OFFLINE,
        ]

        for provider in priority:
            if provider in self.providers:
                return provider

        return TranslationProvider.OFFLINE

    async def _translate_with_provider(
        self, code: str, source_lang: str, target_lang: str, provider: TranslationProvider
    ) -> Tuple[str, float]:
        """Translate using specific provider"""

        if provider == TranslationProvider.OPENAI:
            return await self._translate_openai(code, source_lang, target_lang)
        elif provider == TranslationProvider.ANTHROPIC:
            return await self._translate_anthropic(code, source_lang, target_lang)
        elif provider == TranslationProvider.GOOGLE:
            return await self._translate_google(code, source_lang, target_lang)
        else:
            return self._translate_offline(code, source_lang, target_lang)

    async def _translate_openai(
        self, code: str, source_lang: str, target_lang: str
    ) -> Tuple[str, float]:
        """Translate using OpenAI"""
        wrapper = self.providers[TranslationProvider.OPENAI]

        prompt = f"""Translate this {source_lang} code to {target_lang}. 
        Maintain the logic and functionality while adapting to {target_lang} idioms and best practices.
        Do not include explanations, only provide the translated code.
        
        {source_lang} code:
        {code}
        """

        # Use the compatibility wrapper which handles both old and new API
        response = await asyncio.to_thread(
            wrapper.create_chat_completion_sync,
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert code translator."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        translated = response["content"].strip()
        confidence = 0.95  # High confidence for GPT-4

        return translated, confidence

    async def _translate_anthropic(
        self, code: str, source_lang: str, target_lang: str
    ) -> Tuple[str, float]:
        """Translate using Anthropic Claude"""
        client = self.providers[TranslationProvider.ANTHROPIC]

        prompt = f"""Translate this {source_lang} code to {target_lang}.
        
Requirements:
- Maintain the exact logic and functionality
- Use {target_lang} idioms and best practices
- Handle paradigm differences appropriately
- Include necessary imports/headers
- Preserve comments but translate them
- Output only the translated code, no explanations

{source_lang} code:
{code}
"""

        message = await asyncio.to_thread(
            client.messages.create,
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )

        translated = message.content[0].text.strip()
        confidence = 0.97  # Highest confidence for Claude

        return translated, confidence

    async def _translate_google(
        self, code: str, source_lang: str, target_lang: str
    ) -> Tuple[str, float]:
        """Translate using Google Gemini"""
        genai_client = self.providers[TranslationProvider.GOOGLE]

        model = genai_client.GenerativeModel("gemini-pro")

        prompt = f"""You are an expert code translator. Translate this {source_lang} code to {target_lang}.

Instructions:
- Preserve the exact functionality
- Use appropriate {target_lang} conventions
- Handle language-specific features properly
- Output only code, no explanations

{source_lang} code:
{code}
"""

        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 2000,
            },
        )

        translated = response.text.strip()
        confidence = 0.93  # Good confidence for Gemini

        return translated, confidence

    def _translate_offline(
        self, code: str, source_lang: str, target_lang: str
    ) -> Tuple[str, float]:
        """Translate using offline engine"""
        translated = self.offline_translator.translate(code, source_lang, target_lang)
        confidence = 0.7  # Lower confidence for offline
        return translated, confidence

    def detect_language(self, code: str) -> Optional[str]:
        """Attempt to detect the programming language"""
        # Strip the code to avoid issues with leading/trailing whitespace
        code = code.strip()
        if not code:
            return None

        patterns = {
            "Python": [
                # Function definitions
                r"^\s*def\s+\w+\s*\(",
                r"^\s*async\s+def\s+\w+\s*\(",
                # Class definitions
                r"^\s*class\s+\w+[\s\(:)]",
                # Import statements
                r"^\s*import\s+\w+",
                r"^\s*from\s+\w+\s+import",
                # Print statements (both Python 2 and 3)
                r"\bprint\s*\(",
                r"\bprint\s+[\"']",
                # Python-specific
                r"if\s+__name__\s*==\s*[\"']__main__[\"']",
                r"^\s*elif\s+",
                r"^\s*except[\s:]",
                # F-strings
                r"[fF][\"'][^\"']*\{[^}]*\}",
                # List comprehensions
                r"\[\s*\w+\s+for\s+\w+\s+in\s+",
                # Python decorators
                r"^\s*@\w+",
                # Triple quotes
                r"[\"']{3}",
            ],
            "JavaScript": [
                # Function declarations
                r"\bfunction\s+\w+\s*\(",
                r"\bfunction\s*\(",
                # Arrow functions
                r"=>\s*\{",
                r"=>\s*[^{]",
                # Variable declarations
                r"\b(const|let|var)\s+\w+\s*=",
                # Console methods
                r"\bconsole\.(log|error|warn|info)\s*\(",
                # Template literals
                r"`[^`]*\$\{[^}]*\}",
                # Common JS patterns
                r"\bexport\s+(default\s+)?",
                r"\bimport\s+.*\s+from\s+[\"']",
                r"\brequire\s*\([\"']",
                # Common methods
                r"\.(map|filter|reduce|forEach)\s*\(",
                # async/await
                r"\basync\s+function",
                r"\bawait\s+",
                # typeof operator
                r"\btypeof\s+\w+",
            ],
            "Java": [
                # Class declarations
                r"\b(public|private|protected)\s+(static\s+)?class\s+\w+",
                # Main method
                r"public\s+static\s+void\s+main\s*\(\s*String",
                # Import statements
                r"^\s*import\s+(static\s+)?java\.",
                r"^\s*package\s+[\w\.]+;",
                # Print statements
                r"System\.(out|err)\.(print|println)\s*\(",
                # Annotations
                r"^\s*@(Override|Deprecated|SuppressWarnings)",
                # Java-specific keywords
                r"\b(extends|implements)\s+\w+",
                r"\bfinal\s+\w+",
                r"\bnew\s+\w+\s*\(",
                # Generics
                r"<[A-Z]\w*>",
                # Exception handling
                r"\b(try|catch|finally)\s*\{",
                r"\bthrows\s+\w+",
            ],
            "C++": [
                # Include directives
                r"^\s*#include\s*[<\"]",
                # Namespace
                r"\busing\s+namespace\s+std\s*;",
                r"\bnamespace\s+\w+\s*\{",
                # Main function
                r"\bint\s+main\s*\(",
                # STL usage
                r"\bstd::(cout|cin|endl|string|vector)",
                # Stream operators
                r"(cout|cerr)\s*<<",
                r"cin\s*>>",
                # C++ specific
                r"\bclass\s+\w+\s*[\{:]",
                r"\btemplate\s*<",
                r"::\w+",
                r"\bvirtual\s+",
                r"\boperator\s*[+\-*/=<>]+\s*\(",
                # Pointers and references
                r"\w+\s*\*\s*\w+",
                r"\w+\s*&\s*\w+",
            ],
            "Go": [
                # Package declaration
                r"^\s*package\s+\w+",
                # Import statements
                r"^\s*import\s*\(",
                r"^\s*import\s+\"",
                # Function declarations
                r"\bfunc\s+(\(\w+\s+\*?\w+\)\s+)?\w+\s*\(",
                r"\bfunc\s+main\s*\(\s*\)",
                # Go-specific syntax
                r":=",
                # Common packages
                r"\bfmt\.(Print|Printf|Println)\s*\(",
                # Go keywords
                r"\b(defer|go|chan|select)\s+",
                # Error handling
                r"\bif\s+err\s*!=\s*nil\s*\{",
                # Structs
                r"\btype\s+\w+\s+struct\s*\{",
                # Interfaces
                r"\btype\s+\w+\s+interface\s*\{",
            ],
            "Rust": [
                # Function declarations
                r"\bfn\s+\w+\s*\(",
                r"\bfn\s+main\s*\(\s*\)",
                # Use statements
                r"^\s*use\s+\w+(::\w+)*;",
                # Print macros
                r"\b(println!|print!|eprintln!)\s*\(",
                # Variable declarations
                r"\blet\s+(mut\s+)?\w+",
                # Match expressions
                r"\bmatch\s+\w+\s*\{",
                # Rust-specific
                r"\bimpl\s+\w+",
                r"\bstruct\s+\w+",
                r"\benum\s+\w+",
                r"\btrait\s+\w+",
                # Ownership
                r"&mut\s+",
                r"\bBox<",
                r"\bOption<",
                r"\bResult<",
                # Attributes
                r"^\s*#\[derive",
            ],
            "Kotlin": [
                # Function declarations
                r"\bfun\s+\w+\s*\(",
                r"\bfun\s+main\s*\(",
                # Variable declarations
                r"\b(val|var)\s+\w+\s*(:\s*\w+)?\s*=",
                # Class declarations
                r"\b(data\s+)?class\s+\w+",
                r"\bobject\s+\w+",
                # Kotlin-specific
                r"\bwhen\s*\{",
                r"\bwhen\s*\([^)]+\)\s*\{",
                r"^\s*package\s+[\w\.]+",
                r"^\s*import\s+[\w\.]+",
                # Print statements
                r"\bprintln\s*\(",
                r"\bprint\s*\(",
                # Null safety
                r"\?\.",
                r"\?:",
                r"!!\.",
                # Coroutines
                r"\bsuspend\s+fun",
                r"\blaunch\s*\{",
                r"\basync\s*\{",
                # Extension functions
                r"\bfun\s+\w+\.\w+\s*\(",
            ],
            "Swift": [
                # Function declarations
                r"\bfunc\s+\w+\s*\(",
                # Variable declarations
                r"\b(let|var)\s+\w+\s*(:\s*\w+)?\s*=",
                # Class/Struct declarations
                r"\bclass\s+\w+",
                r"\bstruct\s+\w+",
                r"\benum\s+\w+",
                r"\bprotocol\s+\w+",
                # Swift-specific
                r"\bguard\s+",
                r"\bif\s+let\s+",
                r"\bswitch\s+\w+\s*\{",
                r"^\s*import\s+(Foundation|UIKit|SwiftUI)",
                # Print statements
                r"\bprint\s*\(",
                # Optionals
                r"\?\?",
                r"\w+\?",
                r"\w+!",
                # Closures
                r"\{\s*\([^)]*\)\s+in",
                r"\$\d+",
                # Type annotations
                r"->\s*\w+",
            ],
            "Ruby": [
                # Method definitions
                r"\bdef\s+\w+",
                r"\bend\b",
                # Class definitions
                r"\bclass\s+\w+(\s*<\s*\w+)?",
                r"\bmodule\s+\w+",
                # Ruby-specific
                r"\bputs\s+",
                r"\bp\s+",
                r"\brequire\s+[\"']",
                r"\brequire_relative\s+",
                # Blocks
                r"\bdo\s*\|[^|]*\|",
                r"\{\s*\|[^|]*\|\s*",
                r"\.each\s+do",
                r"\.map\s+do",
                # Symbols
                r":\w+",
                # Instance variables
                r"@\w+",
                # Heredoc
                r"<<[-~]?\w+",
                # Method chaining
                r"\.(select|reject|find|any\?|all\?)\s*[{\(]",
            ],
            "TypeScript": [
                # Type annotations
                r":\s*(string|number|boolean|any|void|never)\b",
                r":\s*\w+\[\]",
                r"<\w+>",
                # Interface/Type declarations
                r"\binterface\s+\w+",
                r"\btype\s+\w+\s*=",
                # TypeScript-specific keywords
                r"\bas\s+\w+",
                r"\breadonly\s+\w+",
                r"\bprivate\s+\w+",
                r"\bpublic\s+\w+",
                r"\bprotected\s+\w+",
                # Import/Export with types
                r"\bimport\s+type\s+",
                r"\bexport\s+type\s+",
                # Generic constraints
                r"<\w+\s+extends\s+\w+>",
                # Enum
                r"\benum\s+\w+",
                # Decorators (also JS but common in TS)
                r"^\s*@\w+",
            ],
        }

        scores = {}
        max_score = 0

        for lang, patterns_list in patterns.items():
            score = 0
            for pattern in patterns_list:
                # Use case-sensitive search for better accuracy
                if re.search(pattern, code, re.MULTILINE):
                    score += 1
            scores[lang] = score
            if score > max_score:
                max_score = score

        # Only return a match if we have reasonable confidence
        if max_score > 0:
            best_match = max(scores, key=scores.get)
            # For single pattern matches, be more careful about ambiguity
            if max_score == 1:
                # Check for Python print statement specifically
                if best_match == "Python" and re.search(r"\bprint\s*\(", code):
                    return "Python"
                # Only return if no other language has the same score
                sorted_scores = sorted(scores.values(), reverse=True)
                if len(sorted_scores) > 1 and sorted_scores[0] > sorted_scores[1]:
                    return best_match
            else:
                # Multiple patterns matched, more confident
                return best_match

        return None

    def explain_code(
        self,
        code: str,
        language: Optional[str] = None,
        line_by_line: bool = False,
        provider: Optional[TranslationProvider] = None,
    ) -> str:
        """
        Generate a plain English explanation of the code.

        Args:
            code: Source code to explain
            language: Programming language (auto-detected if not provided)
            line_by_line: If True, add comments for each line
            provider: AI provider to use

        Returns:
            Plain English explanation or commented code
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.explain_code_async(code, language, line_by_line, provider)
            )
        finally:
            loop.close()

    async def explain_code_async(
        self,
        code: str,
        language: Optional[str] = None,
        line_by_line: bool = False,
        provider: Optional[TranslationProvider] = None,
    ) -> str:
        """
        Async version of explain_code.
        """
        # Auto-detect language if not provided
        if not language:
            language = self.detect_language(code)
            if not language:
                language = "Unknown"

        # Select provider
        if provider is None:
            provider = self._select_best_provider()

        try:
            return await self._explain_with_provider(code, language, line_by_line, provider)
        except Exception as e:
            self.logger.error(f"Explanation failed with {provider}: {e}")

            # Fallback to offline explanation
            if provider != TranslationProvider.OFFLINE:
                return self._explain_offline(code, language, line_by_line)
            raise

    async def _explain_with_provider(
        self,
        code: str,
        language: str,
        line_by_line: bool,
        provider: TranslationProvider,
    ) -> str:
        """Explain code using specific provider"""
        if provider == TranslationProvider.OPENAI:
            return await self._explain_openai(code, language, line_by_line)
        elif provider == TranslationProvider.ANTHROPIC:
            return await self._explain_anthropic(code, language, line_by_line)
        elif provider == TranslationProvider.GOOGLE:
            return await self._explain_google(code, language, line_by_line)
        else:
            return self._explain_offline(code, language, line_by_line)

    async def _explain_openai(self, code: str, language: str, line_by_line: bool) -> str:
        """Explain code using OpenAI"""
        wrapper = self.providers.get(TranslationProvider.OPENAI)
        if not wrapper:
            return self._explain_offline(code, language, line_by_line)

        if line_by_line:
            prompt = f"""Add detailed inline comments to this {language} code explaining what each line does.
Keep the original code and add comments above or inline with each significant line.

{language} code:
{code}
"""
        else:
            prompt = f"""Explain this {language} code in plain English. 
Describe:
1. What the code does overall
2. The main components/functions
3. The flow of execution
4. Any important patterns or techniques used

{language} code:
{code}
"""

        response = await asyncio.to_thread(
            wrapper.create_chat_completion_sync,
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert code explainer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        return response["content"].strip()

    async def _explain_anthropic(self, code: str, language: str, line_by_line: bool) -> str:
        """Explain code using Anthropic Claude"""
        client = self.providers.get(TranslationProvider.ANTHROPIC)
        if not client:
            return self._explain_offline(code, language, line_by_line)

        if line_by_line:
            prompt = f"""Add detailed inline comments to this {language} code.
For each significant line, add a comment explaining what it does and why.
Preserve the original code structure.

{language} code:
{code}
"""
        else:
            prompt = f"""Provide a comprehensive explanation of this {language} code.

Include:
1. Overall purpose and functionality
2. Description of each function/class
3. Data flow and control flow
4. Key algorithms or patterns used
5. Any potential issues or improvements

{language} code:
{code}
"""

        message = await asyncio.to_thread(
            client.messages.create,
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text.strip()

    async def _explain_google(self, code: str, language: str, line_by_line: bool) -> str:
        """Explain code using Google Gemini"""
        genai_client = self.providers.get(TranslationProvider.GOOGLE)
        if not genai_client:
            return self._explain_offline(code, language, line_by_line)

        model = genai_client.GenerativeModel("gemini-pro")

        if line_by_line:
            prompt = f"""Add inline comments to this {language} code explaining each line.
Keep all original code and add explanatory comments.

{language} code:
{code}
"""
        else:
            prompt = f"""Explain this {language} code in detail.
Describe what it does, how it works, and any important patterns.

{language} code:
{code}
"""

        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 2000,
            },
        )

        return response.text.strip()

    def _explain_offline(self, code: str, language: str, line_by_line: bool) -> str:
        """Generate basic explanation without AI"""
        lines = code.split('\n')

        if line_by_line:
            # Add basic comments based on patterns
            commented_lines = []
            for line in lines:
                stripped = line.strip()
                comment = self._get_line_comment(stripped, language)
                if comment:
                    comment_char = "#" if language == "Python" else "//"
                    commented_lines.append(f"{comment_char} {comment}")
                commented_lines.append(line)
            return '\n'.join(commented_lines)
        else:
            # Generate basic summary
            return self._generate_basic_summary(code, language)

    def _get_line_comment(self, line: str, language: str) -> Optional[str]:
        """Generate a comment for a line of code"""
        patterns = [
            (r'^def\s+(\w+)', 'Define function: {}'),
            (r'^class\s+(\w+)', 'Define class: {}'),
            (r'^import\s+(\w+)', 'Import module: {}'),
            (r'^from\s+(\w+)', 'Import from module: {}'),
            (r'^if\s+', 'Conditional check'),
            (r'^for\s+', 'Loop iteration'),
            (r'^while\s+', 'While loop'),
            (r'^return\s+', 'Return value'),
            (r'^try:', 'Begin error handling'),
            (r'^except', 'Handle exception'),
            (r'^function\s+(\w+)', 'Define function: {}'),
            (r'^const\s+(\w+)', 'Declare constant: {}'),
            (r'^let\s+(\w+)', 'Declare variable: {}'),
        ]

        for pattern, template in patterns:
            match = re.match(pattern, line)
            if match:
                if '{}' in template and match.groups():
                    return template.format(match.group(1))
                return template

        return None

    def _generate_basic_summary(self, code: str, language: str) -> str:
        """Generate a basic summary of the code"""
        summary_parts = [f"This is {language} code."]

        # Count functions
        func_patterns = {
            "Python": r'\bdef\s+(\w+)',
            "JavaScript": r'\bfunction\s+(\w+)',
            "Java": r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\(',
        }

        pattern = func_patterns.get(language, func_patterns["Python"])
        functions = re.findall(pattern, code)
        if functions:
            summary_parts.append(f"\nFunctions defined: {', '.join(functions[:5])}")
            if len(functions) > 5:
                summary_parts.append(f" (and {len(functions) - 5} more)")

        # Count classes
        classes = re.findall(r'\bclass\s+(\w+)', code)
        if classes:
            summary_parts.append(f"\nClasses defined: {', '.join(classes)}")

        # Detect common patterns
        if re.search(r'\.read\(|\.write\(|open\(', code):
            summary_parts.append("\nContains file I/O operations.")
        if re.search(r'requests\.|urllib|fetch\(|http', code, re.IGNORECASE):
            summary_parts.append("\nContains HTTP/network operations.")
        if re.search(r'SELECT|INSERT|UPDATE|DELETE|\.execute\(', code, re.IGNORECASE):
            summary_parts.append("\nContains database operations.")

        summary_parts.append("\n\nNote: For detailed explanations, configure an AI provider.")

        return ''.join(summary_parts)
