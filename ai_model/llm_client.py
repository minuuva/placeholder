"""
LLM Client - Abstract interface for multiple LLM providers.

Supports Anthropic Claude, OpenAI, and local Ollama with automatic fallback.
"""

import json
import os
from typing import Optional, Any
from abc import ABC, abstractmethod

from .config import Config


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        """Generate completion from LLM."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        self.client = None
        
        if self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                print("Warning: anthropic package not installed. Run: pip install anthropic")
    
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        """Generate completion using Claude."""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")
    
    def is_available(self) -> bool:
        """Check if Anthropic is configured."""
        return bool(self.client)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("Warning: openai package not installed. Run: pip install openai")
    
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        """Generate completion using GPT."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self.client)


class OllamaProvider(BaseLLMProvider):
    """Local Ollama provider (free, requires local installation)."""
    
    def __init__(self, model: str = "llama3"):
        self.model = model
        self.base_url = "http://localhost:11434"
    
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        """Generate completion using Ollama."""
        try:
            import requests
            
            payload = {
                "model": self.model,
                "prompt": f"{system_prompt}\n\nUser Query: {user_prompt}",
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise RuntimeError(f"Ollama error: {response.status_code}")
        
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")
    
    def is_available(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False


class LLMClient:
    """
    Claude-only LLM client for natural language processing.
    
    Uses Anthropic's Claude API for query parsing and summarization.
    """
    
    def __init__(self, preferred_provider: Optional[str] = None):
        """
        Initialize LLM client with Claude.
        
        Args:
            preferred_provider: Ignored (always uses "anthropic")
        """
        self.provider = AnthropicProvider()
        self.active_provider: Optional[BaseLLMProvider] = None
        
        self._select_provider()
    
    def _select_provider(self):
        """Select Claude provider."""
        if self.provider.is_available():
            self.active_provider = self.provider
            print("Using LLM provider: Claude (Anthropic)")
        else:
            raise RuntimeError(
                "Claude API not available. Please:\n"
                "  1. Get API key from https://console.anthropic.com/\n"
                "  2. Set ANTHROPIC_API_KEY in .env file\n"
                "  3. Run: pip install anthropic"
            )
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_retries: int = 3
    ) -> str:
        """
        Generate completion with automatic retry and fallback.
        
        Args:
            system_prompt: System instruction for the LLM
            user_prompt: User query/input
            temperature: Sampling temperature (0.0 = deterministic)
            max_retries: Number of retries before giving up
        
        Returns:
            Generated text completion
        
        Raises:
            RuntimeError: If all providers fail
        """
        if not self.active_provider:
            raise RuntimeError("No active LLM provider")
        
        for attempt in range(max_retries):
            try:
                return self.active_provider.generate(system_prompt, user_prompt, temperature)
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    continue
                else:
                    raise RuntimeError(f"All LLM generation attempts failed: {e}")
    
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0
    ) -> dict:
        """
        Generate JSON completion.
        
        Args:
            system_prompt: System instruction for the LLM
            user_prompt: User query/input
            temperature: Sampling temperature
        
        Returns:
            Parsed JSON dict
        
        Raises:
            RuntimeError: If generation fails or JSON is invalid
        """
        response = self.generate(system_prompt, user_prompt, temperature)
        
        try:
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            return json.loads(response_clean.strip())
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON from LLM response: {e}\nResponse: {response}")
    
    def get_provider_name(self) -> str:
        """Get name of active provider."""
        return "claude" if self.active_provider else "none"
