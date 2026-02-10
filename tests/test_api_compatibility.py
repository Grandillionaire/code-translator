"""
Tests for OpenAI API compatibility layer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock the openai module for testing
sys.modules["openai"] = MagicMock()

from src.utils.api_compatibility import OpenAICompatibilityWrapper, check_openai_compatibility


class TestOpenAICompatibilityWrapper:
    """Test the OpenAI compatibility wrapper"""

    def test_new_api_detection(self):
        """Test detection of new OpenAI API (>= 1.0)"""
        with patch("importlib.metadata.version", return_value="1.5.0"):
            with patch("openai.OpenAI") as mock_client:
                wrapper = OpenAICompatibilityWrapper("test-key")
                assert wrapper.is_new_version is True
                assert wrapper.version == "1.5.0"
                mock_client.assert_called_once_with(api_key="test-key")

    def test_old_api_detection(self):
        """Test detection of old OpenAI API (< 1.0)"""
        with patch("importlib.metadata.version", return_value="0.27.8"):
            wrapper = OpenAICompatibilityWrapper("test-key")
            assert wrapper.is_new_version is False
            assert wrapper.version == "0.27.8"
            # In old API, api_key is set directly on the module
            assert wrapper.openai.api_key == "test-key"

    def test_fallback_detection_new_api(self):
        """Test fallback detection when version info unavailable (new API detected)"""
        with patch("importlib.metadata.version", side_effect=Exception):
            # When hasattr(openai, 'OpenAI') is True, it's new version
            mock_openai = MagicMock()
            mock_openai.OpenAI = MagicMock()
            with patch.dict(sys.modules, {"openai": mock_openai}):
                wrapper = OpenAICompatibilityWrapper("test-key")
                assert wrapper.is_new_version is True

    @pytest.mark.asyncio
    async def test_create_chat_completion_new_api(self):
        """Test chat completion with new API"""
        with patch("importlib.metadata.version", return_value="1.5.0"):
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Translated code"))]
            mock_response.usage = Mock(total_tokens=100, prompt_tokens=50, completion_tokens=50)
            mock_client.chat.completions.create.return_value = mock_response

            with patch("openai.OpenAI", return_value=mock_client):
                wrapper = OpenAICompatibilityWrapper("test-key")

                result = await wrapper.create_chat_completion(
                    model="gpt-4", messages=[{"role": "user", "content": "test"}], temperature=0.5
                )

                assert result["content"] == "Translated code"
                assert result["usage"]["total_tokens"] == 100
                assert result["model"] == "gpt-4"

    def test_create_chat_completion_sync_old_api(self):
        """Test synchronous chat completion with old API"""
        with patch("importlib.metadata.version", return_value="0.27.8"):
            # Create a mock response that matches old API format
            mock_choice = Mock()
            mock_choice.message = Mock()
            mock_choice.message.content = "Translated code"

            mock_response = Mock()
            mock_response.choices = [mock_choice]
            # The old API uses .get('usage', {}) so we need to mock the get method
            mock_response.get = Mock(
                return_value={"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50}
            )

            with patch("openai.ChatCompletion.create", return_value=mock_response):
                wrapper = OpenAICompatibilityWrapper("test-key")

                result = wrapper.create_chat_completion_sync(
                    model="gpt-3.5-turbo", messages=[{"role": "user", "content": "test"}]
                )

                assert result["content"] == "Translated code"
                assert result["usage"]["total_tokens"] == 100

    def test_error_handling(self):
        """Test error handling in API calls"""
        with patch("importlib.metadata.version", return_value="1.5.0"):
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")

            with patch("openai.OpenAI", return_value=mock_client):
                wrapper = OpenAICompatibilityWrapper("test-key")

                with pytest.raises(Exception, match="API Error"):
                    wrapper.create_chat_completion_sync(
                        messages=[{"role": "user", "content": "test"}]
                    )

    def test_missing_messages_parameter(self):
        """Test that missing messages parameter raises ValueError"""
        wrapper = OpenAICompatibilityWrapper("test-key")

        with pytest.raises(ValueError, match="Messages parameter is required"):
            wrapper.create_chat_completion_sync()


class TestCheckOpenAICompatibility:
    """Test the compatibility checker function"""

    def test_openai_installed_detection(self):
        """Test checking when OpenAI is installed"""
        # The actual version of openai is installed in this test environment
        result = check_openai_compatibility()

        assert result["installed"] is True
        assert result["version"] is not None
        assert result["import_error"] is None

    def test_version_detection(self):
        """Test that version detection works"""
        result = check_openai_compatibility()

        # Since we have openai installed, we should get version info
        assert result["installed"] is True
        # The version should be a string
        if result["version"]:
            assert isinstance(result["version"], str)

    def test_compatibility_info_structure(self):
        """Test that the compatibility info has expected structure"""
        result = check_openai_compatibility()

        assert "installed" in result
        assert "version" in result
        assert "is_new_version" in result
        assert "import_error" in result
