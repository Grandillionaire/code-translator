"""
Enterprise Error Handling Framework
Provides structured logging, error classification, recovery strategies, and telemetry
"""

import asyncio
import json
import logging
import sys
import traceback
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, Callable
import threading
from collections import defaultdict, deque
from contextlib import contextmanager
import inspect


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ErrorCategory(Enum):
    """Error categorization"""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    PROVIDER = "provider"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Available recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    RESET = "reset"
    IGNORE = "ignore"
    USER_INTERVENTION = "user_intervention"
    AUTOMATIC_FIX = "automatic_fix"


@dataclass
class ErrorContext:
    """Contextual information about an error"""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "component": self.component,
            "operation": self.operation,
            "metadata": self.metadata
        }


@dataclass
class ErrorInfo:
    """Comprehensive error information"""
    error: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    stacktrace: Optional[str] = None
    user_message: Optional[str] = None
    technical_details: Dict[str, Any] = field(default_factory=dict)
    recovery_suggestions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.stacktrace is None:
            self.stacktrace = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context.to_dict(),
            "stacktrace": self.stacktrace,
            "user_message": self.user_message,
            "technical_details": self.technical_details,
            "recovery_suggestions": self.recovery_suggestions
        }


class ErrorClassifier:
    """Classifies errors into categories and severities"""
    
    def __init__(self):
        self.rules: List[Tuple[Callable[[Exception], bool], ErrorCategory, ErrorSeverity]] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default classification rules"""
        # Network errors
        self.add_rule(
            lambda e: "timeout" in str(e).lower() or isinstance(e, asyncio.TimeoutError),
            ErrorCategory.NETWORK,
            ErrorSeverity.MEDIUM
        )
        
        self.add_rule(
            lambda e: any(err in str(e).lower() for err in ["connection", "network", "unreachable"]),
            ErrorCategory.NETWORK,
            ErrorSeverity.MEDIUM
        )
        
        # Authentication errors
        self.add_rule(
            lambda e: any(auth in str(e).lower() for auth in ["unauthorized", "authentication", "401", "403"]),
            ErrorCategory.AUTHENTICATION,
            ErrorSeverity.HIGH
        )
        
        # Rate limit errors
        self.add_rule(
            lambda e: any(rate in str(e).lower() for rate in ["rate limit", "429", "too many requests"]),
            ErrorCategory.RATE_LIMIT,
            ErrorSeverity.LOW
        )
        
        # Configuration errors
        self.add_rule(
            lambda e: any(cfg in str(e).lower() for cfg in ["config", "setting", "missing", "invalid"]),
            ErrorCategory.CONFIGURATION,
            ErrorSeverity.HIGH
        )
        
        # Validation errors
        self.add_rule(
            lambda e: isinstance(e, (ValueError, TypeError)) or "validation" in str(e).lower(),
            ErrorCategory.VALIDATION,
            ErrorSeverity.MEDIUM
        )
        
        # System errors
        self.add_rule(
            lambda e: isinstance(e, (OSError, IOError, MemoryError)),
            ErrorCategory.SYSTEM,
            ErrorSeverity.CRITICAL
        )
    
    def add_rule(
        self,
        condition: Callable[[Exception], bool],
        category: ErrorCategory,
        severity: ErrorSeverity
    ):
        """Add a classification rule"""
        self.rules.append((condition, category, severity))
    
    def classify(self, error: Exception) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Classify an error"""
        for condition, category, severity in self.rules:
            try:
                if condition(error):
                    return category, severity
            except Exception:
                continue
        
        # Default classification
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM


class ErrorRecoveryStrategy(ABC):
    """Abstract base class for error recovery strategies"""
    
    @abstractmethod
    async def recover(self, error_info: ErrorInfo) -> bool:
        """Attempt to recover from error. Returns True if successful."""
        pass


class RetryStrategy(ErrorRecoveryStrategy):
    """Retry strategy with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def recover(self, error_info: ErrorInfo) -> bool:
        """Implement retry logic"""
        # This would be implemented by the caller
        # Strategy just provides the parameters
        return True


class FallbackStrategy(ErrorRecoveryStrategy):
    """Fallback to alternative implementation"""
    
    def __init__(self, fallback_func: Callable):
        self.fallback_func = fallback_func
    
    async def recover(self, error_info: ErrorInfo) -> bool:
        """Execute fallback function"""
        try:
            await self.fallback_func(error_info)
            return True
        except Exception:
            return False


class UserMessageFormatter:
    """Formats error messages for end users"""
    
    def __init__(self):
        self.templates = {
            ErrorCategory.NETWORK: "Network connection issue. Please check your internet connection and try again.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your API keys in settings.",
            ErrorCategory.RATE_LIMIT: "Rate limit exceeded. Please wait a moment before trying again.",
            ErrorCategory.CONFIGURATION: "Configuration issue detected. Please check your settings.",
            ErrorCategory.VALIDATION: "Invalid input provided. Please check your data and try again.",
            ErrorCategory.PROVIDER: "Service provider error. The service might be temporarily unavailable.",
            ErrorCategory.SYSTEM: "System error occurred. Please restart the application if the issue persists.",
            ErrorCategory.USER_INPUT: "Invalid input. Please check your code and try again.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again."
        }
    
    def format_message(self, error_info: ErrorInfo) -> str:
        """Format user-friendly error message"""
        base_message = self.templates.get(
            error_info.category,
            self.templates[ErrorCategory.UNKNOWN]
        )
        
        # Add recovery suggestions if available
        if error_info.recovery_suggestions:
            suggestions = "\n\nSuggestions:\n" + "\n".join(
                f"• {s}" for s in error_info.recovery_suggestions
            )
            base_message += suggestions
        
        return base_message


class ErrorTelemetry:
    """Collects and manages error telemetry data"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.error_history: deque = deque(maxlen=max_history)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.category_counts: Dict[ErrorCategory, int] = defaultdict(int)
        self.severity_counts: Dict[ErrorSeverity, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def record_error(self, error_info: ErrorInfo):
        """Record error for telemetry"""
        with self._lock:
            self.error_history.append(error_info)
            
            error_type = type(error_info.error).__name__
            self.error_counts[error_type] += 1
            self.category_counts[error_info.category] += 1
            self.severity_counts[error_info.severity] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        with self._lock:
            total_errors = len(self.error_history)
            
            if total_errors == 0:
                return {
                    "total_errors": 0,
                    "error_rate": 0.0
                }
            
            # Calculate time range
            if self.error_history:
                oldest = self.error_history[0].context.timestamp
                newest = self.error_history[-1].context.timestamp
                time_range = (newest - oldest).total_seconds()
                error_rate = total_errors / max(time_range, 1.0)  # Errors per second
            else:
                error_rate = 0.0
            
            return {
                "total_errors": total_errors,
                "error_rate": error_rate,
                "top_errors": dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
                "category_distribution": dict(self.category_counts),
                "severity_distribution": {k.name: v for k, v in self.severity_counts.items()}
            }
    
    def get_recent_errors(self, count: int = 10) -> List[ErrorInfo]:
        """Get most recent errors"""
        with self._lock:
            return list(self.error_history)[-count:]


class StructuredLogger:
    """Structured logging with correlation IDs and context"""
    
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        self.logger = logging.getLogger(name)
        self.log_dir = log_dir
        
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            self._setup_file_handler()
    
    def _setup_file_handler(self):
        """Setup structured log file handler"""
        log_file = self.log_dir / f"structured_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.DEBUG)
        
        # Custom formatter for structured logs
        handler.setFormatter(StructuredFormatter())
        
        self.logger.addHandler(handler)
    
    def log_error(self, error_info: ErrorInfo):
        """Log structured error information"""
        log_data = {
            "type": "error",
            "data": error_info.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.error(json.dumps(log_data))
    
    @contextmanager
    def correlation_context(self, correlation_id: str):
        """Context manager for correlation ID"""
        # This would integrate with logging framework
        # to automatically add correlation ID to all logs
        yield


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logs"""
    
    def format(self, record):
        # Extract structured data if available
        if hasattr(record, 'structured_data'):
            return json.dumps(record.structured_data)
        
        # Fallback to standard format
        return super().format(record)


class ErrorHandler:
    """Main error handling orchestrator"""
    
    def __init__(
        self,
        app_name: str = "CodeTranslator",
        log_dir: Optional[Path] = None,
        enable_telemetry: bool = True
    ):
        self.app_name = app_name
        self.classifier = ErrorClassifier()
        self.message_formatter = UserMessageFormatter()
        self.telemetry = ErrorTelemetry() if enable_telemetry else None
        self.logger = StructuredLogger(app_name, log_dir)
        self.recovery_strategies: Dict[ErrorCategory, List[ErrorRecoveryStrategy]] = defaultdict(list)
        self._context_stack: List[Dict[str, Any]] = []
        
        # Setup default recovery strategies
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Setup default recovery strategies"""
        # Network errors: retry
        self.add_recovery_strategy(ErrorCategory.NETWORK, RetryStrategy())
        
        # Rate limit: wait and retry
        self.add_recovery_strategy(ErrorCategory.RATE_LIMIT, RetryStrategy(max_retries=5, base_delay=5.0))
    
    def add_recovery_strategy(self, category: ErrorCategory, strategy: ErrorRecoveryStrategy):
        """Add recovery strategy for error category"""
        self.recovery_strategies[category].append(strategy)
    
    @contextmanager
    def error_context(self, **context_data):
        """Context manager for adding error context"""
        self._context_stack.append(context_data)
        try:
            yield
        finally:
            self._context_stack.pop()
    
    def _build_context(self, **kwargs) -> ErrorContext:
        """Build error context from stack and kwargs"""
        # Merge all context data
        merged_context = {}
        for ctx in self._context_stack:
            merged_context.update(ctx)
        merged_context.update(kwargs)
        
        # Extract specific fields
        context = ErrorContext(
            user_id=merged_context.pop('user_id', None),
            session_id=merged_context.pop('session_id', None),
            request_id=merged_context.pop('request_id', None),
            component=merged_context.pop('component', None),
            operation=merged_context.pop('operation', None),
            metadata=merged_context
        )
        
        return context
    
    def handle_error(
        self,
        error: Exception,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None,
        **context_data
    ) -> ErrorInfo:
        """Main error handling method"""
        
        # Auto-classify if not provided
        if category is None or severity is None:
            auto_category, auto_severity = self.classifier.classify(error)
            category = category or auto_category
            severity = severity or auto_severity
        
        # Build error info
        context = self._build_context(**context_data)
        
        # Get calling function info
        frame = inspect.currentframe()
        if frame and frame.f_back:
            func_name = frame.f_back.f_code.co_name
            file_name = frame.f_back.f_code.co_filename
            line_number = frame.f_back.f_lineno
            context.metadata.update({
                "function": func_name,
                "file": file_name,
                "line": line_number
            })
        
        error_info = ErrorInfo(
            error=error,
            category=category,
            severity=severity,
            context=context,
            user_message=user_message or self.message_formatter.format_message(error_info),
            recovery_suggestions=recovery_suggestions or []
        )
        
        # Add technical details
        error_info.technical_details = {
            "error_class": error.__class__.__module__ + "." + error.__class__.__name__,
            "args": str(error.args) if error.args else None,
        }
        
        # Log structured error
        self.logger.log_error(error_info)
        
        # Record telemetry
        if self.telemetry:
            self.telemetry.record_error(error_info)
        
        # Handle based on severity
        if severity == ErrorSeverity.CRITICAL:
            self._handle_critical_error(error_info)
        
        return error_info
    
    def _handle_critical_error(self, error_info: ErrorInfo):
        """Special handling for critical errors"""
        # Could implement alerts, emergency recovery, etc.
        logging.critical(f"CRITICAL ERROR: {error_info.error}")
    
    async def attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """Attempt to recover from error"""
        strategies = self.recovery_strategies.get(error_info.category, [])
        
        for strategy in strategies:
            try:
                if await strategy.recover(error_info):
                    logging.info(f"Successfully recovered from error using {type(strategy).__name__}")
                    return True
            except Exception as e:
                logging.warning(f"Recovery strategy {type(strategy).__name__} failed: {e}")
        
        return False
    
    def get_telemetry_stats(self) -> Optional[Dict[str, Any]]:
        """Get telemetry statistics"""
        if self.telemetry:
            return self.telemetry.get_statistics()
        return None
    
    def create_error_report(self, include_recent: int = 10) -> Dict[str, Any]:
        """Create comprehensive error report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "app_name": self.app_name,
        }
        
        if self.telemetry:
            report["statistics"] = self.telemetry.get_statistics()
            report["recent_errors"] = [
                e.to_dict() for e in self.telemetry.get_recent_errors(include_recent)
            ]
        
        return report


class GracefulDegradation:
    """Manages graceful degradation of functionality"""
    
    def __init__(self):
        self.degraded_features: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def degrade_feature(self, feature: str, reason: str, alternative: Optional[str] = None):
        """Mark a feature as degraded"""
        with self._lock:
            self.degraded_features[feature] = {
                "reason": reason,
                "alternative": alternative,
                "degraded_at": datetime.now(),
            }
    
    def restore_feature(self, feature: str):
        """Restore a degraded feature"""
        with self._lock:
            self.degraded_features.pop(feature, None)
    
    def is_degraded(self, feature: str) -> bool:
        """Check if feature is degraded"""
        with self._lock:
            return feature in self.degraded_features
    
    def get_alternative(self, feature: str) -> Optional[str]:
        """Get alternative for degraded feature"""
        with self._lock:
            info = self.degraded_features.get(feature)
            return info["alternative"] if info else None
    
    @contextmanager
    def feature_fallback(self, feature: str, fallback_func: Callable):
        """Context manager for feature with fallback"""
        if self.is_degraded(feature):
            yield fallback_func
        else:
            yield None