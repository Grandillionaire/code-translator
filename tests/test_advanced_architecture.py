"""
Integration tests for advanced architecture components
"""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import json

from config.config_manager import (
    ConfigurationManager, StorageBackend, ConfigSchema, 
    ConfigTransaction, ConfigCorruptionError
)
from providers.provider_framework import (
    ProviderRegistry, ProviderStatus, CircuitBreaker,
    RateLimiter, ProviderChain, LoadBalancer
)
from providers.implementations import MockProvider
from error_handling.error_framework import (
    ErrorHandler, ErrorCategory, ErrorSeverity
)
from lifecycle.app_manager import (
    ApplicationLifecycleManager, ApplicationState
)


class TestConfigurationManager:
    """Test advanced configuration management"""
    
    def test_atomic_transactions(self):
        """Test atomic configuration transactions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            manager = ConfigurationManager(config_dir)
            
            # Set initial values
            manager.set("key1", "value1")
            manager.set("key2", "value2")
            
            # Test successful transaction
            with manager.transaction() as tx:
                tx.set("key1", "new_value1")
                tx.set("key3", "value3")
                tx.commit()
            
            assert manager.get("key1") == "new_value1"
            assert manager.get("key3") == "value3"
            
            # Test failed transaction with rollback
            with pytest.raises(Exception):
                with manager.transaction() as tx:
                    tx.set("key1", "failed_value")
                    tx.set("key2", "failed_value")
                    raise Exception("Simulated error")
            
            # Values should be unchanged
            assert manager.get("key1") == "new_value1"
            assert manager.get("key2") == "value2"
    
    def test_corruption_recovery(self):
        """Test configuration corruption detection and recovery"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            manager = ConfigurationManager(config_dir)
            
            # Save valid config
            manager.set("test_key", "test_value")
            
            # Corrupt the config file
            config_path = manager._config_path
            with open(config_path, 'w') as f:
                f.write("{ invalid json }")
            
            # Reload should recover from backup
            manager2 = ConfigurationManager(config_dir)
            
            # Should have default values after corruption
            assert manager2.get("theme") == "dark"  # Default value
    
    def test_schema_validation(self):
        """Test schema validation"""
        schema = ConfigSchema(
            version="1.0.0",
            fields={
                "port": {"type": int, "min": 1, "max": 65535},
                "host": {"type": str},
                "debug": {"type": bool}
            },
            required=["port", "host"]
        )
        
        # Valid data
        valid_data = {"port": 8080, "host": "localhost", "debug": True}
        errors = schema.validate(valid_data)
        assert len(errors) == 0
        
        # Invalid data
        invalid_data = {"port": 70000, "debug": "not_bool"}
        errors = schema.validate(invalid_data)
        assert len(errors) > 0
        assert any("port" in e and "exceeds maximum" in e for e in errors)
        assert any("host" in e and "missing" in e for e in errors)
    
    def test_multi_backend_support(self):
        """Test different storage backends"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            
            # Test JSON backend
            json_manager = ConfigurationManager(
                config_dir / "json",
                backend=StorageBackend.JSON
            )
            json_manager.set("format", "json")
            
            # Test YAML backend
            yaml_manager = ConfigurationManager(
                config_dir / "yaml",
                backend=StorageBackend.YAML
            )
            yaml_manager.set("format", "yaml")
            
            # Test SQLite backend
            sqlite_manager = ConfigurationManager(
                config_dir / "sqlite",
                backend=StorageBackend.SQLITE
            )
            sqlite_manager.set("format", "sqlite")
            
            # Verify each backend works correctly
            assert json_manager.get("format") == "json"
            assert yaml_manager.get("format") == "yaml"
            assert sqlite_manager.get("format") == "sqlite"


class TestProviderFramework:
    """Test provider framework components"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        breaker = CircuitBreaker()
        call_count = 0
        
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Simulated failure")
        
        # Test failures open the circuit
        for i in range(5):
            with pytest.raises(Exception):
                await breaker.async_call(failing_function)
        
        # Circuit should be open now
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.async_call(failing_function)
        
        # Verify function wasn't called when circuit was open
        assert call_count == 5
    
    def test_rate_limiter(self):
        """Test rate limiter"""
        limiter = RateLimiter(rate=2, burst=4)  # 2 per second, burst of 4
        
        # Should allow burst
        for i in range(4):
            assert limiter.acquire(blocking=False)
        
        # Should be exhausted
        assert not limiter.acquire(blocking=False)
        
        # Wait and try again
        import time
        time.sleep(0.5)  # Should restore 1 token
        assert limiter.acquire(blocking=False)
    
    @pytest.mark.asyncio
    async def test_provider_chain_fallback(self):
        """Test provider chain with fallback"""
        # Create mock providers
        provider1 = MockProvider({"fail_rate": 1.0})  # Always fails
        provider2 = MockProvider({"fail_rate": 0.5})  # Sometimes fails
        provider3 = MockProvider({"fail_rate": 0.0})  # Never fails
        
        await provider1.initialize()
        await provider2.initialize()
        await provider3.initialize()
        
        chain = ProviderChain([provider1, provider2, provider3])
        
        # Should fallback to provider3
        result = await chain.execute("translate_code", "test", "Python", "JavaScript")
        assert result is not None
    
    def test_load_balancer(self):
        """Test load balancer strategies"""
        providers = [
            MockProvider({"name": "provider1"}),
            MockProvider({"name": "provider2"}),
            MockProvider({"name": "provider3"})
        ]
        
        # Test round-robin
        balancer = LoadBalancer(providers, strategy="round_robin")
        selected = []
        for i in range(6):
            provider = balancer.select_provider()
            selected.append(providers.index(provider))
        
        # Should cycle through providers
        assert selected == [0, 1, 2, 0, 1, 2]


class TestErrorHandling:
    """Test error handling framework"""
    
    def test_error_classification(self):
        """Test automatic error classification"""
        handler = ErrorHandler()
        
        # Network error
        network_error = Exception("Connection timeout")
        info = handler.handle_error(network_error)
        assert info.category == ErrorCategory.NETWORK
        
        # Auth error
        auth_error = Exception("401 Unauthorized")
        info = handler.handle_error(auth_error)
        assert info.category == ErrorCategory.AUTHENTICATION
        
        # Rate limit error
        rate_error = Exception("429 Too Many Requests")
        info = handler.handle_error(rate_error)
        assert info.category == ErrorCategory.RATE_LIMIT
    
    def test_error_telemetry(self):
        """Test error telemetry collection"""
        handler = ErrorHandler(enable_telemetry=True)
        
        # Generate some errors
        for i in range(10):
            try:
                raise ValueError(f"Test error {i}")
            except Exception as e:
                handler.handle_error(e)
        
        # Check telemetry
        stats = handler.get_telemetry_stats()
        assert stats["total_errors"] == 10
        assert "ValueError" in stats["top_errors"]
    
    def test_user_friendly_messages(self):
        """Test user-friendly error messages"""
        handler = ErrorHandler()
        
        # Technical error
        error = ConnectionError("Failed to connect to api.openai.com:443")
        info = handler.handle_error(error, category=ErrorCategory.NETWORK)
        
        # Should have user-friendly message
        assert "internet connection" in info.user_message.lower()
        assert "api.openai.com" not in info.user_message  # Technical details hidden
    
    def test_structured_logging(self):
        """Test structured logging output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            handler = ErrorHandler(log_dir=log_dir)
            
            # Generate error
            try:
                raise Exception("Test error for logging")
            except Exception as e:
                info = handler.handle_error(
                    e,
                    component="test_component",
                    operation="test_operation",
                    user_id="test_user"
                )
            
            # Check log file was created
            log_files = list(log_dir.glob("structured_*.jsonl"))
            assert len(log_files) > 0
            
            # Verify structured format
            with open(log_files[0]) as f:
                log_entry = json.loads(f.read().strip())
                assert log_entry["type"] == "error"
                assert "correlation_id" in log_entry["data"]["context"]


class TestLifecycleManagement:
    """Test application lifecycle management"""
    
    @pytest.mark.asyncio
    async def test_initialization_sequence(self):
        """Test proper initialization sequence"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ApplicationLifecycleManager(
                config_dir=Path(tmpdir),
                enable_monitoring=False  # Disable for testing
            )
            
            assert manager.state == ApplicationState.UNINITIALIZED
            
            # Mock dependencies
            with patch.object(manager, '_check_dependencies', return_value=True):
                success = await manager.initialize()
                assert success
                assert manager.state == ApplicationState.READY
    
    def test_environment_detection(self):
        """Test environment detection"""
        from lifecycle.app_manager import EnvironmentDetector
        
        env = EnvironmentDetector.detect_environment()
        
        # Should detect basic environment info
        assert "platform" in env
        assert "python_version" in env
        assert "cpu_count" in env
        assert isinstance(env["is_virtual"], bool)
        assert isinstance(env["is_docker"], bool)
    
    def test_resource_monitoring(self):
        """Test resource monitoring"""
        from lifecycle.app_manager import ResourceMonitor
        
        monitor = ResourceMonitor()
        metrics = monitor.collect_metrics()
        
        # Should collect metrics
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.memory_mb > 0
        assert metrics.threads > 0
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Test graceful shutdown"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ApplicationLifecycleManager(
                config_dir=Path(tmpdir),
                enable_monitoring=False
            )
            
            # Initialize
            with patch.object(manager, '_check_dependencies', return_value=True):
                await manager.initialize()
            
            # Register cleanup
            cleanup_called = False
            def cleanup():
                nonlocal cleanup_called
                cleanup_called = True
            
            manager.register_cleanup(cleanup)
            
            # Shutdown
            await manager.shutdown()
            
            assert manager.state == ApplicationState.SHUTDOWN
            assert cleanup_called


@pytest.mark.asyncio
async def test_full_integration():
    """Test full integration of all components"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        
        # 1. Initialize lifecycle manager
        lifecycle = ApplicationLifecycleManager(
            app_name="TestApp",
            config_dir=config_dir,
            enable_monitoring=True
        )
        
        with patch.object(lifecycle, '_check_dependencies', return_value=True):
            await lifecycle.initialize()
        
        # 2. Get components
        config = lifecycle.config_manager
        error_handler = lifecycle.error_handler
        
        # 3. Test configuration with transaction
        with config.transaction() as tx:
            tx.set("test_key", "test_value")
            tx.set("api_key", "secret123")
            tx.commit()
        
        # 4. Test error handling
        try:
            raise ConnectionError("Network unreachable")
        except Exception as e:
            error_info = error_handler.handle_error(e)
            assert error_info.category == ErrorCategory.NETWORK
        
        # 5. Check health status
        health = lifecycle.get_health_status()
        assert health["healthy"]
        assert health["status"] == "ready"
        
        # 6. Graceful shutdown
        await lifecycle.shutdown()
        assert lifecycle.state == ApplicationState.SHUTDOWN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])