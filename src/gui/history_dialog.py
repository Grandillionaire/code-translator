"""
History and Favorites dialog for Code Translator
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QListWidget,
    QListWidgetItem, QPushButton, QTextEdit, QSplitter, QLabel,
    QLineEdit, QMessageBox, QDialogButtonBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from typing import Dict, List
import json
import sys

from config.settings import Settings


class HistoryDialog(QDialog):
    """Dialog for viewing translation history and favorites"""
    
    # Signal emitted when user wants to use a translation
    translation_selected = pyqtSignal(str, str, str, str)  # source_lang, target_lang, source_code, translated_code
    
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("History & Favorites")
        self.setModal(False)  # Non-modal so user can interact with main window
        self.setMinimumSize(800, 600)
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in code or languages...")
        self.search_input.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # History tab
        self.history_widget = self.create_history_tab()
        self.tabs.addTab(self.history_widget, "History")
        
        # Favorites tab
        self.favorites_widget = self.create_favorites_tab()
        self.tabs.addTab(self.favorites_widget, "Favorites")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.use_button = QPushButton("Use Translation")
        self.use_button.clicked.connect(self.use_translation)
        self.use_button.setEnabled(False)
        button_layout.addWidget(self.use_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_item)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        
        self.clear_history_button = QPushButton("Clear All History")
        self.clear_history_button.clicked.connect(self.clear_history)
        button_layout.addWidget(self.clear_history_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
    def create_history_tab(self):
        """Create the history tab"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # History list
        self.history_list = QListWidget()
        self.history_list.itemSelectionChanged.connect(self.on_history_selection_changed)
        self.history_list.itemDoubleClicked.connect(self.use_translation)
        layout.addWidget(self.history_list, 1)
        
        # Preview area
        preview_layout = QVBoxLayout()
        
        # Source code preview
        preview_layout.addWidget(QLabel("Source Code:"))
        self.history_source_preview = QTextEdit()
        self.history_source_preview.setReadOnly(True)
        font_family = "Menlo" if sys.platform == "darwin" else "Consolas" if sys.platform == "win32" else "monospace"
        self.history_source_preview.setFont(QFont(font_family, 10))
        preview_layout.addWidget(self.history_source_preview)
        
        # Translated code preview
        preview_layout.addWidget(QLabel("Translated Code:"))
        self.history_translated_preview = QTextEdit()
        self.history_translated_preview.setReadOnly(True)
        self.history_translated_preview.setFont(QFont(font_family, 10))
        preview_layout.addWidget(self.history_translated_preview)
        
        # Details label
        self.history_details_label = QLabel("")
        self.history_details_label.setWordWrap(True)
        preview_layout.addWidget(self.history_details_label)
        
        preview_widget = QWidget()
        preview_widget.setLayout(preview_layout)
        layout.addWidget(preview_widget, 2)
        
        return widget
        
    def create_favorites_tab(self):
        """Create the favorites tab"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Favorites list
        self.favorites_list = QListWidget()
        self.favorites_list.itemSelectionChanged.connect(self.on_favorites_selection_changed)
        self.favorites_list.itemDoubleClicked.connect(self.use_translation)
        layout.addWidget(self.favorites_list, 1)
        
        # Preview area
        preview_layout = QVBoxLayout()
        
        # Source code preview
        preview_layout.addWidget(QLabel("Source Code:"))
        self.favorites_source_preview = QTextEdit()
        self.favorites_source_preview.setReadOnly(True)
        font_family = "Menlo" if sys.platform == "darwin" else "Consolas" if sys.platform == "win32" else "monospace"
        self.favorites_source_preview.setFont(QFont(font_family, 10))
        preview_layout.addWidget(self.favorites_source_preview)
        
        # Translated code preview
        preview_layout.addWidget(QLabel("Translated Code:"))
        self.favorites_translated_preview = QTextEdit()
        self.favorites_translated_preview.setReadOnly(True)
        self.favorites_translated_preview.setFont(QFont(font_family, 10))
        preview_layout.addWidget(self.favorites_translated_preview)
        
        # Details label
        self.favorites_details_label = QLabel("")
        self.favorites_details_label.setWordWrap(True)
        preview_layout.addWidget(self.favorites_details_label)
        
        preview_widget = QWidget()
        preview_widget.setLayout(preview_layout)
        layout.addWidget(preview_widget, 2)
        
        return widget
        
    def load_data(self):
        """Load history and favorites data"""
        # Load history
        history = self.settings.get("translation_history", [])
        self.history_list.clear()
        
        for entry in history:
            item = QListWidgetItem()
            timestamp = datetime.fromisoformat(entry['timestamp'])
            item.setText(f"{entry['source_lang']} → {entry['target_lang']} ({timestamp.strftime('%Y-%m-%d %H:%M')})")
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.history_list.addItem(item)
            
        # Load favorites
        favorites = self.settings.get("favorites", [])
        self.favorites_list.clear()
        
        for entry in favorites:
            item = QListWidgetItem()
            timestamp = datetime.fromisoformat(entry['timestamp'])
            item.setText(f"{entry['source_lang']} → {entry['target_lang']} ({timestamp.strftime('%Y-%m-%d %H:%M')})")
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.favorites_list.addItem(item)
            
    def filter_items(self, text: str):
        """Filter items based on search text"""
        search_text = text.lower()
        
        # Filter history
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            entry = item.data(Qt.ItemDataRole.UserRole)
            visible = (
                search_text in entry['source_code'].lower() or
                search_text in entry['translated_code'].lower() or
                search_text in entry['source_lang'].lower() or
                search_text in entry['target_lang'].lower()
            )
            item.setHidden(not visible)
            
        # Filter favorites
        for i in range(self.favorites_list.count()):
            item = self.favorites_list.item(i)
            entry = item.data(Qt.ItemDataRole.UserRole)
            visible = (
                search_text in entry['source_code'].lower() or
                search_text in entry['translated_code'].lower() or
                search_text in entry['source_lang'].lower() or
                search_text in entry['target_lang'].lower()
            )
            item.setHidden(not visible)
            
    def on_history_selection_changed(self):
        """Handle history selection change"""
        items = self.history_list.selectedItems()
        if items:
            entry = items[0].data(Qt.ItemDataRole.UserRole)
            self.history_source_preview.setPlainText(entry['source_code'])
            self.history_translated_preview.setPlainText(entry['translated_code'])
            
            timestamp = datetime.fromisoformat(entry['timestamp'])
            details = f"Translation: {entry['source_lang']} → {entry['target_lang']}\n"
            details += f"Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            if 'confidence' in entry:
                details += f"Confidence: {entry['confidence']:.0%}"
            self.history_details_label.setText(details)
            
            self.use_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            self.history_source_preview.clear()
            self.history_translated_preview.clear()
            self.history_details_label.clear()
            self.use_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            
    def on_favorites_selection_changed(self):
        """Handle favorites selection change"""
        items = self.favorites_list.selectedItems()
        if items:
            entry = items[0].data(Qt.ItemDataRole.UserRole)
            self.favorites_source_preview.setPlainText(entry['source_code'])
            self.favorites_translated_preview.setPlainText(entry['translated_code'])
            
            timestamp = datetime.fromisoformat(entry['timestamp'])
            details = f"Translation: {entry['source_lang']} → {entry['target_lang']}\n"
            details += f"Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            self.favorites_details_label.setText(details)
            
            self.use_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            self.favorites_source_preview.clear()
            self.favorites_translated_preview.clear()
            self.favorites_details_label.clear()
            self.use_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            
    def use_translation(self):
        """Use the selected translation"""
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 0:  # History tab
            items = self.history_list.selectedItems()
        else:  # Favorites tab
            items = self.favorites_list.selectedItems()
            
        if items:
            entry = items[0].data(Qt.ItemDataRole.UserRole)
            self.translation_selected.emit(
                entry.get('source_lang', 'Auto-detect'),
                entry['target_lang'],
                entry['source_code'],
                entry['translated_code']
            )
            
    def delete_item(self):
        """Delete the selected item"""
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 0:  # History tab
            items = self.history_list.selectedItems()
            if items:
                row = self.history_list.row(items[0])
                self.history_list.takeItem(row)
                
                # Update settings
                history = self.settings.get("translation_history", [])
                if 0 <= row < len(history):
                    history.pop(row)
                    self.settings.set("translation_history", history)
                    self.settings.save()
        else:  # Favorites tab
            items = self.favorites_list.selectedItems()
            if items:
                row = self.favorites_list.row(items[0])
                self.favorites_list.takeItem(row)
                
                # Update settings
                favorites = self.settings.get("favorites", [])
                if 0 <= row < len(favorites):
                    favorites.pop(row)
                    self.settings.set("favorites", favorites)
                    self.settings.save()
                    
    def clear_history(self):
        """Clear all history"""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all translation history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_list.clear()
            self.settings.set("translation_history", [])
            self.settings.save()
            self.history_source_preview.clear()
            self.history_translated_preview.clear()
            self.history_details_label.clear()