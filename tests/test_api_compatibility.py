"""
Tests for OpenAI API compatibility layer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock the openai module for testing
sys.modules['openai'] = MagicMock()

from src.utils.api_compatibility import OpenAICompatibilityWrapper, check_openai_compatibility


class TestOpenAICompatibilityWrapper:
    """Test the OpenAI compatibility wrapper"""
    
    def test_new_api_detection(self):
        """Test detection of new OpenAI API (>= 1.0)"""
        with patch('importlib.metadata.version', return_value='1.5.0'):
            with patch('openai.OpenAI') as mock_client:
                wrapper = OpenAICompatibilityWrapper("test-key")
                assert wrapper.is_new_version is True
                assert wrapper.version == '1.5.0'
                mock_client.assert_called_once_with(api_key="test-key")
    
    def test_old_api_detection(self):
        """Test detection of old OpenAI API (< 1.0)"""
        with patch('importlib.metadata.version', return_value='0.27.8'):
            with patch('openai.api_key') as mock_api_key:
                wrapper = OpenAICompatibilityWrapper("test-key")
                assert wrapper.is_new_version is False
                assert wrapper.version == '0.27.8'
                assert mock_api_key == "test-key"
    
    def test_fallback_detection(self):
        """Test fallback detection when version info unavailable"""
        with patch('importlib.metadata.version', side_effect=Exception):
            with patch('hasattr', return_value=True):
                wrapper = OpenAICompatibilityWrapper("test-key")
                assert wrapper.is_new_version is True
    
    @pytest.mark.asyncio
    async def test_create_chat_completion_new_api(self):
        """Test chat completion with new API"""
        with patch('importlib.metadata.version', return_value='1.5.0'):
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Translated code"))]
            mock_response.usage = Mock(
                total_tokens=100,
                prompt_tokens=50,
                completion_tokens=50
            )
            mock_client.chat.completions.create.return_value = mock_response
            
            with patch('openai.OpenAI', return_value=mock_client):
                wrapper = OpenAICompatibilityWrapper("test-key")
                
                result = await wrapper.create_chat_completion(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.5
                )
                
                assert result['content'] == "Translated code"
                assert result['usage']['total_tokens'] == 100
                assert result['model'] == "gpt-4"
    
    def test_create_chat_completion_sync_old_api(self):
        """Test synchronous chat completion with old API"""
        with patch('importlib.metadata.version', return_value='0.27.8'):
            mock_response = {
                'choices': [{'message': {'content': 'Translated code'}}],
                'usage': {'total_tokens': 100}
            }
            
            with patch('openai.ChatCompletion.create', return_value=Mock(**mock_response)):
                wrapper = OpenAICompatibilityWrapper("test-key")
                
                result = wrapper.create_chat_completion_sync(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}]
                )
                
                assert result['content'] == "Translated code"
                assert result['usage']['total_tokens'] == 100
    
    def test_error_handling(self):
        """Test error handling in API calls"""
        with patch('importlib.metadata.version', return_value='1.5.0'):
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            with patch('openai.OpenAI', return_value=mock_client):
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
    
    def test_openai_installed_new_version(self):
        """Test checking when new OpenAI version is installed"""
        with patch('importlib.import_module'):
            with patch('importlib.metadata.version', return_value='1.5.0'):
                result = check_openai_compatibility()
                
                assert result['installed'] is True
                assert result['version'] == '1.5.0'
                assert result['is_new_version'] is True
                assert result['import_error'] is None
    
    def test_openai_not_installed(self):
        """Test checking when OpenAI is not installed"""
        with patch('importlib.import_module', side_effect=ImportError("No module")):
            result = check_openai_compatibility()
            
            assert result['installed'] is False
            assert result['version'] is None
            assert result['is_new_version'] is False
            assert "No module" in result['import_error']
    
    def test_version_detection_fallback(self):
        """Test version detection with fallback"""
        with patch('importlib.import_module'):
            with patch('importlib.metadata.version', side_effect=Exception):
                with patch('hasattr', return_value=True):
                    result = check_openai_compatibility()
                    
                    assert result['installed'] is True
                    assert result['version'] == 'unknown'
                    assert result['is_new_version'] is True