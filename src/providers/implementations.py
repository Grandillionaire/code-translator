"""
Provider Implementations
Concrete implementations of API providers with version compatibility
"""

import asyncio
import aiohttp
import importlib.metadata
from typing import Dict, Any, Tuple, Optional
import logging

from .provider_framework import (
    BaseProvider, ProviderStatus, ProviderCapabilities, 
    VersionCompatibilityAdapter, RequestPriority
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI API provider with version compatibility"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.client = None
        self.version = None
        self.adapter = None
    
    async def initialize(self):
        """Initialize OpenAI client with version detection"""
        try:
            import openai
            
            # Detect version
            try:
                self.version = importlib.metadata.version('openai')
            except:
                self.version = "0.x"  # Fallback for old versions
            
            # Initialize version adapter
            self.adapter = VersionCompatibilityAdapter("openai", self.version)
            
            # Initialize client based on version
            if self.version.startswith("1.") or hasattr(openai, 'OpenAI'):
                # New API (v1.x)
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info(f"Initialized OpenAI provider with v1.x API (version: {self.version})")
            else:
                # Old API (v0.x)
                openai.api_key = self.api_key
                self.client = openai
                logger.info(f"Initialized OpenAI provider with v0.x API (version: {self.version})")
            
            # Test connection
            await self.health_check()
            
        except ImportError:
            raise Exception("OpenAI package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            raise
    
    async def translate_code(
        self,
        code: str,
        source_lang: str,
        target_lang: str,
        model: str = "gpt-4",
        temperature: float = 0.2,
        max_tokens: int = 2000,
        **kwargs
    ) -> Tuple[str, float]:
        """Translate code using OpenAI"""
        
        prompt = f"""You are an expert code translator. Translate the following {source_lang} code to {target_lang}.

Requirements:
- Maintain the exact functionality and logic
- Use idiomatic {target_lang} patterns and conventions
- Handle language-specific features appropriately
- Include necessary imports/headers
- Preserve comments but translate them
- Output only the translated code without explanations

{source_lang} code:
{code}
"""
        
        messages = [
            {"role": "system", "content": "You are an expert programmer skilled in code translation."},
            {"role": "user", "content": prompt}
        ]
        
        # Execute with resilience
        async def make_request():
            if self.version.startswith("1.") or hasattr(self.client, 'chat'):
                # New API
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                content = response.choices[0].message.content
                confidence = 0.95 if model == "gpt-4" else 0.90
                
            else:
                # Old API
                response = await asyncio.to_thread(
                    self.client.ChatCompletion.create,
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                content = response.choices[0].message.content
                confidence = 0.95 if model == "gpt-4" else 0.90
            
            return content.strip(), confidence
        
        return await self.execute_with_resilience(
            make_request,
            priority=kwargs.get('priority', RequestPriority.NORMAL)
        )
    
    async def health_check(self) -> ProviderStatus:
        """Check OpenAI API health"""
        try:
            # Simple test request
            if self.version.startswith("1.") or hasattr(self.client, 'models'):
                await asyncio.to_thread(self.client.models.list)
            else:
                await asyncio.to_thread(self.client.Model.list)
            
            return ProviderStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return ProviderStatus.UNHEALTHY
    
    def get_capabilities(self) -> ProviderCapabilities:
        """Get OpenAI provider capabilities"""
        return ProviderCapabilities(
            supported_models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            max_tokens=8192,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=True,
            rate_limits={"requests_per_minute": 60, "tokens_per_minute": 90000},
            version_info={"api_version": self.version}
        )


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.client = None
    
    async def initialize(self):
        """Initialize Anthropic client"""
        try:
            import anthropic
            
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("Initialized Anthropic provider")
            
            # Test connection
            await self.health_check()
            
        except ImportError:
            raise Exception("Anthropic package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
            raise
    
    async def translate_code(
        self,
        code: str,
        source_lang: str,
        target_lang: str,
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.2,
        max_tokens: int = 2000,
        **kwargs
    ) -> Tuple[str, float]:
        """Translate code using Anthropic Claude"""
        
        prompt = f"""Translate this {source_lang} code to {target_lang}.

Requirements:
- Maintain the exact logic and functionality
- Use {target_lang} idioms and best practices
- Handle paradigm differences appropriately
- Include necessary imports/headers
- Preserve comments but translate them
- Output only the translated code, no explanations

{source_lang} code:
{code}
"""
        
        async def make_request():
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            confidence = 0.97  # High confidence for Claude
            
            return content, confidence
        
        return await self.execute_with_resilience(
            make_request,
            priority=kwargs.get('priority', RequestPriority.NORMAL)
        )
    
    async def health_check(self) -> ProviderStatus:
        """Check Anthropic API health"""
        try:
            # Simple test request
            await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            
            return ProviderStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"Anthropic health check failed: {e}")
            return ProviderStatus.UNHEALTHY
    
    def get_capabilities(self) -> ProviderCapabilities:
        """Get Anthropic provider capabilities"""
        return ProviderCapabilities(
            supported_models=[
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ],
            max_tokens=100000,
            supports_streaming=True,
            supports_functions=False,
            supports_vision=True,
            rate_limits={"requests_per_minute": 50},
            version_info={"provider": "anthropic"}
        )


class GoogleProvider(BaseProvider):
    """Google Gemini API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.client = None
    
    async def initialize(self):
        """Initialize Google Generative AI client"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            self.client = genai
            logger.info("Initialized Google provider")
            
            # Test connection
            await self.health_check()
            
        except ImportError:
            raise Exception("Google Generative AI package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Google provider: {e}")
            raise
    
    async def translate_code(
        self,
        code: str,
        source_lang: str,
        target_lang: str,
        model_name: str = "gemini-pro",
        temperature: float = 0.2,
        max_tokens: int = 2000,
        **kwargs
    ) -> Tuple[str, float]:
        """Translate code using Google Gemini"""
        
        model = self.client.GenerativeModel(model_name)
        
        prompt = f"""You are an expert code translator. Translate this {source_lang} code to {target_lang}.

Instructions:
- Preserve the exact functionality
- Use appropriate {target_lang} conventions
- Handle language-specific features properly
- Output only code, no explanations

{source_lang} code:
{code}
"""
        
        async def make_request():
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
            
            content = response.text.strip()
            confidence = 0.93  # Good confidence for Gemini
            
            return content, confidence
        
        return await self.execute_with_resilience(
            make_request,
            priority=kwargs.get('priority', RequestPriority.NORMAL)
        )
    
    async def health_check(self) -> ProviderStatus:
        """Check Google API health"""
        try:
            # Simple test request
            model = self.client.GenerativeModel('gemini-pro')
            await asyncio.to_thread(
                model.generate_content,
                "test",
                generation_config={"max_output_tokens": 10}
            )
            
            return ProviderStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"Google health check failed: {e}")
            return ProviderStatus.UNHEALTHY
    
    def get_capabilities(self) -> ProviderCapabilities:
        """Get Google provider capabilities"""
        return ProviderCapabilities(
            supported_models=["gemini-pro", "gemini-pro-vision"],
            max_tokens=32768,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=True,
            rate_limits={"requests_per_minute": 60},
            version_info={"provider": "google"}
        )


class OfflineProvider(BaseProvider):
    """Offline translation provider using rule-based translation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.translator = None
    
    async def initialize(self):
        """Initialize offline translator"""
        try:
            from translator.offline_translator import OfflineTranslator
            self.translator = OfflineTranslator()
            logger.info("Initialized offline provider")
            
        except Exception as e:
            logger.error(f"Failed to initialize offline provider: {e}")
            raise
    
    async def translate_code(
        self,
        code: str,
        source_lang: str,
        target_lang: str,
        **kwargs
    ) -> Tuple[str, float]:
        """Translate code using offline rules"""
        
        try:
            # Run in thread to avoid blocking
            translated = await asyncio.to_thread(
                self.translator.translate,
                code,
                source_lang,
                target_lang
            )
            
            confidence = 0.7  # Lower confidence for offline
            return translated, confidence
            
        except Exception as e:
            logger.error(f"Offline translation failed: {e}")
            raise
    
    async def health_check(self) -> ProviderStatus:
        """Check offline translator health"""
        # Always healthy as it's local
        return ProviderStatus.HEALTHY
    
    def get_capabilities(self) -> ProviderCapabilities:
        """Get offline provider capabilities"""
        return ProviderCapabilities(
            supported_models=["rule-based"],
            max_tokens=100000,  # No real limit
            supports_streaming=False,
            supports_functions=False,
            supports_vision=False,
            rate_limits={},  # No rate limits
            version_info={"type": "offline"}
        )


class MockProvider(BaseProvider):
    """Mock provider for testing"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.fail_rate = config.get('fail_rate', 0.0)
        self.latency = config.get('latency', 0.1)
    
    async def initialize(self):
        """Initialize mock provider"""
        logger.info("Initialized mock provider")
    
    async def translate_code(
        self,
        code: str,
        source_lang: str,
        target_lang: str,
        **kwargs
    ) -> Tuple[str, float]:
        """Mock translation"""
        import random
        
        # Simulate latency
        await asyncio.sleep(self.latency)
        
        # Simulate failures
        if random.random() < self.fail_rate:
            raise Exception("Mock provider failure")
        
        # Simple mock translation
        translated = f"// Translated from {source_lang} to {target_lang}\n{code}"
        confidence = 0.5
        
        return translated, confidence
    
    async def health_check(self) -> ProviderStatus:
        """Mock health check"""
        import random
        
        if random.random() < self.fail_rate:
            return ProviderStatus.UNHEALTHY
        
        return ProviderStatus.HEALTHY
    
    def get_capabilities(self) -> ProviderCapabilities:
        """Get mock provider capabilities"""
        return ProviderCapabilities(
            supported_models=["mock"],
            max_tokens=10000,
            supports_streaming=False,
            supports_functions=False,
            supports_vision=False,
            rate_limits={"requests_per_minute": 100},
            version_info={"type": "mock"}
        )