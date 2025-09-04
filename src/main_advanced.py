#!/usr/bin/env python3
"""
Code Translator - Advanced Production-Grade Architecture
Main entry point with enterprise-level features
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional
import logging

# Check Python version before any imports
if sys.version_info < (3, 8):
    print("ERROR: Code Translator requires Python 3.8 or newer")
    print(f"You are using Python {sys.version}")
    sys.exit(1)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import advanced components
from config.config_manager import ConfigurationManager, StorageBackend
from providers.provider_framework import ProviderRegistry, ProviderChain, LoadBalancer
from providers.implementations import OpenAIProvider, AnthropicProvider, GoogleProvider, OfflineProvider
from error_handling.error_framework import ErrorHandler, ErrorCategory, ErrorSeverity
from lifecycle.app_manager import ApplicationLifecycleManager, ApplicationState

# PyQt imports with error handling
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow
    from PyQt6.QtCore import Qt, QCoreApplication, QTimer, pyqtSignal
except ImportError:
    print("ERROR: PyQt6 not installed. Please run: pip install PyQt6>=6.5.0")
    sys.exit(1)

# Application imports
from gui.main_window import TranslatorWindow
from translator.translator_engine import TranslatorEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedTranslatorEngine:
    """Enhanced translator engine with provider management"""
    
    def __init__(
        self,
        config_manager: ConfigurationManager,
        provider_registry: ProviderRegistry,
        error_handler: ErrorHandler
    ):
        self.config_manager = config_manager
        self.provider_registry = provider_registry
        self.error_handler = error_handler
        
        # Setup provider chain with fallback
        self.provider_chain = self._setup_provider_chain()
        
        # Setup load balancer
        self.load_balancer = LoadBalancer(
            self.provider_registry.get_healthy_providers(),
            strategy="best_performance"
        )
    
    def _setup_provider_chain(self) -> ProviderChain:
        """Setup provider chain with priority order"""
        providers = []
        
        # Priority order based on configuration
        preferred = self.config_manager.get("preferred_provider", "auto")
        
        if preferred == "auto":
            # Automatic selection based on availability and performance
            priority_order = ["anthropic", "openai", "google", "offline"]
        else:
            # User preference first, then fallbacks
            priority_order = [preferred, "anthropic", "openai", "google", "offline"]
        
        for name in priority_order:
            provider = self.provider_registry.get_provider(name)
            if provider:
                providers.append(provider)
        
        return ProviderChain(providers)
    
    async def translate(
        self,
        code: str,
        source_lang: str,
        target_lang: str,
        **kwargs
    ) -> tuple[str, float]:
        """Translate code with advanced provider management"""
        try:
            # Use provider chain for automatic fallback
            result = await self.provider_chain.execute(
                "translate_code",
                code,
                source_lang,
                target_lang,
                **kwargs
            )
            
            return result
            
        except Exception as e:
            # Handle translation error
            error_info = self.error_handler.handle_error(
                e,
                category=ErrorCategory.PROVIDER,
                severity=ErrorSeverity.HIGH,
                operation="translate_code",
                source_lang=source_lang,
                target_lang=target_lang
            )
            
            # Attempt recovery
            if await self.error_handler.attempt_recovery(error_info):
                # Retry with recovered state
                return await self.translate(code, source_lang, target_lang, **kwargs)
            
            raise


class EnhancedTranslatorWindow(TranslatorWindow):
    """Enhanced main window with advanced features"""
    
    status_update = pyqtSignal(str)
    
    def __init__(
        self,
        config_manager: ConfigurationManager,
        translator_engine: AdvancedTranslatorEngine,
        error_handler: ErrorHandler,
        lifecycle_manager: ApplicationLifecycleManager
    ):
        # Initialize with legacy settings adapter
        legacy_settings = self._create_legacy_settings(config_manager)
        super().__init__(legacy_settings)
        
        self.config_manager = config_manager
        self.advanced_translator = translator_engine
        self.error_handler = error_handler
        self.lifecycle_manager = lifecycle_manager
        
        # Setup health monitoring
        self._setup_health_monitoring()
        
        # Connect signals
        self.status_update.connect(self._update_status_bar)
    
    def _create_legacy_settings(self, config_manager: ConfigurationManager):
        """Create legacy settings adapter for compatibility"""
        class LegacySettingsAdapter:
            def __init__(self, cm):
                self.cm = cm
            
            def get(self, key, default=None):
                return self.cm.get(key, default)
            
            def set(self, key, value):
                self.cm.set(key, value)
            
            def save(self):
                # ConfigurationManager saves automatically
                pass
        
        return LegacySettingsAdapter(config_manager)
    
    def _setup_health_monitoring(self):
        """Setup periodic health monitoring"""
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self._check_health)
        self.health_timer.start(30000)  # Check every 30 seconds
    
    def _check_health(self):
        """Check application health and update UI"""
        health = self.lifecycle_manager.get_health_status()
        
        if health["healthy"]:
            self.status_update.emit("✓ All systems operational")
        else:
            self.status_update.emit("⚠ Some systems degraded")
        
        # Update provider status in UI
        if "providers" in health:
            healthy_providers = [
                name for name, info in health["providers"].items()
                if info["status"] == "healthy"
            ]
            
            if len(healthy_providers) == 0:
                self.status_update.emit("⚠ No AI providers available - using offline mode")
    
    def _update_status_bar(self, message: str):
        """Update status bar with message"""
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(message, 5000)
    
    async def translate_code_async(self, code: str, source_lang: str, target_lang: str):
        """Override to use advanced translator"""
        try:
            # Show loading state
            self.status_update.emit("Translating...")
            
            # Use advanced translator
            result, confidence = await self.advanced_translator.translate(
                code,
                source_lang,
                target_lang
            )
            
            # Update UI with result
            self.output_editor.setPlainText(result)
            self.status_update.emit(f"Translation complete (confidence: {confidence:.0%})")
            
        except Exception as e:
            # Handle error with advanced error handling
            error_info = self.error_handler.handle_error(
                e,
                category=ErrorCategory.USER_INPUT,
                user_message="Translation failed. Please check your input and try again."
            )
            
            # Show user-friendly error
            QMessageBox.warning(
                self,
                "Translation Error",
                error_info.user_message
            )
    
    def closeEvent(self, event):
        """Handle application close with proper cleanup"""
        # Save configuration
        self.config_manager.export(
            self.config_manager.config_dir / "config_backup.json",
            include_sensitive=True
        )
        
        # Call parent close event
        super().closeEvent(event)


async def main_async():
    """Async main application entry point"""
    # Create lifecycle manager
    lifecycle_manager = ApplicationLifecycleManager(
        app_name="CodeTranslator",
        enable_monitoring=True
    )
    
    # Initialize application
    logger.info("Starting Code Translator with advanced architecture")
    
    if not await lifecycle_manager.initialize():
        logger.error("Failed to initialize application")
        return 1
    
    # Get components
    config_manager = lifecycle_manager.config_manager
    error_handler = lifecycle_manager.error_handler
    provider_registry = lifecycle_manager.provider_registry
    
    # Create advanced translator engine
    translator_engine = AdvancedTranslatorEngine(
        config_manager,
        provider_registry,
        error_handler
    )
    
    # Setup Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Code Translator")
    app.setOrganizationName("CodeTranslator")
    app.setStyle("Fusion")
    
    # Enable high DPI support
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    
    # Create main window
    window = EnhancedTranslatorWindow(
        config_manager,
        translator_engine,
        error_handler,
        lifecycle_manager
    )
    
    # Show window
    window.show()
    
    # Log successful startup
    metrics = lifecycle_manager.get_performance_metrics()
    logger.info(f"Application started successfully in {metrics.startup_time:.2f}s")
    
    # Create error report if needed
    if error_handler.get_telemetry_stats()["total_errors"] > 0:
        report = error_handler.create_error_report()
        report_path = lifecycle_manager.config_dir / "logs" / "startup_errors.json"
        
        with open(report_path, 'w') as f:
            import json
            json.dump(report, f, indent=2)
    
    # Run Qt event loop
    exit_code = app.exec()
    
    # Shutdown
    await lifecycle_manager.shutdown()
    
    return exit_code


def main():
    """Main entry point"""
    try:
        # Run async main
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        
        # Show error dialog if possible
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Fatal Error",
                f"A critical error occurred:\n\n{str(e)}\n\n"
                "Please check the logs for more information."
            )
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()