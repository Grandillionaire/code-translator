"""
Global keyboard shortcuts management
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget
import sys
import os

# Platform-specific imports for global hotkeys
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    import win32con
elif sys.platform == "darwin":
    try:
        from pynput import keyboard
    except ImportError:
        keyboard = None
else:
    # Linux - use python-xlib if available
    try:
        from Xlib import X, display
        from Xlib.ext import record
        from Xlib.protocol import rq
    except ImportError:
        X = None


class ShortcutManager(QObject):
    """Manage global keyboard shortcuts"""

    # Signals for global hotkeys
    show_hide_triggered = pyqtSignal()
    translate_triggered = pyqtSignal()

    def __init__(self, parent_window: QWidget):
        super().__init__()
        self.parent_window = parent_window
        self.global_hotkeys_enabled = False

        # Try to setup global hotkeys based on platform
        self._setup_platform_hotkeys()

    def _setup_platform_hotkeys(self):
        """Setup platform-specific global hotkeys"""
        if sys.platform == "win32":
            self._setup_windows_hotkeys()
        elif sys.platform == "darwin":
            self._setup_macos_hotkeys()
        else:
            self._setup_linux_hotkeys()

    def _setup_windows_hotkeys(self):
        """Setup Windows global hotkeys"""
        # This would require a more complex implementation with Windows hooks
        # For now, we'll rely on Qt's built-in shortcuts
        pass

    def _setup_macos_hotkeys(self):
        """Setup macOS global hotkeys using pynput"""
        if keyboard is None:
            return

        try:
            # Create hotkey combinations
            self.hotkeys = keyboard.GlobalHotKeys(
                {
                    "<cmd>+<shift>+t": self._on_show_hide,
                    "<cmd>+<shift>+<return>": self._on_translate,
                }
            )

            # Start listening
            self.hotkeys.start()
            self.global_hotkeys_enabled = True

        except Exception as e:
            print(f"Failed to setup macOS global hotkeys: {e}")

    def _setup_linux_hotkeys(self):
        """Setup Linux global hotkeys"""
        # This would require X11 integration
        # For now, we'll rely on Qt's built-in shortcuts
        pass

    def _on_show_hide(self):
        """Handle show/hide hotkey"""
        self.show_hide_triggered.emit()

    def _on_translate(self):
        """Handle translate hotkey"""
        self.translate_triggered.emit()

    def cleanup(self):
        """Cleanup global hotkeys"""
        if hasattr(self, "hotkeys") and self.hotkeys:
            self.hotkeys.stop()
