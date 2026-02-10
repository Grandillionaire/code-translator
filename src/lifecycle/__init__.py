"""
Application Lifecycle Management
Initialization, resource monitoring, and graceful shutdown
"""

from .app_manager import (
    ApplicationLifecycleManager,
    ApplicationState,
    Dependency,
    DependencyStatus,
    ResourceMonitor,
    ResourceMetrics,
    PerformanceMetrics,
    EnvironmentDetector,
    PluginInterface,
)

__all__ = [
    "ApplicationLifecycleManager",
    "ApplicationState",
    "Dependency",
    "DependencyStatus",
    "ResourceMonitor",
    "ResourceMetrics",
    "PerformanceMetrics",
    "EnvironmentDetector",
    "PluginInterface",
]
