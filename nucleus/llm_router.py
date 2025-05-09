import aiohttp
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

class AsyncLLMBackend(ABC):
    """
    Абстрактный асинхронный бэкенд для LLM: генерация текста и эмбеддингов.
    """

    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        pass

class AsyncOpenAIBackend(AsyncLLMBackend):
    """
    Асинхронный OpenAI-совместимый бэкенд (через API).
    """
    def __init__(self, api_url: str, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def complete(self, prompt: str, **kwargs) -> str:
        url = f"{self.api_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            **kwargs
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        url = f"{self.api_url}/v1/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": self.model,
            "input": texts,
            **kwargs
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return [e["embedding"] for e in data["data"]]

class AsyncOllamaBackend(AsyncLLMBackend):
    """
    Асинхронный Ollama backend.
    """
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def complete(self, prompt: str, **kwargs) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["message"]["content"]

    async def embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model,
            "input": texts,
            **kwargs
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return [e["embedding"] for e in data["data"]]

class AsyncPollinationsBackend(AsyncLLMBackend):
    """
    Асинхронный бэкенд для Pollinations LLM API.
    """
    def __init__(self, api_url: str, model: str):
        self.api_url = api_url.rstrip("/")
        self.model = model

    async def complete(self, prompt: str, **kwargs) -> str:
        url = f"{self.api_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            **kwargs
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        url = f"{self.api_url}/v1/embeddings"
        payload = {
            "model": self.model,
            "input": texts,
            **kwargs
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return [e["embedding"] for e in data["data"]]

class AsyncLLMRouter:
    """
    Маршрутизатор для асинхронных LLM-бэкендов: complete/embeddings.
    """
    def __init__(self):
        self.backends: Dict[str, AsyncLLMBackend] = {}
        self.default_backend: Optional[str] = None

    def register(self, name: str, backend: AsyncLLMBackend, default: bool = False):
        self.backends[name] = backend
        if default or not self.default_backend:
            self.default_backend = name

    async def complete(self, prompt: str, backend: Optional[str] = None, **kwargs) -> str:
        name = backend or self.default_backend
        if not name or name not in self.backends:
            raise ValueError("Нет доступного LLM-бэкенда.")
        return await self.backends[name].complete(prompt, **kwargs)

    async def embeddings(self, texts: List[str], backend: Optional[str] = None, **kwargs) -> List[List[float]]:
        name = backend or self.default_backend
        if not name or name not in self.backends:
            raise ValueError("Нет доступного LLM-бэкенда.")
        return await self.backends[name].embeddings(texts, **kwargs)