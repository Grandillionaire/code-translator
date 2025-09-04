"""
API Compatibility Layer for handling different OpenAI library versions
Provides a unified interface that works with both old and new OpenAI syntax
"""

import sys
import importlib.metadata
from typing import Optional, Dict, List, Any, Union
import logging

logger = logging.getLogger(__name__)


class OpenAICompatibilityWrapper:
    """
    Wrapper class to handle OpenAI API version differences.
    Supports both old (< 1.0) and new (>= 1.0) API syntax.
    """
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.client = None
        self.version = None
        self.is_new_version = False
        self.initialization_error = None
        
        try:
            import openai
            self.openai = openai
            
            # Detect OpenAI version
            try:
                self.version = importlib.metadata.version('openai')
                major_version = int(self.version.split('.')[0])
                self.is_new_version = major_version >= 1
            except:
                # Fallback for older Python versions
                self.is_new_version = hasattr(openai, 'OpenAI')
            
            # Initialize based on version
            if self.is_new_version:
                # New API (>= 1.0.0)
                # Check httpx version compatibility
                try:
                    import httpx
                    httpx_version = getattr(httpx, '__version__', '0.0.0')
                    httpx_major = int(httpx_version.split('.')[0])
                    httpx_minor = int(httpx_version.split('.')[1])
                    
                    # OpenAI 1.0.0 has issues with httpx < 0.23
                    if httpx_major == 0 and httpx_minor >= 23:
                        # Apply workaround for httpx proxy parameter issue
                        import inspect
                        
                        # Check if httpx.Client accepts proxies parameter
                        client_init_params = inspect.signature(httpx.Client.__init__).parameters
                        
                        # Patch httpx.Client to handle the proxies parameter
                        original_httpx_client = httpx.Client
                        
                        class PatchedHTTPXClient(original_httpx_client):
                            def __init__(self, **kwargs):
                                # Remove proxies if not supported
                                if 'proxies' in kwargs and 'proxies' not in client_init_params:
                                    kwargs.pop('proxies')
                                super().__init__(**kwargs)
                        
                        # Temporarily replace httpx.Client
                        httpx.Client = PatchedHTTPXClient
                        
                        try:
                            self.client = openai.OpenAI(api_key=api_key)
                            logger.info(f"Initialized OpenAI with patched httpx workaround")
                        finally:
                            # Restore original
                            httpx.Client = original_httpx_client
                    else:
                        # Direct initialization for compatible httpx versions
                        self.client = openai.OpenAI(api_key=api_key)
                        logger.info(f"Initialized OpenAI with new API (version {self.version})")
                        
                except ImportError:
                    # httpx not available, try direct initialization
                    try:
                        self.client = openai.OpenAI(api_key=api_key)
                        logger.info(f"Initialized OpenAI with new API (no httpx)")
                    except Exception as e:
                        logger.error(f"Failed to initialize OpenAI client: {e}")
                        raise
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
                    # Last resort: use a minimal mock that prevents crashes
                    logger.warning("Using fallback OpenAI client due to initialization errors")
                    
                    class FallbackOpenAIClient:
                        def __init__(self):
                            self.chat = type('obj', (object,), {
                                'completions': type('obj', (object,), {
                                    'create': lambda **kwargs: None
                                })()
                            })()
                    
                    self.client = FallbackOpenAIClient()
                    self.initialization_error = str(e)
            else:
                # Old API (< 1.0.0)
                openai.api_key = api_key
                # Handle old API parameters
                if 'organization' in kwargs:
                    openai.organization = kwargs['organization']
                if 'api_base' in kwargs or 'base_url' in kwargs:
                    openai.api_base = kwargs.get('api_base', kwargs.get('base_url'))
                    
                self.client = openai
                logger.info(f"Initialized OpenAI with old API (version {self.version})")
                
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    async def create_chat_completion(
        self,
        model: str = "gpt-4",
        messages: List[Dict[str, str]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion using the appropriate API version.
        
        Args:
            model: The model to use (e.g., 'gpt-4', 'gpt-3.5-turbo')
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters passed to the API
            
        Returns:
            Response dictionary with 'content' and 'usage' keys
        """
        
        if not messages:
            raise ValueError("Messages parameter is required")
        
        # Check if there was an initialization error
        if self.initialization_error:
            raise Exception(f"OpenAI client initialization failed: {self.initialization_error}")
        
        try:
            if self.is_new_version:
                # New API call pattern
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Extract content from new format
                content = response.choices[0].message.content
                usage = {
                    'total_tokens': response.usage.total_tokens if response.usage else None,
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else None,
                    'completion_tokens': response.usage.completion_tokens if response.usage else None
                }
                
            else:
                # Old API call pattern
                params = {
                    'model': model,
                    'messages': messages,
                    'temperature': temperature,
                    **kwargs
                }
                if max_tokens:
                    params['max_tokens'] = max_tokens
                    
                response = self.openai.ChatCompletion.create(**params)
                
                # Extract content from old format
                content = response.choices[0].message.content
                usage = response.get('usage', {})
            
            return {
                'content': content,
                'usage': usage,
                'model': model,
                'full_response': response
            }
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def create_chat_completion_sync(
        self,
        model: str = "gpt-4",
        messages: List[Dict[str, str]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synchronous version of create_chat_completion.
        """
        
        if not messages:
            raise ValueError("Messages parameter is required")
        
        # Check if there was an initialization error
        if self.initialization_error:
            raise Exception(f"OpenAI client initialization failed: {self.initialization_error}")
        
        try:
            if self.is_new_version:
                # New API call pattern
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Extract content from new format
                content = response.choices[0].message.content
                usage = {
                    'total_tokens': response.usage.total_tokens if response.usage else None,
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else None,
                    'completion_tokens': response.usage.completion_tokens if response.usage else None
                }
                
            else:
                # Old API call pattern
                params = {
                    'model': model,
                    'messages': messages,
                    'temperature': temperature,
                    **kwargs
                }
                if max_tokens:
                    params['max_tokens'] = max_tokens
                    
                response = self.openai.ChatCompletion.create(**params)
                
                # Extract content from old format
                content = response.choices[0].message.content
                usage = response.get('usage', {})
            
            return {
                'content': content,
                'usage': usage,
                'model': model,
                'full_response': response
            }
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise


def check_openai_compatibility() -> Dict[str, Any]:
    """
    Check OpenAI installation and version compatibility.
    
    Returns:
        Dictionary with installation status and version info
    """
    
    result = {
        'installed': False,
        'version': None,
        'is_new_version': False,
        'import_error': None
    }
    
    try:
        import openai
        result['installed'] = True
        
        try:
            version = importlib.metadata.version('openai')
            result['version'] = version
            major_version = int(version.split('.')[0])
            result['is_new_version'] = major_version >= 1
        except:
            # Fallback check
            result['is_new_version'] = hasattr(openai, 'OpenAI')
            result['version'] = 'unknown'
            
    except ImportError as e:
        result['import_error'] = str(e)
        
    return result


def create_safe_openai_client(api_key: str, **kwargs) -> OpenAICompatibilityWrapper:
    """
    Create a safe OpenAI client that filters out unsupported parameters.
    
    This is a convenience function that ensures compatibility across different
    OpenAI library versions and prevents errors from unsupported parameters.
    
    Args:
        api_key: OpenAI API key
        **kwargs: Additional parameters (will be ignored for safety)
        
    Returns:
        OpenAICompatibilityWrapper instance
    """
    # Log if any parameters were provided (they will be ignored)
    if kwargs:
        logger.info(f"Ignoring additional parameters for OpenAI client: {list(kwargs.keys())}")
    
    # Always create with minimal parameters to avoid issues
    return OpenAICompatibilityWrapper(api_key)