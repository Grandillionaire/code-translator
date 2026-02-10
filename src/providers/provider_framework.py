"""
Intelligent API Provider Architecture
Provides dynamic discovery, version compatibility, circuit breakers, and automatic failover
"""

import asyncio
import importlib
import inspect
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Tuple, Callable, Union
from collections import deque
import threading
import queue
import logging
from contextlib import asynccontextmanager
import aiohttp
import requests

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Provider health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RequestPriority(Enum):
    """Request priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ProviderMetrics:
    """Provider performance metrics"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    error_counts: Dict[str, int] = field(default_factory=dict)
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def average_latency(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency / self.successful_requests


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5
    recovery_timeout: timedelta = timedelta(seconds=60)
    success_threshold: int = 2
    half_open_max_requests: int = 3


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance"""

    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_requests = 0
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        with self._lock:
            if not self._can_execute():
                raise Exception(f"Circuit breaker is OPEN")

            if self.state == CircuitBreakerState.HALF_OPEN:
                self.half_open_requests += 1

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function through circuit breaker"""
        with self._lock:
            if not self._can_execute():
                raise Exception(f"Circuit breaker is OPEN")

            if self.state == CircuitBreakerState.HALF_OPEN:
                self.half_open_requests += 1

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if (
                self.last_failure_time
                and datetime.now() - self.last_failure_time > self.config.recovery_timeout
            ):
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_requests = 0
                return True
            return False

        # Half-open state
        return self.half_open_requests < self.config.half_open_max_requests

    def _on_success(self):
        """Handle successful request"""
        with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info("Circuit breaker closed (recovered)")
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = 0

    def _on_failure(self):
        """Handle failed request"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitBreakerState.OPEN
                    logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            elif self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                self.success_count = 0
                logger.warning("Circuit breaker reopened during recovery")


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, rate: int, burst: int):
        """
        Args:
            rate: Tokens per second
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self._lock = threading.Lock()

    def acquire(self, tokens: int = 1, blocking: bool = True) -> bool:
        """Acquire tokens from bucket"""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # Add tokens based on elapsed time
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            if blocking:
                # Calculate wait time
                wait_time = (tokens - self.tokens) / self.rate
                time.sleep(wait_time)
                self.tokens = 0
                return True

            return False


class PriorityQueue:
    """Priority queue for request scheduling"""

    def __init__(self, maxsize: int = 0):
        self.queues = {priority: queue.Queue(maxsize=maxsize) for priority in RequestPriority}
        self._semaphore = threading.Semaphore(0)

    def put(self, item: Any, priority: RequestPriority = RequestPriority.NORMAL):
        """Add item to queue with priority"""
        self.queues[priority].put(item)
        self._semaphore.release()

    def get(self, timeout: Optional[float] = None) -> Any:
        """Get highest priority item"""
        if not self._semaphore.acquire(timeout=timeout):
            raise queue.Empty("Queue is empty")

        # Check queues in priority order
        for priority in sorted(RequestPriority, key=lambda p: p.value, reverse=True):
            try:
                return self.queues[priority].get_nowait()
            except queue.Empty:
                continue

        raise queue.Empty("Queue is empty")

    def empty(self) -> bool:
        """Check if all queues are empty"""
        return all(q.empty() for q in self.queues.values())


@dataclass
class ProviderCapabilities:
    """Defines provider capabilities and features"""

    supported_models: List[str] = field(default_factory=list)
    max_tokens: int = 4096
    supports_streaming: bool = False
    supports_functions: bool = False
    supports_vision: bool = False
    rate_limits: Dict[str, int] = field(default_factory=dict)
    version_info: Dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract base class for API providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.metrics = ProviderMetrics()
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = self._init_rate_limiter()
        self._health_check_task: Optional[asyncio.Task] = None
        self._status = ProviderStatus.UNKNOWN
        self._capabilities: Optional[ProviderCapabilities] = None

    def _init_rate_limiter(self) -> Optional[RateLimiter]:
        """Initialize rate limiter based on provider limits"""
        rate_limit = self.config.get("rate_limit")
        if rate_limit:
            return RateLimiter(rate=rate_limit.get("rate", 10), burst=rate_limit.get("burst", 20))
        return None

    @abstractmethod
    async def initialize(self):
        """Initialize provider and verify configuration"""
        pass

    @abstractmethod
    async def translate_code(
        self, code: str, source_lang: str, target_lang: str, **kwargs
    ) -> Tuple[str, float]:
        """Translate code between languages"""
        pass

    @abstractmethod
    async def health_check(self) -> ProviderStatus:
        """Check provider health status"""
        pass

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities"""
        pass

    async def execute_with_resilience(
        self, func: Callable, *args, priority: RequestPriority = RequestPriority.NORMAL, **kwargs
    ) -> Any:
        """Execute function with resilience patterns"""
        # Rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire()

        # Circuit breaker
        start_time = time.time()

        try:
            result = await self.circuit_breaker.async_call(func, *args, **kwargs)

            # Update metrics
            latency = time.time() - start_time
            self.metrics.successful_requests += 1
            self.metrics.total_requests += 1
            self.metrics.total_latency += latency
            self.metrics.last_success = datetime.now()

            return result

        except Exception as e:
            # Update metrics
            self.metrics.failed_requests += 1
            self.metrics.total_requests += 1
            self.metrics.last_failure = datetime.now()

            error_type = type(e).__name__
            self.metrics.error_counts[error_type] = self.metrics.error_counts.get(error_type, 0) + 1

            raise

    async def start_health_monitoring(self, interval: int = 60):
        """Start background health monitoring"""

        async def monitor():
            while True:
                try:
                    self._status = await self.health_check()
                except Exception as e:
                    logger.error(f"Health check failed for {self.name}: {e}")
                    self._status = ProviderStatus.UNHEALTHY

                await asyncio.sleep(interval)

        self._health_check_task = asyncio.create_task(monitor())

    async def stop_health_monitoring(self):
        """Stop health monitoring"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

    def get_status(self) -> ProviderStatus:
        """Get current provider status"""
        return self._status

    def get_metrics(self) -> ProviderMetrics:
        """Get provider metrics"""
        return self.metrics


class ProviderRegistry:
    """Registry for dynamic provider discovery and management"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.providers: Dict[str, Type[BaseProvider]] = {}
            self.provider_instances: Dict[str, BaseProvider] = {}
            self._initialized = True

    def register(self, name: str, provider_class: Type[BaseProvider]):
        """Register a provider class"""
        if not issubclass(provider_class, BaseProvider):
            raise TypeError(f"{provider_class} must inherit from BaseProvider")

        self.providers[name] = provider_class
        logger.info(f"Registered provider: {name}")

    def discover_providers(self, module_path: str = "providers.implementations"):
        """Automatically discover and register providers"""
        try:
            module = importlib.import_module(module_path)

            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseProvider) and obj != BaseProvider:
                    provider_name = obj.__name__.replace("Provider", "").lower()
                    self.register(provider_name, obj)

        except ImportError as e:
            logger.warning(f"Failed to discover providers from {module_path}: {e}")

    async def create_provider(self, name: str, config: Dict[str, Any]) -> BaseProvider:
        """Create and initialize a provider instance"""
        if name not in self.providers:
            raise ValueError(f"Unknown provider: {name}")

        provider_class = self.providers[name]
        provider = provider_class(config)

        try:
            await provider.initialize()
            self.provider_instances[name] = provider

            # Start health monitoring
            await provider.start_health_monitoring()

            return provider

        except Exception as e:
            logger.error(f"Failed to initialize provider {name}: {e}")
            raise

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get an initialized provider instance"""
        return self.provider_instances.get(name)

    def get_all_providers(self) -> Dict[str, BaseProvider]:
        """Get all initialized providers"""
        return self.provider_instances.copy()

    def get_healthy_providers(self) -> List[BaseProvider]:
        """Get list of healthy providers"""
        return [
            provider
            for provider in self.provider_instances.values()
            if provider.get_status() == ProviderStatus.HEALTHY
        ]

    async def shutdown(self):
        """Shutdown all providers"""
        for provider in self.provider_instances.values():
            await provider.stop_health_monitoring()

        self.provider_instances.clear()


class ProviderChain:
    """Manages fallback chain of providers"""

    def __init__(self, providers: List[BaseProvider]):
        self.providers = providers
        self._last_used_index = 0

    async def execute(
        self, func_name: str, *args, priority: RequestPriority = RequestPriority.NORMAL, **kwargs
    ) -> Any:
        """Execute function with automatic fallback"""
        exceptions = []

        # Try each provider in order
        for i, provider in enumerate(self.providers):
            try:
                # Skip unhealthy providers
                if provider.get_status() == ProviderStatus.UNHEALTHY:
                    continue

                # Get the provider method
                if not hasattr(provider, func_name):
                    continue

                func = getattr(provider, func_name)

                # Execute with resilience
                result = await provider.execute_with_resilience(
                    func, *args, priority=priority, **kwargs
                )

                self._last_used_index = i
                return result

            except Exception as e:
                exceptions.append((provider.name, e))
                logger.warning(f"Provider {provider.name} failed: {e}")

        # All providers failed
        raise Exception(f"All providers failed: {exceptions}")

    def get_primary_provider(self) -> Optional[BaseProvider]:
        """Get the current primary provider"""
        return self.providers[0] if self.providers else None

    def reorder_by_performance(self):
        """Reorder providers based on performance metrics"""

        def provider_score(provider: BaseProvider) -> float:
            metrics = provider.get_metrics()

            # Calculate composite score
            success_rate = metrics.success_rate
            avg_latency = metrics.average_latency

            # Lower latency is better, so invert it
            latency_score = 1.0 / (1.0 + avg_latency) if avg_latency > 0 else 1.0

            # Combine scores (70% success rate, 30% latency)
            return 0.7 * success_rate + 0.3 * latency_score

        # Sort providers by score (highest first)
        self.providers.sort(key=provider_score, reverse=True)


class LoadBalancer:
    """Load balancer for distributing requests across providers"""

    def __init__(self, providers: List[BaseProvider], strategy: str = "round_robin"):
        self.providers = providers
        self.strategy = strategy
        self._index = 0
        self._lock = threading.Lock()

    def select_provider(self) -> Optional[BaseProvider]:
        """Select a provider based on strategy"""
        healthy_providers = [
            p for p in self.providers if p.get_status() != ProviderStatus.UNHEALTHY
        ]

        if not healthy_providers:
            return None

        if self.strategy == "round_robin":
            return self._round_robin(healthy_providers)
        elif self.strategy == "least_loaded":
            return self._least_loaded(healthy_providers)
        elif self.strategy == "best_performance":
            return self._best_performance(healthy_providers)
        else:
            return healthy_providers[0]

    def _round_robin(self, providers: List[BaseProvider]) -> BaseProvider:
        """Round-robin selection"""
        with self._lock:
            provider = providers[self._index % len(providers)]
            self._index += 1
            return provider

    def _least_loaded(self, providers: List[BaseProvider]) -> BaseProvider:
        """Select least loaded provider based on current requests"""
        # This would need implementation of active request tracking
        return min(providers, key=lambda p: p.metrics.total_requests)

    def _best_performance(self, providers: List[BaseProvider]) -> BaseProvider:
        """Select best performing provider"""

        def performance_score(provider: BaseProvider) -> float:
            metrics = provider.get_metrics()
            return metrics.success_rate - (metrics.average_latency / 10.0)

        return max(providers, key=performance_score)


class VersionCompatibilityAdapter:
    """Handles version differences between API clients"""

    def __init__(self, provider_name: str, version: str):
        self.provider_name = provider_name
        self.version = version
        self._adapters: Dict[str, Callable] = {}
        self._init_adapters()

    def _init_adapters(self):
        """Initialize version-specific adapters"""
        # Example: OpenAI version adapters
        if self.provider_name == "openai":
            if self.version.startswith("0."):
                self._adapters["chat_completion"] = self._openai_v0_chat
            else:
                self._adapters["chat_completion"] = self._openai_v1_chat

    def adapt(self, method_name: str, *args, **kwargs) -> Any:
        """Adapt method call for specific version"""
        adapter = self._adapters.get(method_name)
        if adapter:
            return adapter(*args, **kwargs)
        else:
            # Default passthrough
            return (args, kwargs)

    def _openai_v0_chat(self, *args, **kwargs):
        """Adapter for OpenAI v0.x chat completions"""
        # Transform to v0 format
        if "model" in kwargs:
            kwargs["engine"] = kwargs.pop("model")
        return (args, kwargs)

    def _openai_v1_chat(self, *args, **kwargs):
        """Adapter for OpenAI v1.x chat completions"""
        # Transform to v1 format
        if "engine" in kwargs:
            kwargs["model"] = kwargs.pop("engine")
        return (args, kwargs)
