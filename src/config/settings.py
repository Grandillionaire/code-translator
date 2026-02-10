"""
Settings management for Code Translator
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
import base64
import yaml

from utils.logger import get_logger


class Settings:
    """Manage application settings with encryption for sensitive data"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.settings_dir = self._get_settings_dir()
        self.settings_file = self.settings_dir / "settings.json"
        self.key_file = self.settings_dir / ".key"

        # Ensure settings directory exists
        self.settings_dir.mkdir(parents=True, exist_ok=True)

        # Initialize encryption
        self.cipher = self._init_encryption()

        # Load settings
        self.settings = self._load_settings()

        # Apply defaults
        self._apply_defaults()

    def _get_settings_dir(self) -> Path:
        """Get the settings directory path"""
        if os.name == "nt":  # Windows
            base_path = Path(os.environ.get("APPDATA", ""))
        else:  # macOS/Linux
            base_path = Path.home() / ".config"

        return base_path / "CodeTranslator"

    def _init_encryption(self) -> Fernet:
        """Initialize encryption for sensitive data"""
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            # Secure the key file
            if os.name != "nt":
                os.chmod(self.key_file, 0o600)

        return Fernet(key)

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file with bulletproof error handling"""
        if not self.settings_file.exists():
            self.logger.info("Settings file not found, using defaults")
            return {}

        try:
            # Read file content
            with open(self.settings_file, "r", encoding="utf-8") as f:
                content = f.read().strip()

            # Handle empty file
            if not content:
                self.logger.warning("Settings file is empty, using defaults")
                return {}

            # Try to parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as json_error:
                self.logger.error(f"Invalid JSON in settings file: {json_error}")

                # Attempt to backup corrupt file
                backup_path = self.settings_file.with_suffix(".json.corrupt")
                try:
                    import shutil

                    shutil.copy2(self.settings_file, backup_path)
                    self.logger.info(f"Backed up corrupt settings to: {backup_path}")
                except Exception:
                    pass

                # Return defaults
                return {}

            # Validate that data is a dictionary
            if not isinstance(data, dict):
                self.logger.error(f"Settings must be a JSON object, got {type(data).__name__}")
                return {}

            # Decrypt sensitive fields
            for key in ["openai_api_key", "anthropic_api_key", "google_api_key"]:
                if key in data and data[key]:
                    try:
                        data[key] = self._decrypt(data[key])
                    except Exception as decrypt_error:
                        self.logger.warning(f"Failed to decrypt {key}: {decrypt_error}")
                        # Clear the invalid encrypted value
                        data[key] = ""

            return data

        except PermissionError:
            self.logger.error(f"Permission denied reading settings file: {self.settings_file}")
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error loading settings: {type(e).__name__}: {e}")
            return {}

    def _save_settings(self):
        """Save settings to file with bulletproof error handling"""
        try:
            # Create a copy for saving
            save_data = self.settings.copy()

            # Encrypt sensitive fields
            for key in ["openai_api_key", "anthropic_api_key", "google_api_key"]:
                if key in save_data and save_data[key]:
                    try:
                        save_data[key] = self._encrypt(save_data[key])
                    except Exception as e:
                        self.logger.warning(f"Failed to encrypt {key}, saving empty: {e}")
                        save_data[key] = ""

            # Validate data before saving
            try:
                json_str = json.dumps(save_data, indent=2, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                self.logger.error(f"Settings contain non-serializable data: {e}")
                # Try to clean the data
                save_data = self._clean_for_json(save_data)
                json_str = json.dumps(save_data, indent=2, ensure_ascii=False)

            # Create a temporary file first
            temp_file = self.settings_file.with_suffix(".tmp")
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(json_str)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data is written to disk

                # Atomically replace the original file
                import shutil

                shutil.move(str(temp_file), str(self.settings_file))

                # Secure the settings file
                if os.name != "nt":
                    os.chmod(self.settings_file, 0o600)

                self.logger.debug("Settings saved successfully")

            except Exception as e:
                # Clean up temp file if it exists
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except Exception:
                        pass
                raise

        except PermissionError:
            self.logger.error(f"Permission denied writing settings file: {self.settings_file}")
        except Exception as e:
            self.logger.error(f"Failed to save settings: {type(e).__name__}: {e}")

    def _clean_for_json(self, obj):
        """Clean object for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_for_json(v) for v in obj]
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            # Convert to string for any other type
            return str(obj)

    def _encrypt(self, value: str) -> str:
        """Encrypt a string value"""
        encrypted = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()

    def _decrypt(self, value: str) -> str:
        """Decrypt a string value"""
        encrypted = base64.b64decode(value.encode())
        return self.cipher.decrypt(encrypted).decode()

    def _apply_defaults(self):
        """Apply default settings"""
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
            # Behavior
            "copy_on_translate": False,
            "clear_output_on_input_change": True,
            # Advanced
            "cache_translations": True,
            "max_cache_size": 100,
            "log_level": "INFO",
        }

        for key, value in defaults.items():
            if key not in self.settings:
                self.settings[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value

    def save(self):
        """Save settings to disk"""
        self._save_settings()

    def reset(self):
        """Reset settings to defaults"""
        self.settings.clear()
        self._apply_defaults()
        self._save_settings()

    def export_settings(self, file_path: str, include_sensitive: bool = False):
        """Export settings to a file"""
        export_data = self.settings.copy()

        # Remove sensitive data if requested
        if not include_sensitive:
            for key in ["openai_api_key", "anthropic_api_key", "google_api_key"]:
                export_data.pop(key, None)

        # Determine format from extension
        ext = Path(file_path).suffix.lower()

        try:
            if ext == ".yaml" or ext == ".yml":
                with open(file_path, "w") as f:
                    yaml.dump(export_data, f, default_flow_style=False)
            else:
                with open(file_path, "w") as f:
                    json.dump(export_data, f, indent=2)

            self.logger.info(f"Settings exported to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            raise

    def import_settings(self, file_path: str, merge: bool = True):
        """Import settings from a file"""
        ext = Path(file_path).suffix.lower()

        try:
            if ext == ".yaml" or ext == ".yml":
                with open(file_path, "r") as f:
                    import_data = yaml.safe_load(f)
            else:
                with open(file_path, "r") as f:
                    import_data = json.load(f)

            if merge:
                self.settings.update(import_data)
            else:
                self.settings = import_data
                self._apply_defaults()

            self._save_settings()
            self.logger.info(f"Settings imported from {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            raise
