"""
Custom widgets for the Code Translator application
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QSplitter,
    QDialog,
    QTabWidget,
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QMimeData, QUrl
from PyQt6.QtGui import (
    QFont,
    QTextCharFormat,
    QColor,
    QSyntaxHighlighter,
    QTextDocument,
    QDragEnterEvent,
    QDropEvent,
)
import re
from typing import Optional, Dict, List
import json
from datetime import datetime
import sys

from translator.translator_engine import TranslatorEngine
from config.settings import Settings


class CodeTextEdit(QTextEdit):
    """Custom text edit with drag & drop support for code files"""

    file_dropped = pyqtSignal(str)  # Signal emitted when file is dropped

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            # Check if any of the URLs are files we can handle
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    # Accept common code file extensions
                    if file_path.endswith((".py", ".js", ".java", ".cpp", ".go", ".rs", ".txt")):
                        event.acceptProposedAction()
                        return
        elif event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            self.setPlainText(content)
                            self.file_dropped.emit(file_path)
                            event.acceptProposedAction()
                            return
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to read file: {str(e)}")
        elif event.mimeData().hasText():
            # Handle text drop
            super().dropEvent(event)
        else:
            event.ignore()


class CodeHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for code"""

    def __init__(self, parent=None, language="Python"):
        super().__init__(parent)
        self.language = language
        self.setup_rules()

    def setup_rules(self):
        """Setup highlighting rules based on language"""
        self.rules = []

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        if self.language == "Python":
            keywords = [
                "def",
                "class",
                "import",
                "from",
                "as",
                "if",
                "else",
                "elif",
                "for",
                "while",
                "break",
                "continue",
                "return",
                "yield",
                "pass",
                "try",
                "except",
                "finally",
                "with",
                "lambda",
                "and",
                "or",
                "not",
                "in",
                "is",
                "None",
                "True",
                "False",
                "self",
            ]
        elif self.language == "JavaScript":
            keywords = [
                "function",
                "const",
                "let",
                "var",
                "if",
                "else",
                "for",
                "while",
                "do",
                "break",
                "continue",
                "return",
                "class",
                "extends",
                "new",
                "this",
                "super",
                "import",
                "export",
                "from",
                "async",
                "await",
                "try",
                "catch",
                "finally",
                "throw",
                "null",
                "undefined",
                "true",
                "false",
            ]
        else:
            keywords = []

        for keyword in keywords:
            pattern = r"\b" + keyword + r"\b"
            self.rules.append((pattern, keyword_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        self.rules.append((r'"[^"]*"', string_format))
        self.rules.append((r"'[^']*'", string_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        if self.language == "Python":
            self.rules.append((r"#.*$", comment_format))
        else:
            self.rules.append((r"//.*$", comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.rules.append((r"\b\d+\.?\d*\b", number_format))

    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text"""
        for pattern, format_style in self.rules:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format_style)


class TranslationWidget(QWidget):
    """Main translation widget with input/output areas"""

    translation_requested = pyqtSignal(str, str, str)  # source_lang, target_lang, code

    def __init__(self, translator: TranslatorEngine, settings: Settings):
        super().__init__()
        self.translator = translator
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        """Initialize the translation UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Language selection bar
        lang_bar = QHBoxLayout()

        # Source language
        lang_bar.addWidget(QLabel("From:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Auto-detect"] + TranslatorEngine.SUPPORTED_LANGUAGES)
        self.source_combo.currentTextChanged.connect(self.on_source_language_changed)
        lang_bar.addWidget(self.source_combo)

        # Swap button
        swap_btn = QPushButton("⇄")
        swap_btn.setFixedSize(30, 30)
        swap_btn.clicked.connect(self.swap_languages)
        lang_bar.addWidget(swap_btn)

        # Target language
        lang_bar.addWidget(QLabel("To:"))
        self.target_combo = QComboBox()
        self.target_combo.addItems(TranslatorEngine.SUPPORTED_LANGUAGES)
        self.target_combo.setCurrentText("JavaScript")
        self.target_combo.currentTextChanged.connect(self.on_target_language_changed)
        lang_bar.addWidget(self.target_combo)

        # Translate button
        self.translate_btn = QPushButton("Translate (Ctrl+Enter)")
        self.translate_btn.clicked.connect(self.translate_code)
        lang_bar.addWidget(self.translate_btn)

        # Favorite button
        self.favorite_btn = QPushButton("☆")
        self.favorite_btn.setFixedSize(30, 30)
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        lang_bar.addWidget(self.favorite_btn)

        # Paste button
        paste_btn = QPushButton("📋")
        paste_btn.setFixedSize(30, 30)
        paste_btn.setToolTip("Paste from clipboard")
        paste_btn.clicked.connect(self.paste_from_clipboard)
        lang_bar.addWidget(paste_btn)

        layout.addLayout(lang_bar)

        # Second row of buttons for advanced features
        advanced_bar = QHBoxLayout()
        
        # Explain button
        self.explain_btn = QPushButton("💡 Explain")
        self.explain_btn.setToolTip("Explain this code in plain English")
        self.explain_btn.clicked.connect(self.explain_code)
        advanced_bar.addWidget(self.explain_btn)
        
        # Generate Tests button
        self.generate_tests_btn = QPushButton("🧪 Generate Tests")
        self.generate_tests_btn.setToolTip("Generate unit tests for this code")
        self.generate_tests_btn.clicked.connect(self.generate_tests)
        advanced_bar.addWidget(self.generate_tests_btn)
        
        # Analyze button
        self.analyze_btn = QPushButton("📊 Analyze")
        self.analyze_btn.setToolTip("Analyze code complexity")
        self.analyze_btn.clicked.connect(self.analyze_code)
        advanced_bar.addWidget(self.analyze_btn)
        
        advanced_bar.addStretch()
        layout.addLayout(advanced_bar)

        # Code areas
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Input area
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)

        input_label = QLabel("Source Code")
        input_label.setStyleSheet("font-weight: bold; padding: 5px;")
        input_layout.addWidget(input_label)

        self.input_area = CodeTextEdit()
        self.input_area.setPlaceholderText("Paste or type your code here...")
        self.input_area.file_dropped.connect(self.on_file_dropped)
        # Use platform-appropriate monospace font
        font_family = (
            "Menlo"
            if sys.platform == "darwin"
            else "Consolas"
            if sys.platform == "win32"
            else "monospace"
        )
        self.input_area.setFont(QFont(font_family, 11))
        self.input_highlighter = CodeHighlighter(self.input_area.document())
        input_layout.addWidget(self.input_area)

        # Output area
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)

        output_header = QHBoxLayout()
        output_label = QLabel("Translated Code")
        output_label.setStyleSheet("font-weight: bold; padding: 5px;")
        output_header.addWidget(output_label)

        self.confidence_label = QLabel("")
        self.confidence_label.setStyleSheet("color: #4CAF50; padding: 5px;")
        output_header.addWidget(self.confidence_label)
        output_header.addStretch()

        # Copy button
        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(self.copy_output)
        output_header.addWidget(copy_btn)

        output_layout.addLayout(output_header)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont(font_family, 11))
        self.output_highlighter = CodeHighlighter(self.output_area.document())
        output_layout.addWidget(self.output_area)

        splitter.addWidget(input_container)
        splitter.addWidget(output_container)
        splitter.setSizes([400, 400])

        layout.addWidget(splitter)

        # Setup auto-detect timer
        self.auto_detect_timer = QTimer()
        self.auto_detect_timer.timeout.connect(self.auto_detect_language)
        self.auto_detect_timer.setSingleShot(True)
        self.input_area.textChanged.connect(lambda: self.auto_detect_timer.start(500))

        # Setup real-time translation timer (if enabled)
        self.realtime_timer = QTimer()
        self.realtime_timer.timeout.connect(self.translate_code)
        self.realtime_timer.setSingleShot(True)

        # Connect for real-time translation
        if self.settings.get("realtime_translation", False):
            self.input_area.textChanged.connect(lambda: self.realtime_timer.start(1000))

    def on_source_language_changed(self, language):
        """Handle source language change"""
        if language != "Auto-detect":
            self.input_highlighter.language = language
            self.input_highlighter.setup_rules()
            self.input_highlighter.rehighlight()

    def on_target_language_changed(self, language):
        """Handle target language change"""
        self.output_highlighter.language = language
        self.output_highlighter.setup_rules()
        self.output_highlighter.rehighlight()

    def auto_detect_language(self):
        """Auto-detect source language and update syntax highlighting"""
        if self.source_combo.currentText() == "Auto-detect":
            code = self.input_area.toPlainText()
            if code.strip():
                detected = self.translator.detect_language(code)
                if detected:
                    # Update syntax highlighter
                    self.input_highlighter.language = detected
                    self.input_highlighter.setup_rules()
                    self.input_highlighter.rehighlight()

                    # Show subtle feedback in status bar
                    if hasattr(self.parent(), "status_bar"):
                        self.parent().status_bar.showMessage(f"Auto-detected: {detected}", 2000)
                else:
                    # Reset highlighter if detection failed
                    self.input_highlighter.language = None
                    self.input_highlighter.setup_rules()
                    self.input_highlighter.rehighlight()

    def swap_languages(self):
        """Swap source and target languages"""
        source = self.source_combo.currentText()
        target = self.target_combo.currentText()

        if source != "Auto-detect":
            self.target_combo.setCurrentText(source)
            self.source_combo.setCurrentText(target)

            # Swap code areas content
            source_code = self.input_area.toPlainText()
            target_code = self.output_area.toPlainText()
            self.input_area.setPlainText(target_code)
            self.output_area.setPlainText(source_code)

    def translate_code(self):
        """Translate the code"""
        code = self.input_area.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "Warning", "Please enter some code to translate.")
            return

        source_lang = self.source_combo.currentText()
        target_lang = self.target_combo.currentText()

        # Auto-detect if needed
        if source_lang == "Auto-detect":
            detected = self.translator.detect_language(code)
            if not detected:
                # Don't show a dialog - just update status and return
                if hasattr(self.parent(), "status_bar"):
                    self.parent().status_bar.showMessage(
                        "Could not detect source language. Please select manually.", 3000
                    )
                return
            source_lang = detected
            # Update status to show what was detected
            if hasattr(self.parent(), "status_bar"):
                self.parent().status_bar.showMessage(f"Detected language: {source_lang}", 2000)

        # Disable button during translation
        self.translate_btn.setEnabled(False)
        self.translate_btn.setText("Translating...")

        # Create translation thread
        self.translation_thread = TranslationThread(self.translator, code, source_lang, target_lang)
        self.translation_thread.translation_complete.connect(self.on_translation_complete)
        self.translation_thread.translation_error.connect(self.on_translation_error)
        self.translation_thread.start()

        # Emit signal
        self.translation_requested.emit(source_lang, target_lang, code)

    def on_translation_complete(self, translated_code, confidence):
        """Handle translation completion"""
        self.output_area.setPlainText(translated_code)
        self.confidence_label.setText(f"Confidence: {confidence:.0%}")

        # Re-enable button
        self.translate_btn.setEnabled(True)
        self.translate_btn.setText("Translate (Ctrl+Enter)")

        # Save to history
        self.save_to_history(
            self.input_area.toPlainText(),
            translated_code,
            self.source_combo.currentText(),
            self.target_combo.currentText(),
            confidence,
        )

    def on_translation_error(self, error_msg):
        """Handle translation error"""
        QMessageBox.critical(self, "Translation Error", error_msg)

        # Re-enable button
        self.translate_btn.setEnabled(True)
        self.translate_btn.setText("Translate (Ctrl+Enter)")

    def copy_output(self):
        """Copy output to clipboard"""
        code = self.output_area.toPlainText()
        if code:
            clipboard = QApplication.clipboard()
            clipboard.setText(code)

            # Show temporary feedback
            original_text = self.sender().text()
            self.sender().setText("✓ Copied")
            QTimer.singleShot(1000, lambda: self.sender().setText(original_text))

    def toggle_favorite(self):
        """Toggle favorite status of current translation"""
        if self.favorite_btn.text() == "☆":
            self.favorite_btn.setText("★")
            self.save_to_favorites()
        else:
            self.favorite_btn.setText("☆")

    def save_to_history(self, source_code, translated_code, source_lang, target_lang, confidence):
        """Save translation to history"""
        history = self.settings.get("translation_history", [])

        entry = {
            "timestamp": datetime.now().isoformat(),
            "source_code": source_code,
            "translated_code": translated_code,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "confidence": confidence,
        }

        history.insert(0, entry)

        # Keep only last 100 entries
        history = history[:100]

        self.settings.set("translation_history", history)

    def save_to_favorites(self):
        """Save current translation to favorites"""
        source_code = self.input_area.toPlainText()
        translated_code = self.output_area.toPlainText()

        if not source_code or not translated_code:
            return

        favorites = self.settings.get("favorites", [])

        entry = {
            "timestamp": datetime.now().isoformat(),
            "source_code": source_code,
            "translated_code": translated_code,
            "source_lang": self.source_combo.currentText(),
            "target_lang": self.target_combo.currentText(),
        }

        favorites.append(entry)
        self.settings.set("favorites", favorites)
        self.settings.save()

    def load_translation(
        self, source_lang: str, target_lang: str, source_code: str, translated_code: str
    ):
        """Load a translation into the UI"""
        # Set languages
        if source_lang != "Auto-detect":
            self.source_combo.setCurrentText(source_lang)
        self.target_combo.setCurrentText(target_lang)

        # Set code
        self.input_area.setPlainText(source_code)
        self.output_area.setPlainText(translated_code)

        # Reset favorite button
        self.favorite_btn.setText("☆")

    def on_file_dropped(self, file_path: str):
        """Handle file drop event"""
        # Try to detect language from file extension
        ext_to_lang = {
            ".py": "Python",
            ".js": "JavaScript",
            ".java": "Java",
            ".cpp": "C++",
            ".go": "Go",
            ".rs": "Rust",
        }

        for ext, lang in ext_to_lang.items():
            if file_path.endswith(ext):
                self.source_combo.setCurrentText(lang)
                break

    def paste_from_clipboard(self):
        """Paste code from clipboard"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.input_area.setPlainText(text)

    def explain_code(self):
        """Explain the input code in plain English"""
        code = self.input_area.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "Warning", "Please enter some code to explain.")
            return

        source_lang = self.source_combo.currentText()
        if source_lang == "Auto-detect":
            source_lang = self.translator.detect_language(code)
            if not source_lang:
                QMessageBox.warning(
                    self, "Warning",
                    "Could not detect language. Please select manually."
                )
                return

        self.explain_btn.setEnabled(False)
        self.explain_btn.setText("Explaining...")

        try:
            explanation = self.translator.explain_code(code, source_lang)
            self.output_area.setPlainText(explanation)
            self.confidence_label.setText("Explanation")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to explain code: {e}")
        finally:
            self.explain_btn.setEnabled(True)
            self.explain_btn.setText("💡 Explain")

    def generate_tests(self):
        """Generate unit tests for the input code"""
        code = self.input_area.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "Warning", "Please enter some code to generate tests for.")
            return

        source_lang = self.source_combo.currentText()
        if source_lang == "Auto-detect":
            source_lang = self.translator.detect_language(code)
            if not source_lang:
                QMessageBox.warning(
                    self, "Warning",
                    "Could not detect language. Please select manually."
                )
                return

        self.generate_tests_btn.setEnabled(False)
        self.generate_tests_btn.setText("Generating...")

        try:
            from translator.test_generator import TestGenerator
            generator = TestGenerator()
            tests = generator.generate_tests(code, source_lang)
            self.output_area.setPlainText(tests)
            self.confidence_label.setText("Generated Tests")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate tests: {e}")
        finally:
            self.generate_tests_btn.setEnabled(True)
            self.generate_tests_btn.setText("🧪 Generate Tests")

    def analyze_code(self):
        """Analyze code complexity"""
        code = self.input_area.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "Warning", "Please enter some code to analyze.")
            return

        source_lang = self.source_combo.currentText()
        if source_lang == "Auto-detect":
            source_lang = self.translator.detect_language(code)
            if not source_lang:
                QMessageBox.warning(
                    self, "Warning",
                    "Could not detect language. Please select manually."
                )
                return

        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("Analyzing...")

        try:
            from analyzer.complexity import ComplexityAnalyzer
            analyzer = ComplexityAnalyzer()
            analysis = analyzer.analyze(code, source_lang)
            output = analyzer.format_analysis(analysis)
            self.output_area.setPlainText(output)
            self.confidence_label.setText(f"Complexity: {analyzer.get_complexity_rating(analysis.max_complexity)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to analyze code: {e}")
        finally:
            self.analyze_btn.setEnabled(True)
            self.analyze_btn.setText("📊 Analyze")


class TranslationThread(QThread):
    """Thread for performing translations"""

    translation_complete = pyqtSignal(str, float)  # translated_code, confidence
    translation_error = pyqtSignal(str)  # error_message

    def __init__(self, translator, code, source_lang, target_lang):
        super().__init__()
        self.translator = translator
        self.code = code
        self.source_lang = source_lang
        self.target_lang = target_lang

    def run(self):
        """Run translation in thread"""
        try:
            translated, confidence = self.translator.translate(
                self.code, self.source_lang, self.target_lang
            )
            self.translation_complete.emit(translated, confidence)
        except Exception as e:
            self.translation_error.emit(str(e))


class SettingsDialog(QDialog):
    """Settings dialog for configuration"""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(500, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize settings UI"""
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()

        # General tab
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "General")

        # API Keys tab
        api_tab = self.create_api_tab()
        tabs.addTab(api_tab, "API Keys")

        # Appearance tab
        appearance_tab = self.create_appearance_tab()
        tabs.addTab(appearance_tab, "Appearance")

        # Shortcuts tab
        shortcuts_tab = self.create_shortcuts_tab()
        tabs.addTab(shortcuts_tab, "Shortcuts")

        layout.addWidget(tabs)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def create_general_tab(self):
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Auto-detect language
        self.auto_detect_check = QCheckBox("Auto-detect source language")
        self.auto_detect_check.setChecked(self.settings.get("auto_detect_language", True))
        layout.addWidget(self.auto_detect_check)

        # Save history
        self.save_history_check = QCheckBox("Save translation history")
        self.save_history_check.setChecked(self.settings.get("save_history", True))
        layout.addWidget(self.save_history_check)

        # Real-time translation
        self.realtime_check = QCheckBox("Enable real-time translation (as you type)")
        self.realtime_check.setChecked(self.settings.get("realtime_translation", False))
        layout.addWidget(self.realtime_check)

        # History limit
        history_group = QGroupBox("History Settings")
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("Keep last"))

        self.history_limit_spin = QSpinBox()
        self.history_limit_spin.setRange(10, 1000)
        self.history_limit_spin.setValue(self.settings.get("history_limit", 100))
        history_layout.addWidget(self.history_limit_spin)

        history_layout.addWidget(QLabel("translations"))
        history_layout.addStretch()
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        # Start minimized
        self.start_minimized_check = QCheckBox("Start minimized to tray")
        self.start_minimized_check.setChecked(self.settings.get("start_minimized", False))
        layout.addWidget(self.start_minimized_check)

        layout.addStretch()
        return widget

    def create_api_tab(self):
        """Create API keys tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # OpenAI
        openai_group = QGroupBox("OpenAI")
        openai_layout = QVBoxLayout()

        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setPlaceholderText("sk-...")
        self.openai_key_input.setText(self.settings.get("openai_api_key", ""))
        openai_layout.addWidget(QLabel("API Key:"))
        openai_layout.addWidget(self.openai_key_input)

        openai_group.setLayout(openai_layout)
        layout.addWidget(openai_group)

        # Anthropic
        anthropic_group = QGroupBox("Anthropic Claude")
        anthropic_layout = QVBoxLayout()

        self.anthropic_key_input = QLineEdit()
        self.anthropic_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.anthropic_key_input.setPlaceholderText("sk-ant-...")
        self.anthropic_key_input.setText(self.settings.get("anthropic_api_key", ""))
        anthropic_layout.addWidget(QLabel("API Key:"))
        anthropic_layout.addWidget(self.anthropic_key_input)

        anthropic_group.setLayout(anthropic_layout)
        layout.addWidget(anthropic_group)

        # Google
        google_group = QGroupBox("Google Gemini")
        google_layout = QVBoxLayout()

        self.google_key_input = QLineEdit()
        self.google_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.google_key_input.setPlaceholderText("AI...")
        self.google_key_input.setText(self.settings.get("google_api_key", ""))
        google_layout.addWidget(QLabel("API Key:"))
        google_layout.addWidget(self.google_key_input)

        google_group.setLayout(google_layout)
        layout.addWidget(google_group)

        # Note
        note_label = QLabel(
            "Note: API keys are stored locally and encrypted. "
            "You need at least one API key for online translation."
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(note_label)

        layout.addStretch()
        return widget

    def create_appearance_tab(self):
        """Create appearance settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Theme
        theme_group = QGroupBox("Theme")
        theme_layout = QHBoxLayout()

        self.dark_theme_radio = QCheckBox("Dark theme")
        self.dark_theme_radio.setChecked(self.settings.get("theme", "dark") == "dark")
        theme_layout.addWidget(self.dark_theme_radio)

        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # Window opacity
        opacity_group = QGroupBox("Window Opacity")
        opacity_layout = QHBoxLayout()

        self.opacity_slider = QSpinBox()
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setSuffix("%")
        self.opacity_slider.setValue(int(self.settings.get("window_opacity", 0.95) * 100))
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addStretch()

        opacity_group.setLayout(opacity_layout)
        layout.addWidget(opacity_group)

        # Font settings
        font_group = QGroupBox("Code Font")
        font_layout = QHBoxLayout()

        font_layout.addWidget(QLabel("Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.settings.get("font_size", 11))
        font_layout.addWidget(self.font_size_spin)
        font_layout.addStretch()

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        layout.addStretch()
        return widget

    def create_shortcuts_tab(self):
        """Create shortcuts tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        shortcuts_label = QLabel(
            "Keyboard Shortcuts:\n\n"
            "Ctrl+Shift+T - Show/Hide window\n"
            "Ctrl+Enter - Translate\n"
            "Ctrl+M - Toggle click-through mode\n"
            "Ctrl+D - Toggle dark/light theme\n"
            "Ctrl+\\ - Close window\n"
            "Ctrl+Arrow Keys - Move window\n"
            "Ctrl+H - Show history\n"
            "Ctrl+S - Save to favorites"
        )
        shortcuts_label.setStyleSheet("font-family: monospace; padding: 10px;")
        layout.addWidget(shortcuts_label)

        layout.addStretch()
        return widget

    def save_settings(self):
        """Save settings and close dialog"""
        # General
        self.settings.set("auto_detect_language", self.auto_detect_check.isChecked())
        self.settings.set("save_history", self.save_history_check.isChecked())
        self.settings.set("realtime_translation", self.realtime_check.isChecked())
        self.settings.set("history_limit", self.history_limit_spin.value())
        self.settings.set("start_minimized", self.start_minimized_check.isChecked())

        # API Keys
        self.settings.set("openai_api_key", self.openai_key_input.text())
        self.settings.set("anthropic_api_key", self.anthropic_key_input.text())
        self.settings.set("google_api_key", self.google_key_input.text())

        # Appearance
        self.settings.set("theme", "dark" if self.dark_theme_radio.isChecked() else "light")
        self.settings.set("window_opacity", self.opacity_slider.value() / 100)
        self.settings.set("font_size", self.font_size_spin.value())

        self.settings.save()
        self.accept()
