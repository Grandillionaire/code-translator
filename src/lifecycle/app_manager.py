"""
Robust Application Lifecycle Management
Handles initialization, resource management, performance monitoring, and graceful shutdown
"""

import asyncio
import atexit
import signal
import sys
import threading
import psutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Set
import logging
import json
import time
from contextlib import contextmanager
import os
import platform

from config.config_manager import ConfigurationManager
from providers.provider_framework import ProviderRegistry, BaseProvider
from error_handling.error_framework import ErrorHandler, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class ApplicationState(Enum):
    """Application lifecycle states"""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    ERROR = "error"


class DependencyStatus(Enum):
    """Dependency health status"""

    SATISFIED = "satisfied"
    MISSING = "missing"
    OUTDATED = "outdated"
    INCOMPATIBLE = "incompatible"


@dataclass
class Dependency:
    """Application dependency definition"""

    name: str
    required: bool = True
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    check_func: Optional[Callable[[], bool]] = None
    install_command: Optional[str] = None

    def check(self) -> DependencyStatus:
        """Check dependency status"""
        if self.check_func:
            try:
                if self.check_func():
                    return DependencyStatus.SATISFIED
                else:
                    return DependencyStatus.MISSING
            except Exception:
                return DependencyStatus.MISSING

        # Default to checking if module can be imported
        try:
            import importlib

            importlib.import_module(self.name)
            return DependencyStatus.SATISFIED
        except ImportError:
            return DependencyStatus.MISSING


@dataclass
class ResourceMetrics:
    """System resource metrics"""

    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_usage_percent: float
    open_files: int
    threads: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceMetrics:
    """Application performance metrics"""

    startup_time: Optional[float] = None
    requests_processed: int = 0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    uptime: Optional[timedelta] = None
    resource_metrics: Optional[ResourceMetrics] = None


class ResourceMonitor:
    """Monitors system resources and performance"""

    def __init__(self, threshold_cpu: float = 80.0, threshold_memory: float = 80.0):
        self.threshold_cpu = threshold_cpu
        self.threshold_memory = threshold_memory
        self.process = psutil.Process()
        self._monitoring = False
        self._monitor_thread = None
        self._callbacks: List[Callable[[ResourceMetrics], None]] = []
        self._metrics_history: List[ResourceMetrics] = []
        self._max_history = 100

    def start_monitoring(self, interval: int = 5):
        """Start resource monitoring"""
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,), daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Started resource monitoring with {interval}s interval")

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Stopped resource monitoring")

    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                metrics = self.collect_metrics()

                # Store in history
                self._metrics_history.append(metrics)
                if len(self._metrics_history) > self._max_history:
                    self._metrics_history.pop(0)

                # Check thresholds
                if metrics.cpu_percent > self.threshold_cpu:
                    logger.warning(f"High CPU usage: {metrics.cpu_percent:.1f}%")

                if metrics.memory_percent > self.threshold_memory:
                    logger.warning(f"High memory usage: {metrics.memory_percent:.1f}%")

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logger.error(f"Resource monitor callback failed: {e}")

            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")

            time.sleep(interval)

    def collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        try:
            # CPU usage
            cpu_percent = self.process.cpu_percent(interval=0.1)

            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self.process.memory_percent()

            # Disk usage (for working directory)
            disk_usage = psutil.disk_usage(os.getcwd())
            disk_percent = disk_usage.percent

            # Open files and threads
            open_files = len(self.process.open_files())
            threads = self.process.num_threads()

            return ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                disk_usage_percent=disk_percent,
                open_files=open_files,
                threads=threads,
            )

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return ResourceMetrics(0, 0, 0, 0, 0, 0)

    def add_callback(self, callback: Callable[[ResourceMetrics], None]):
        """Add resource monitoring callback"""
        self._callbacks.append(callback)

    def get_average_metrics(self) -> Optional[ResourceMetrics]:
        """Get average metrics from history"""
        if not self._metrics_history:
            return None

        avg_cpu = sum(m.cpu_percent for m in self._metrics_history) / len(self._metrics_history)
        avg_memory_pct = sum(m.memory_percent for m in self._metrics_history) / len(
            self._metrics_history
        )
        avg_memory_mb = sum(m.memory_mb for m in self._metrics_history) / len(self._metrics_history)

        return ResourceMetrics(
            cpu_percent=avg_cpu,
            memory_percent=avg_memory_pct,
            memory_mb=avg_memory_mb,
            disk_usage_percent=self._metrics_history[-1].disk_usage_percent,
            open_files=self._metrics_history[-1].open_files,
            threads=self._metrics_history[-1].threads,
        )


class EnvironmentDetector:
    """Detects and adapts to runtime environment"""

    @staticmethod
    def detect_environment() -> Dict[str, Any]:
        """Detect runtime environment details"""
        env = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "is_virtual": EnvironmentDetector._is_virtual_env(),
            "is_docker": EnvironmentDetector._is_docker(),
            "is_pyinstaller": EnvironmentDetector._is_pyinstaller(),
            "display_available": EnvironmentDetector._has_display(),
        }

        # Memory info
        try:
            memory = psutil.virtual_memory()
            env["total_memory_gb"] = memory.total / 1024 / 1024 / 1024
            env["available_memory_gb"] = memory.available / 1024 / 1024 / 1024
        except Exception:
            env["total_memory_gb"] = None
            env["available_memory_gb"] = None

        return env

    @staticmethod
    def _is_virtual_env() -> bool:
        """Check if running in virtual environment"""
        return (
            hasattr(sys, "real_prefix")
            or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
            or os.environ.get("VIRTUAL_ENV") is not None
        )

    @staticmethod
    def _is_docker() -> bool:
        """Check if running in Docker"""
        return os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER") is not None

    @staticmethod
    def _is_pyinstaller() -> bool:
        """Check if running as PyInstaller bundle"""
        return hasattr(sys, "_MEIPASS")

    @staticmethod
    def _has_display() -> bool:
        """Check if display is available"""
        if platform.system() == "Windows":
            return True
        else:
            return os.environ.get("DISPLAY") is not None


class PluginInterface(ABC):
    """Base interface for application plugins"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""
        pass

    @abstractmethod
    async def initialize(self, app: "ApplicationLifecycleManager"):
        """Initialize plugin"""
        pass

    @abstractmethod
    async def shutdown(self):
        """Shutdown plugin"""
        pass


class ApplicationLifecycleManager:
    """Main application lifecycle manager"""

    def __init__(
        self,
        app_name: str = "CodeTranslator",
        config_dir: Optional[Path] = None,
        enable_monitoring: bool = True,
    ):
        self.app_name = app_name
        self.state = ApplicationState.UNINITIALIZED
        self.start_time = None
        self.config_dir = config_dir or Path.home() / ".config" / app_name

        # Core components
        self.config_manager: Optional[ConfigurationManager] = None
        self.error_handler: Optional[ErrorHandler] = None
        self.provider_registry: Optional[ProviderRegistry] = None
        self.resource_monitor: Optional[ResourceMonitor] = None

        # Dependencies
        self.dependencies: List[Dependency] = []
        self._setup_dependencies()

        # Plugins
        self.plugins: Dict[str, PluginInterface] = {}

        # Resource management
        self._cleanup_functions: List[Callable] = []
        self._shutdown_event = threading.Event()

        # Performance tracking
        self._startup_start_time = time.time()

        # Environment
        self.environment = EnvironmentDetector.detect_environment()

        # Monitoring
        if enable_monitoring:
            self.resource_monitor = ResourceMonitor()

    def _setup_dependencies(self):
        """Setup application dependencies"""
        # Core dependencies
        self.dependencies.extend(
            [
                Dependency(
                    name="PyQt6",
                    required=True,
                    min_version="6.5.0",
                    install_command="pip install PyQt6>=6.5.0",
                ),
                Dependency(
                    name="cryptography",
                    required=True,
                    min_version="41.0.0",
                    install_command="pip install cryptography>=41.0.0",
                ),
                Dependency(name="requests", required=True, install_command="pip install requests"),
                Dependency(name="pyyaml", required=True, install_command="pip install pyyaml"),
            ]
        )

        # Optional AI provider dependencies
        self.dependencies.extend(
            [
                Dependency(name="openai", required=False, install_command="pip install openai"),
                Dependency(
                    name="anthropic", required=False, install_command="pip install anthropic"
                ),
                Dependency(
                    name="google.generativeai",
                    required=False,
                    install_command="pip install google-generativeai",
                ),
            ]
        )

    async def initialize(self) -> bool:
        """Initialize application"""
        try:
            self.state = ApplicationState.INITIALIZING
            logger.info(f"Initializing {self.app_name}")

            # Check dependencies
            if not self._check_dependencies():
                self.state = ApplicationState.ERROR
                return False

            # Initialize error handler
            self.error_handler = ErrorHandler(
                app_name=self.app_name, log_dir=self.config_dir / "logs"
            )

            # Initialize configuration
            self.config_manager = ConfigurationManager(config_dir=self.config_dir)

            # Initialize provider registry
            self.provider_registry = ProviderRegistry()
            await self._initialize_providers()

            # Initialize plugins
            await self._initialize_plugins()

            # Setup signal handlers
            self._setup_signal_handlers()

            # Register cleanup
            atexit.register(self._cleanup)

            # Start monitoring
            if self.resource_monitor:
                self.resource_monitor.start_monitoring()

            # Record startup time
            self._startup_time = time.time() - self._startup_start_time

            self.state = ApplicationState.READY
            self.start_time = datetime.now()

            logger.info(f"{self.app_name} initialized successfully in {self._startup_time:.2f}s")
            return True

        except Exception as e:
            self.state = ApplicationState.ERROR
            logger.error(f"Initialization failed: {e}")
            if self.error_handler:
                self.error_handler.handle_error(
                    e,
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.CRITICAL,
                    component="lifecycle_manager",
                )
            return False

    def _check_dependencies(self) -> bool:
        """Check and validate dependencies"""
        logger.info("Checking dependencies...")

        all_satisfied = True
        missing_required = []

        for dep in self.dependencies:
            status = dep.check()

            if status != DependencyStatus.SATISFIED:
                if dep.required:
                    all_satisfied = False
                    missing_required.append(dep)
                    logger.error(f"Required dependency '{dep.name}' is {status.value}")
                else:
                    logger.warning(f"Optional dependency '{dep.name}' is {status.value}")

        if missing_required:
            logger.error("Missing required dependencies:")
            for dep in missing_required:
                logger.error(f"  - {dep.name}: {dep.install_command}")

        return all_satisfied

    async def _initialize_providers(self):
        """Initialize API providers"""
        logger.info("Initializing providers...")

        # Discover available providers
        self.provider_registry.discover_providers()

        # Initialize configured providers
        config = self.config_manager.get_all()

        provider_configs = {
            "openai": {"api_key": config.get("openai_api_key")},
            "anthropic": {"api_key": config.get("anthropic_api_key")},
            "google": {"api_key": config.get("google_api_key")},
            "offline": {},
        }

        for name, provider_config in provider_configs.items():
            if name == "offline" or (provider_config.get("api_key")):
                try:
                    await self.provider_registry.create_provider(name, provider_config)
                    logger.info(f"Initialized {name} provider")
                except Exception as e:
                    logger.warning(f"Failed to initialize {name} provider: {e}")

    async def _initialize_plugins(self):
        """Initialize plugins"""
        # Plugin initialization would be implemented here
        pass

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self._shutdown_event.set()
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        if hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, signal_handler)

    def register_cleanup(self, cleanup_func: Callable):
        """Register cleanup function"""
        self._cleanup_functions.append(cleanup_func)

    def add_plugin(self, plugin: PluginInterface):
        """Add plugin to application"""
        self.plugins[plugin.name] = plugin

    async def run(self):
        """Run application main loop"""
        if self.state != ApplicationState.READY:
            raise RuntimeError(f"Application not ready. Current state: {self.state}")

        self.state = ApplicationState.RUNNING
        logger.info(f"{self.app_name} is running")

        # Main application loop would be implemented here
        # For now, just wait for shutdown signal
        await self._shutdown_event.wait()

    async def shutdown(self):
        """Graceful shutdown"""
        if self.state == ApplicationState.SHUTTING_DOWN:
            return

        logger.info(f"Shutting down {self.app_name}")
        self.state = ApplicationState.SHUTTING_DOWN

        try:
            # Stop monitoring
            if self.resource_monitor:
                self.resource_monitor.stop_monitoring()

            # Shutdown plugins
            for plugin in self.plugins.values():
                try:
                    await plugin.shutdown()
                except Exception as e:
                    logger.error(f"Plugin {plugin.name} shutdown failed: {e}")

            # Shutdown providers
            if self.provider_registry:
                await self.provider_registry.shutdown()

            # Run cleanup functions
            for cleanup in reversed(self._cleanup_functions):
                try:
                    cleanup()
                except Exception as e:
                    logger.error(f"Cleanup function failed: {e}")

            self.state = ApplicationState.SHUTDOWN
            logger.info(f"{self.app_name} shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self.state = ApplicationState.ERROR

    def _cleanup(self):
        """Final cleanup on exit"""
        if self.state != ApplicationState.SHUTDOWN:
            # Force synchronous shutdown
            asyncio.run(self.shutdown())

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        metrics = PerformanceMetrics()

        if self._startup_time:
            metrics.startup_time = self._startup_time

        if self.start_time:
            metrics.uptime = datetime.now() - self.start_time

        if self.resource_monitor:
            metrics.resource_metrics = self.resource_monitor.get_average_metrics()

        if self.error_handler:
            stats = self.error_handler.get_telemetry_stats()
            if stats:
                metrics.error_rate = stats.get("error_rate", 0.0)

        return metrics

    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status"""
        health = {
            "status": self.state.value,
            "healthy": self.state in [ApplicationState.READY, ApplicationState.RUNNING],
            "uptime": str(datetime.now() - self.start_time) if self.start_time else None,
            "environment": self.environment,
        }

        # Add provider health
        if self.provider_registry:
            providers_health = {}
            for name, provider in self.provider_registry.get_all_providers().items():
                providers_health[name] = {
                    "status": provider.get_status().value,
                    "metrics": {
                        "success_rate": provider.metrics.success_rate,
                        "average_latency": provider.metrics.average_latency,
                    },
                }
            health["providers"] = providers_health

        # Add resource health
        if self.resource_monitor:
            current_metrics = self.resource_monitor.collect_metrics()
            health["resources"] = {
                "cpu_percent": current_metrics.cpu_percent,
                "memory_percent": current_metrics.memory_percent,
                "memory_mb": current_metrics.memory_mb,
            }

        return health

    @contextmanager
    def graceful_degradation(self, feature: str):
        """Context manager for graceful degradation"""
        try:
            yield
        except Exception as e:
            logger.warning(f"Feature '{feature}' degraded due to error: {e}")
            if self.error_handler:
                self.error_handler.handle_error(
                    e, category=ErrorCategory.SYSTEM, severity=ErrorSeverity.MEDIUM, feature=feature
                )

            # Set application to degraded state if not critical
            if self.state == ApplicationState.RUNNING:
                self.state = ApplicationState.DEGRADED
