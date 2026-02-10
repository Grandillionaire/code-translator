"""
Advanced Configuration Management System
Provides atomic operations, schema versioning, corruption detection, and automatic recovery
"""

import json
import yaml
import sqlite3
import tempfile
import shutil
import hashlib
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple, Type, Union
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
import logging

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64


logger = logging.getLogger(__name__)


class StorageBackend(Enum):
    """Supported storage backends"""

    JSON = "json"
    YAML = "yaml"
    SQLITE = "sqlite"


class ConfigError(Exception):
    """Base exception for configuration errors"""

    pass


class ConfigCorruptionError(ConfigError):
    """Raised when configuration is corrupted"""

    pass


class SchemaValidationError(ConfigError):
    """Raised when configuration doesn't match schema"""

    pass


@dataclass
class ConfigSchema:
    """Configuration schema definition"""

    version: str
    fields: Dict[str, Dict[str, Any]]
    required: List[str] = field(default_factory=list)
    migrations: Dict[str, "ConfigMigration"] = field(default_factory=dict)

    def validate(self, data: Dict[str, Any]) -> List[str]:
        """Validate data against schema, returns list of errors"""
        errors = []

        # Check required fields
        for field_name in self.required:
            if field_name not in data:
                errors.append(f"Required field '{field_name}' is missing")

        # Validate field types and constraints
        for field_name, field_spec in self.fields.items():
            if field_name in data:
                value = data[field_name]
                expected_type = field_spec.get("type")

                if expected_type and not isinstance(value, expected_type):
                    errors.append(
                        f"Field '{field_name}' has wrong type. "
                        f"Expected {expected_type.__name__}, got {type(value).__name__}"
                    )

                # Check constraints
                if "min" in field_spec and value < field_spec["min"]:
                    errors.append(
                        f"Field '{field_name}' is below minimum value {field_spec['min']}"
                    )

                if "max" in field_spec and value > field_spec["max"]:
                    errors.append(f"Field '{field_name}' exceeds maximum value {field_spec['max']}")

                if "enum" in field_spec and value not in field_spec["enum"]:
                    errors.append(
                        f"Field '{field_name}' has invalid value. Must be one of {field_spec['enum']}"
                    )

        return errors


@dataclass
class ConfigMigration:
    """Defines a migration from one schema version to another"""

    from_version: str
    to_version: str
    migrate_func: callable
    rollback_func: Optional[callable] = None


class ConfigTransaction:
    """Represents an atomic configuration transaction"""

    def __init__(self, config_manager: "ConfigurationManager"):
        self.config_manager = config_manager
        self.changes: Dict[str, Any] = {}
        self.original_values: Dict[str, Any] = {}
        self.committed = False
        self.rolled_back = False

    def set(self, key: str, value: Any):
        """Set a value in the transaction"""
        if self.committed or self.rolled_back:
            raise ConfigError("Transaction already completed")

        if key not in self.original_values:
            self.original_values[key] = self.config_manager.get(key)

        self.changes[key] = value

    def commit(self):
        """Commit all changes atomically"""
        if self.committed or self.rolled_back:
            raise ConfigError("Transaction already completed")

        try:
            # Apply all changes
            for key, value in self.changes.items():
                self.config_manager._set_internal(key, value)

            # Save to storage
            self.config_manager._save()
            self.committed = True

        except Exception as e:
            # Rollback on any error
            self.rollback()
            raise ConfigError(f"Transaction commit failed: {e}") from e

    def rollback(self):
        """Rollback all changes"""
        if self.committed or self.rolled_back:
            return

        try:
            # Restore original values
            for key, value in self.original_values.items():
                if value is not None:
                    self.config_manager._set_internal(key, value)
                else:
                    self.config_manager._delete_internal(key)

            self.rolled_back = True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise


class StorageAdapter(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    def load(self, path: Path) -> Dict[str, Any]:
        """Load configuration from storage"""
        pass

    @abstractmethod
    def save(self, path: Path, data: Dict[str, Any]):
        """Save configuration to storage"""
        pass

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Check if configuration exists"""
        pass


class JsonStorageAdapter(StorageAdapter):
    """JSON file storage adapter"""

    def load(self, path: Path) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigCorruptionError(f"Invalid JSON: {e}") from e

    def save(self, path: Path, data: Dict[str, Any]):
        # Write to temporary file first
        temp_path = path.with_suffix(".tmp")

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                import os

                os.fsync(f.fileno())

            # Atomic rename
            temp_path.replace(path)

        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def exists(self, path: Path) -> bool:
        return path.exists() and path.is_file()


class YamlStorageAdapter(StorageAdapter):
    """YAML file storage adapter"""

    def load(self, path: Path) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigCorruptionError(f"Invalid YAML: {e}") from e

    def save(self, path: Path, data: Dict[str, Any]):
        temp_path = path.with_suffix(".tmp")

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                f.flush()
                import os

                os.fsync(f.fileno())

            temp_path.replace(path)

        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def exists(self, path: Path) -> bool:
        return path.exists() and path.is_file()


class SqliteStorageAdapter(StorageAdapter):
    """SQLite database storage adapter"""

    def __init__(self):
        self._connections: Dict[str, sqlite3.Connection] = {}

    def _get_connection(self, path: Path) -> sqlite3.Connection:
        path_str = str(path)
        if path_str not in self._connections:
            conn = sqlite3.connect(path_str, check_same_thread=False)
            conn.row_factory = sqlite3.Row

            # Create table if needed
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()

            self._connections[path_str] = conn

        return self._connections[path_str]

    def load(self, path: Path) -> Dict[str, Any]:
        conn = self._get_connection(path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT key, value FROM config")
            result = {}

            for row in cursor.fetchall():
                try:
                    result[row["key"]] = json.loads(row["value"])
                except json.JSONDecodeError:
                    # Store as string if not valid JSON
                    result[row["key"]] = row["value"]

            return result

        except sqlite3.Error as e:
            raise ConfigCorruptionError(f"Database error: {e}") from e

    def save(self, path: Path, data: Dict[str, Any]):
        conn = self._get_connection(path)

        try:
            with conn:
                # Clear existing data
                conn.execute("DELETE FROM config")

                # Insert new data
                for key, value in data.items():
                    json_value = json.dumps(value)
                    conn.execute(
                        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                        (key, json_value),
                    )

        except sqlite3.Error as e:
            raise ConfigError(f"Failed to save to database: {e}") from e

    def exists(self, path: Path) -> bool:
        if not path.exists():
            return False

        try:
            conn = self._get_connection(path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config'")
            return cursor.fetchone() is not None
        except sqlite3.Error:
            return False


class SecureCredentialManager:
    """Manages encryption and secure storage of credentials"""

    def __init__(self, key_path: Path, password: Optional[str] = None):
        self.key_path = key_path
        self.cipher = self._init_cipher(password)

    def _init_cipher(self, password: Optional[str] = None) -> Fernet:
        """Initialize encryption cipher"""
        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                key = f.read()
        else:
            if password:
                # Derive key from password
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b"code-translator-salt",  # In production, use random salt
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            else:
                # Generate new random key
                key = Fernet.generate_key()

            # Save key securely
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_path, "wb") as f:
                f.write(key)

            # Set restrictive permissions on Unix-like systems
            import os

            if os.name != "nt":
                os.chmod(self.key_path, 0o600)

        return Fernet(key)

    def encrypt(self, value: str) -> str:
        """Encrypt a string value"""
        if not value:
            return value

        encrypted = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, value: str) -> str:
        """Decrypt a string value"""
        if not value:
            return value

        try:
            encrypted = base64.b64decode(value.encode())
            return self.cipher.decrypt(encrypted).decode()
        except Exception as e:
            logger.warning(f"Failed to decrypt value: {e}")
            return ""


class ConfigurationManager:
    """
    Advanced configuration manager with atomic operations,
    schema versioning, and corruption recovery
    """

    # Default schema for code translator
    DEFAULT_SCHEMA = ConfigSchema(
        version="2.0.0",
        fields={
            # Window settings
            "window_opacity": {"type": float, "min": 0.1, "max": 1.0},
            "theme": {"type": str, "enum": ["light", "dark", "auto"]},
            "start_minimized": {"type": bool},
            # Translation settings
            "auto_detect_language": {"type": bool},
            "save_history": {"type": bool},
            "history_limit": {"type": int, "min": 0, "max": 10000},
            # Editor settings
            "font_size": {"type": int, "min": 8, "max": 72},
            "show_line_numbers": {"type": bool},
            "word_wrap": {"type": bool},
            # API settings
            "preferred_provider": {
                "type": str,
                "enum": ["auto", "openai", "anthropic", "google", "offline"],
            },
            "translation_timeout": {"type": int, "min": 5, "max": 300},
            # Credentials (encrypted)
            "openai_api_key": {"type": str, "encrypted": True},
            "anthropic_api_key": {"type": str, "encrypted": True},
            "google_api_key": {"type": str, "encrypted": True},
            # Behavior settings
            "copy_on_translate": {"type": bool},
            "clear_output_on_input_change": {"type": bool},
            # Advanced settings
            "cache_translations": {"type": bool},
            "max_cache_size": {"type": int, "min": 0, "max": 1000},
            "log_level": {"type": str, "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
        },
        required=["theme", "font_size"],
    )

    def __init__(
        self,
        config_dir: Path,
        backend: StorageBackend = StorageBackend.JSON,
        schema: Optional[ConfigSchema] = None,
        enable_encryption: bool = True,
        password: Optional[str] = None,
    ):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.backend = backend
        self.schema = schema or self.DEFAULT_SCHEMA
        self._data: Dict[str, Any] = {}
        self._lock = threading.RLock()

        # Initialize storage adapter
        self._storage = self._create_storage_adapter()

        # Initialize credential encryption
        if enable_encryption:
            key_path = self.config_dir / ".encryption_key"
            self._credential_manager = SecureCredentialManager(key_path, password)
        else:
            self._credential_manager = None

        # Configuration file paths
        self._config_path = self._get_config_path()
        self._backup_dir = self.config_dir / "backups"
        self._backup_dir.mkdir(exist_ok=True)

        # Load configuration
        self._load()

    def _create_storage_adapter(self) -> StorageAdapter:
        """Create appropriate storage adapter"""
        adapters = {
            StorageBackend.JSON: JsonStorageAdapter,
            StorageBackend.YAML: YamlStorageAdapter,
            StorageBackend.SQLITE: SqliteStorageAdapter,
        }

        adapter_class = adapters.get(self.backend)
        if not adapter_class:
            raise ValueError(f"Unsupported backend: {self.backend}")

        return adapter_class()

    def _get_config_path(self) -> Path:
        """Get configuration file path based on backend"""
        extensions = {
            StorageBackend.JSON: ".json",
            StorageBackend.YAML: ".yaml",
            StorageBackend.SQLITE: ".db",
        }

        return self.config_dir / f"config{extensions[self.backend]}"

    def _load(self):
        """Load configuration with automatic recovery"""
        with self._lock:
            try:
                if self._storage.exists(self._config_path):
                    raw_data = self._storage.load(self._config_path)

                    # Verify integrity
                    if self._verify_integrity(raw_data):
                        self._data = self._decrypt_sensitive_fields(raw_data)

                        # Check if migration needed
                        current_version = self._data.get("_schema_version", "1.0.0")
                        if current_version != self.schema.version:
                            self._migrate(current_version, self.schema.version)
                    else:
                        raise ConfigCorruptionError("Configuration integrity check failed")
                else:
                    # Initialize with defaults
                    self._data = self._get_defaults()
                    self._data["_schema_version"] = self.schema.version
                    self._save()

            except (ConfigCorruptionError, Exception) as e:
                logger.error(f"Configuration load failed: {e}")

                # Attempt recovery
                if self._recover_from_corruption():
                    logger.info("Successfully recovered configuration")
                else:
                    logger.warning("Recovery failed, using defaults")
                    self._data = self._get_defaults()
                    self._data["_schema_version"] = self.schema.version
                    self._save()

    def _save(self):
        """Save configuration atomically"""
        with self._lock:
            try:
                # Create backup before saving
                self._create_backup()

                # Encrypt sensitive fields
                save_data = self._encrypt_sensitive_fields(self._data.copy())

                # Add integrity checksum
                save_data["_checksum"] = self._calculate_checksum(save_data)

                # Save to storage
                self._storage.save(self._config_path, save_data)

                logger.debug("Configuration saved successfully")

            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")
                raise ConfigError(f"Save failed: {e}") from e

    def _encrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt fields marked as sensitive in schema"""
        if not self._credential_manager:
            return data

        result = data.copy()

        for field_name, field_spec in self.schema.fields.items():
            if field_spec.get("encrypted") and field_name in result and result[field_name]:
                result[field_name] = self._credential_manager.encrypt(result[field_name])

        return result

    def _decrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt fields marked as sensitive in schema"""
        if not self._credential_manager:
            return data

        result = data.copy()

        for field_name, field_spec in self.schema.fields.items():
            if field_spec.get("encrypted") and field_name in result and result[field_name]:
                result[field_name] = self._credential_manager.decrypt(result[field_name])

        return result

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for integrity verification"""
        # Remove existing checksum from calculation
        calc_data = {k: v for k, v in data.items() if k != "_checksum"}

        # Sort keys for consistent hashing
        sorted_data = json.dumps(calc_data, sort_keys=True)

        return hashlib.sha256(sorted_data.encode()).hexdigest()

    def _verify_integrity(self, data: Dict[str, Any]) -> bool:
        """Verify configuration integrity"""
        stored_checksum = data.get("_checksum")
        if not stored_checksum:
            # No checksum, might be old format
            return True

        calculated_checksum = self._calculate_checksum(data)
        return stored_checksum == calculated_checksum

    def _create_backup(self):
        """Create backup of current configuration"""
        if not self._storage.exists(self._config_path):
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"config_backup_{timestamp}{self._config_path.suffix}"
        backup_path = self._backup_dir / backup_name

        try:
            shutil.copy2(self._config_path, backup_path)

            # Keep only recent backups (last 10)
            self._cleanup_old_backups(keep=10)

        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    def _cleanup_old_backups(self, keep: int = 10):
        """Remove old backup files"""
        backups = sorted(self._backup_dir.glob("config_backup_*"), key=lambda p: p.stat().st_mtime)

        if len(backups) > keep:
            for backup in backups[:-keep]:
                try:
                    backup.unlink()
                except Exception:
                    pass

    def _recover_from_corruption(self) -> bool:
        """Attempt to recover from corruption"""
        # Try loading from most recent backup
        backups = sorted(
            self._backup_dir.glob("config_backup_*"), key=lambda p: p.stat().st_mtime, reverse=True
        )

        for backup in backups[:3]:  # Try last 3 backups
            try:
                logger.info(f"Attempting recovery from backup: {backup.name}")

                # Create temporary adapter for the backup
                temp_adapter = self._create_storage_adapter()
                backup_data = temp_adapter.load(backup)

                if self._verify_integrity(backup_data):
                    self._data = self._decrypt_sensitive_fields(backup_data)

                    # Restore the main config file
                    shutil.copy2(backup, self._config_path)

                    return True

            except Exception as e:
                logger.warning(f"Recovery from {backup.name} failed: {e}")

        return False

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values"""
        defaults = {
            # Window
            "window_opacity": 0.95,
            "theme": "dark",
            "start_minimized": False,
            # Translation
            "auto_detect_language": True,
            "save_history": True,
            "history_limit": 100,
            # Editor
            "font_size": 11,
            "show_line_numbers": True,
            "word_wrap": False,
            # API
            "preferred_provider": "auto",
            "translation_timeout": 30,
            # Credentials
            "openai_api_key": "",
            "anthropic_api_key": "",
            "google_api_key": "",
            # Behavior
            "copy_on_translate": False,
            "clear_output_on_input_change": True,
            # Advanced
            "cache_translations": True,
            "max_cache_size": 100,
            "log_level": "INFO",
        }

        return defaults

    def _migrate(self, from_version: str, to_version: str):
        """Migrate configuration between schema versions"""
        logger.info(f"Migrating configuration from {from_version} to {to_version}")

        # Look for migration path
        migration = self.schema.migrations.get(f"{from_version}->{to_version}")

        if migration:
            try:
                # Create backup before migration
                self._create_backup()

                # Apply migration
                self._data = migration.migrate_func(self._data)
                self._data["_schema_version"] = to_version

                # Save migrated data
                self._save()

                logger.info("Migration completed successfully")

            except Exception as e:
                logger.error(f"Migration failed: {e}")

                # Attempt rollback if available
                if migration.rollback_func:
                    try:
                        self._data = migration.rollback_func(self._data)
                        logger.info("Rollback completed")
                    except Exception as rollback_error:
                        logger.error(f"Rollback failed: {rollback_error}")

                raise ConfigError(f"Migration failed: {e}") from e
        else:
            logger.warning(f"No migration path from {from_version} to {to_version}")
            self._data["_schema_version"] = to_version

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value with validation"""
        with self._lock:
            # Validate against schema
            if key in self.schema.fields:
                temp_data = self._data.copy()
                temp_data[key] = value

                errors = self.schema.validate(temp_data)
                if errors:
                    raise SchemaValidationError(f"Validation failed: {'; '.join(errors)}")

            self._set_internal(key, value)
            self._save()

    def _set_internal(self, key: str, value: Any):
        """Internal set without save"""
        self._data[key] = value

    def _delete_internal(self, key: str):
        """Internal delete without save"""
        self._data.pop(key, None)

    def update(self, updates: Dict[str, Any]):
        """Update multiple values atomically"""
        with self._lock:
            # Validate all updates
            temp_data = self._data.copy()
            temp_data.update(updates)

            errors = self.schema.validate(temp_data)
            if errors:
                raise SchemaValidationError(f"Validation failed: {'; '.join(errors)}")

            # Apply updates
            self._data.update(updates)
            self._save()

    @contextmanager
    def transaction(self):
        """Create an atomic transaction context"""
        transaction = ConfigTransaction(self)

        try:
            yield transaction

            # Auto-commit if not explicitly handled
            if not transaction.committed and not transaction.rolled_back:
                transaction.commit()

        except Exception:
            # Auto-rollback on exception
            if not transaction.committed and not transaction.rolled_back:
                transaction.rollback()
            raise

    def export(self, path: Path, include_sensitive: bool = False):
        """Export configuration to file"""
        with self._lock:
            export_data = self._data.copy()

            # Remove internal fields
            export_data.pop("_checksum", None)
            export_data.pop("_schema_version", None)

            # Remove sensitive data if requested
            if not include_sensitive:
                for field_name, field_spec in self.schema.fields.items():
                    if field_spec.get("encrypted"):
                        export_data.pop(field_name, None)

            # Determine format from extension
            if path.suffix.lower() in [".yaml", ".yml"]:
                adapter = YamlStorageAdapter()
            else:
                adapter = JsonStorageAdapter()

            adapter.save(path, export_data)
            logger.info(f"Configuration exported to {path}")

    def import_config(self, path: Path, merge: bool = True):
        """Import configuration from file"""
        # Determine format from extension
        if path.suffix.lower() in [".yaml", ".yml"]:
            adapter = YamlStorageAdapter()
        else:
            adapter = JsonStorageAdapter()

        import_data = adapter.load(path)

        with self._lock:
            if merge:
                # Merge with existing data
                temp_data = self._data.copy()
                temp_data.update(import_data)

                # Validate merged data
                errors = self.schema.validate(temp_data)
                if errors:
                    raise SchemaValidationError(f"Import validation failed: {'; '.join(errors)}")

                self._data = temp_data
            else:
                # Replace entirely
                errors = self.schema.validate(import_data)
                if errors:
                    raise SchemaValidationError(f"Import validation failed: {'; '.join(errors)}")

                self._data = import_data
                self._data["_schema_version"] = self.schema.version

            self._save()
            logger.info(f"Configuration imported from {path}")

    def reset(self):
        """Reset configuration to defaults"""
        with self._lock:
            self._data = self._get_defaults()
            self._data["_schema_version"] = self.schema.version
            self._save()
            logger.info("Configuration reset to defaults")

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate current configuration"""
        with self._lock:
            errors = self.schema.validate(self._data)
            return len(errors) == 0, errors

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values (excluding internal fields)"""
        with self._lock:
            return {k: v for k, v in self._data.items() if not k.startswith("_")}
