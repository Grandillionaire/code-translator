#!/usr/bin/env python3
"""
Code Translator - A professional desktop code translation application
Main entry point for the application
"""

import sys
import os
from pathlib import Path

# Check Python version before any imports
if sys.version_info < (3, 8):
    print("ERROR: Code Translator requires Python 3.8 or newer")
    print(f"You are using Python {sys.version}")
    sys.exit(1)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Now safe to import after Python version check
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt, QCoreApplication
except ImportError:
    print("ERROR: PyQt6 not installed. Please run: pip install PyQt6>=6.5.0")
    sys.exit(1)

from gui.main_window import TranslatorWindow
from config.settings import Settings
from utils.logger import setup_logger
from utils.dependency_checker import DependencyChecker

# Application metadata
QCoreApplication.setOrganizationName("CodeTranslator")
QCoreApplication.setApplicationName("Code Translator")
QCoreApplication.setApplicationVersion("1.0.0")


def main():
    """Main application entry point"""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Code Translator application")
    
    # Check dependencies
    logger.info("Checking runtime dependencies...")
    report = DependencyChecker.check_all_dependencies()
    
    if not report['all_core_satisfied']:
        print("\nERROR: Core dependencies are not satisfied.")
        DependencyChecker.print_report(report)
        
        # If running in GUI mode, show error dialog
        if 'PyQt6' in sys.modules:
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Missing Dependencies",
                "Core dependencies are not installed.\n\n"
                "Please run: pip install -r requirements.txt\n\n"
                "See console output for details."
            )
        sys.exit(1)
    
    # Log AI providers status
    if report['ai_providers_available'] == 0:
        logger.warning("No AI providers available - only offline translation will work")
    else:
        logger.info(f"AI providers available: {report['ai_providers_available']}")
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application instance
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Load settings
    settings = Settings()
    
    # Create and show main window
    window = TranslatorWindow(settings)
    window.show()
    
    # Run application
    logger.info("Application started successfully")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()