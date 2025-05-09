"""
nucleus.llm_api.py: Unified LLM API for multiple providers (OpenAI, Anthropic, Gemini, Ollama, llama.cpp, etc.)
No vendor lock, clean naming, flexible endpoints, async/sync, easy to test.
"""

import os
import aiohttp
import httpx
import logging

from abc import ABC, abstractmethod

class LLMClient(ABC):
    """Abstract LLM client interface for all providers."""
    @abstractmethod
    async def generate(self, prompt: str, **kwargs):
        ...

class OpenAIClient(LLMClient):
    """OpenAI LLM client (supports custom endpoint)."""
    def __init__(self, api_key: str, api_url: str = "https://api.openai.com/v1/chat/completions", model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    async def generate(self, prompt: str, **kwargs):
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        payload.update(kwargs)
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=payload, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

class AnthropicClient(LLMClient):
    """Anthropic Claude API client."""
    def __init__(self, api_key: str, api_url: str = "https://api.anthropic.com/v1/messages", model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    async def generate(self, prompt: str, **kwargs):
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        payload.update(kwargs)
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=payload, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["content"][0]["text"]

class GeminiClient(LLMClient):
    """Google Gemini API client."""
    def __init__(self, api_key: str, api_url: str = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"):
        self.api_key = api_key
        self.api_url = api_url

    async def generate(self, prompt: str, **kwargs):
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        payload.update(kwargs)
        url = f"{self.api_url}?key={self.api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

class OllamaClient(LLMClient):
    """Ollama local API client."""
    def __init__(self, model: str = "llama3", api_url: str = "http://localhost:11434/api/chat"):
        self.model = model
        self.api_url = api_url

    async def generate(self, prompt: str, **kwargs):
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        payload.update(kwargs)
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=payload, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                # Ollama: either "message" or "choices" format
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]
                elif "choices" in data:
                    return data["choices"][0]["message"]["content"]
                return data

class LlamaCppClient(LLMClient):
    """llama.cpp server API client."""
    def __init__(self, api_url: str = "http://localhost:8080/completion"):
        self.api_url = api_url

    async def generate(self, prompt: str, **kwargs):
        payload = {
            "prompt": prompt,
            "stream": False,
            "n_predict": 512,
        }
        payload.update(kwargs)
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=payload, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("content") or data.get("text") or data

# Factory function for getting client by provider
def get_llm_client(provider: str, **kwargs) -> LLMClient:
    provider = provider.lower()
    if provider == "openai":
        return OpenAIClient(**kwargs)
    if provider == "anthropic":
        return AnthropicClient(**kwargs)
    if provider == "gemini":
        return GeminiClient(**kwargs)
    if provider == "ollama":
        return OllamaClient(**kwargs)
    if provider in ("llamacpp", "llama.cpp"):
        return LlamaCppClient(**kwargs)
    raise ValueError(f"Unknown LLM provider: {provider}")