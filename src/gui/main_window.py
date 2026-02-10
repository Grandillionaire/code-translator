"""
Main application window with transparency and overlay features
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QComboBox,
    QLabel,
    QSplitter,
    QFrame,
    QToolBar,
    QStatusBar,
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtCore import (
    Qt,
    QPoint,
    QTimer,
    pyqtSignal,
    QPropertyAnimation,
    QEasingCurve,
    QByteArray,
)
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QShortcut, QPainter, QColor, QBrush, QPixmap
import sys
from typing import Optional

from translator.translator_engine import TranslatorEngine
from gui.widgets import TranslationWidget, SettingsDialog
from gui.history_dialog import HistoryDialog
from config.settings import Settings
from utils.shortcuts import ShortcutManager


class TranslatorWindow(QMainWindow):
    """Main application window with transparent overlay functionality"""

    translation_requested = pyqtSignal(str, str, str)  # source_lang, target_lang, code

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.translator_engine = TranslatorEngine(settings)
        self.shortcut_manager = ShortcutManager(self)
        self.is_click_through = False
        self.drag_position: Optional[QPoint] = None

        self.init_ui()
        self.setup_shortcuts()
        self.load_window_state()
        self.setup_system_tray()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Code Translator")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )

        # Set window transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(self.settings.get("window_opacity", 0.95))

        # Central widget with custom painting
        self.central_widget = TransparentWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title bar
        self.create_title_bar(main_layout)

        # Translation widget
        self.translation_widget = TranslationWidget(self.translator_engine, self.settings)
        self.translation_widget.translation_requested.connect(self.on_translation_requested)
        main_layout.addWidget(self.translation_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background: rgba(40, 40, 40, 180); color: white;")
        main_layout.addWidget(self.status_bar)

        # Apply theme
        self.apply_theme()

        # Set minimum size
        self.setMinimumSize(800, 600)

    def create_title_bar(self, parent_layout):
        """Create custom title bar"""
        title_bar = QFrame()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet(
            """
            QFrame {
                background: rgba(30, 30, 30, 200);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """
        )

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 5, 10, 5)

        # Title label
        title = QLabel("Code Translator")
        title.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(title)

        # Spacer
        layout.addStretch()

        # Control buttons
        self.create_control_buttons(layout)

        parent_layout.addWidget(title_bar)

    def create_control_buttons(self, layout):
        """Create window control buttons"""
        button_style = """
            QPushButton {
                background: rgba(255, 255, 255, 30);
                color: white;
                border: none;
                border-radius: 12px;
                width: 24px;
                height: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 50);
            }
        """

        # Minimize button
        minimize_btn = QPushButton("−")
        minimize_btn.setStyleSheet(button_style)
        minimize_btn.clicked.connect(self.showMinimized)
        layout.addWidget(minimize_btn)

        # Click-through toggle
        self.click_through_btn = QPushButton("👁")
        self.click_through_btn.setStyleSheet(button_style)
        self.click_through_btn.clicked.connect(self.toggle_click_through)
        self.click_through_btn.setToolTip("Toggle click-through mode")
        layout.addWidget(self.click_through_btn)

        # History button
        history_btn = QPushButton("📋")
        history_btn.setStyleSheet(button_style)
        history_btn.clicked.connect(self.show_history)
        history_btn.setToolTip("History (Ctrl+H)")
        layout.addWidget(history_btn)

        # Settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setStyleSheet(button_style)
        settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(settings_btn)

        # Close button
        close_btn = QPushButton("×")
        close_btn.setStyleSheet(
            button_style
            + """
            QPushButton:hover {
                background: rgba(255, 100, 100, 150);
            }
        """
        )
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            "Ctrl+Shift+T": self.toggle_visibility,
            "Ctrl+M": self.toggle_click_through,
            "Ctrl+D": self.toggle_theme,
            "Ctrl+\\": self.close,
            "Ctrl+Enter": self.translation_widget.translate_code,
            "Ctrl+H": self.show_history,
            "Ctrl+Left": lambda: self.move_window(-50, 0),
            "Ctrl+Right": lambda: self.move_window(50, 0),
            "Ctrl+Up": lambda: self.move_window(0, -50),
            "Ctrl+Down": lambda: self.move_window(0, 50),
        }

        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)

    def setup_system_tray(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Code Translator")

        # Create a simple icon (we'll use text for now)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")
        painter.end()

        self.tray_icon.setIcon(QIcon(pixmap))

        # Create tray menu
        tray_menu = QMenu()

        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def toggle_visibility(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def toggle_click_through(self):
        """Toggle click-through mode"""
        self.is_click_through = not self.is_click_through

        if self.is_click_through:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowTransparentForInput)
            self.setWindowOpacity(0.7)
            self.click_through_btn.setText("👻")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowTransparentForInput)
            self.setWindowOpacity(self.settings.get("window_opacity", 0.95))
            self.click_through_btn.setText("👁")

        self.show()

    def toggle_theme(self):
        """Toggle between dark and light theme"""
        current_theme = self.settings.get("theme", "dark")
        new_theme = "light" if current_theme == "dark" else "dark"
        self.settings.set("theme", new_theme)
        self.apply_theme()

    def apply_theme(self):
        """Apply the current theme"""
        theme = self.settings.get("theme", "dark")

        if theme == "dark":
            self.setStyleSheet(
                """
                QMainWindow {
                    background: transparent;
                }
                QTextEdit, QComboBox, QPushButton {
                    background: rgba(40, 40, 40, 200);
                    color: white;
                    border: 1px solid rgba(100, 100, 100, 100);
                    border-radius: 5px;
                    padding: 5px;
                }
                QTextEdit:focus, QComboBox:focus {
                    border: 1px solid rgba(100, 200, 255, 200);
                }
            """
            )
        else:
            self.setStyleSheet(
                """
                QMainWindow {
                    background: transparent;
                }
                QTextEdit, QComboBox, QPushButton {
                    background: rgba(240, 240, 240, 200);
                    color: black;
                    border: 1px solid rgba(200, 200, 200, 100);
                    border-radius: 5px;
                    padding: 5px;
                }
                QTextEdit:focus, QComboBox:focus {
                    border: 1px solid rgba(0, 100, 200, 200);
                }
            """
            )

    def move_window(self, dx: int, dy: int):
        """Move window by specified offset"""
        pos = self.pos()
        self.move(pos.x() + dx, pos.y() + dy)

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.apply_theme()
            self.translator_engine.reload_settings()

    def show_history(self):
        """Show history dialog"""
        dialog = HistoryDialog(self.settings, self)
        dialog.translation_selected.connect(self.load_translation)
        dialog.show()

    def load_translation(
        self, source_lang: str, target_lang: str, source_code: str, translated_code: str
    ):
        """Load a translation from history"""
        self.translation_widget.load_translation(
            source_lang, target_lang, source_code, translated_code
        )

    def on_translation_requested(self, source_lang: str, target_lang: str, code: str):
        """Handle translation request"""
        self.status_bar.showMessage("Translating...", 2000)

    def mousePressEvent(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.drag_position = None

    def load_window_state(self):
        """Load saved window state"""
        try:
            geometry = self.settings.get("window_geometry")
            if geometry:
                # Handle conversion from string to QByteArray if needed
                if isinstance(geometry, str):
                    # Try to decode from base64 first (common format for QByteArray storage)
                    try:
                        import base64

                        geometry_bytes = base64.b64decode(geometry.encode())
                        geometry = QByteArray(geometry_bytes)
                    except:
                        # If base64 fails, try direct byte conversion
                        geometry = QByteArray(geometry.encode())
                elif isinstance(geometry, bytes):
                    geometry = QByteArray(geometry)

                self.restoreGeometry(geometry)
        except Exception as e:
            # Log error but don't crash - just use default window size/position
            print(f"Failed to restore window geometry: {e}")

    def save_window_state(self):
        """Save window state"""
        try:
            geometry = self.saveGeometry()
            # Convert QByteArray to base64 string for JSON storage
            import base64

            geometry_str = base64.b64encode(geometry.data()).decode("utf-8")
            self.settings.set("window_geometry", geometry_str)
        except Exception as e:
            print(f"Failed to save window geometry: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        self.save_window_state()
        self.settings.save()
        event.accept()


class TransparentWidget(QWidget):
    """Custom widget with transparent background and rounded corners"""

    def paintEvent(self, event):
        """Custom paint event for transparency and styling"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw semi-transparent background with rounded corners
        rect = self.rect()
        painter.setBrush(QBrush(QColor(20, 20, 20, 180)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 15, 15)
