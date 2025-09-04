"""
Enterprise Error Handling Framework
Structured logging, error classification, recovery strategies, and telemetry
"""

from .error_framework import (
    ErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    ErrorInfo,
    ErrorClassifier,
    ErrorRecoveryStrategy,
    RetryStrategy,
    FallbackStrategy,
    RecoveryStrategy,
    UserMessageFormatter,
    ErrorTelemetry,
    StructuredLogger,
    GracefulDegradation
)

__all__ = [
    'ErrorHandler',
    'ErrorCategory',
    'ErrorSeverity',
    'ErrorContext',
    'ErrorInfo',
    'ErrorClassifier',
    'ErrorRecoveryStrategy',
    'RetryStrategy',
    'FallbackStrategy',
    'RecoveryStrategy',
    'UserMessageFormatter',
    'ErrorTelemetry',
    'StructuredLogger',
    'GracefulDegradation',
]