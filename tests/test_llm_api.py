import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import nucleus.llm_api as llm
import asyncio

class DummyResponse:
    def __init__(self, content): self.content = content

@pytest.mark.asyncio
async def test_openai_client(monkeypatch):
    class DummySession:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        def post(self, *a, **k):
            class Resp:
                async def json(self): return {"choices":[{"message":{"content":"test response"}}]}
                async def __aenter__(self): return self
                async def __aexit__(self, *a): pass
                def raise_for_status(self): pass
            return Resp()
    monkeypatch.setattr(llm.aiohttp, "ClientSession", lambda: DummySession())
    client = llm.OpenAIClient(api_key="sk-test")
    resp = await client.generate("hi")
    assert resp == "test response"

@pytest.mark.asyncio
async def test_anthropic_client(monkeypatch):
    class DummySession:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        def post(self, *a, **k):
            class Resp:
                async def json(self): return {"content":[{"text":"anthropic reply"}]}
                async def __aenter__(self): return self
                async def __aexit__(self, *a): pass
                def raise_for_status(self): pass
            return Resp()
    monkeypatch.setattr(llm.aiohttp, "ClientSession", lambda: DummySession())
    client = llm.AnthropicClient(api_key="sk-test")
    resp = await client.generate("hi")
    assert resp == "anthropic reply"

@pytest.mark.asyncio
async def test_gemini_client(monkeypatch):
    class DummySession:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        def post(self, *a, **k):
            class Resp:
                async def json(self): return {"candidates":[{"content":{"parts":[{"text":"gemini answer"}]}}]}
                async def __aenter__(self): return self
                async def __aexit__(self, *a): pass
                def raise_for_status(self): pass
            return Resp()
    monkeypatch.setattr(llm.aiohttp, "ClientSession", lambda: DummySession())
    client = llm.GeminiClient(api_key="test")
    resp = await client.generate("hi")
    assert resp == "gemini answer"

@pytest.mark.asyncio
async def test_ollama_client(monkeypatch):
    class DummySession:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        def post(self, *a, **k):
            class Resp:
                async def json(self): return {"message":{"content":"ollama reply"}}
                async def __aenter__(self): return self
                async def __aexit__(self, *a): pass
                def raise_for_status(self): pass
            return Resp()
    monkeypatch.setattr(llm.aiohttp, "ClientSession", lambda: DummySession())
    client = llm.OllamaClient()
    resp = await client.generate("hi")
    assert resp == "ollama reply"

@pytest.mark.asyncio
async def test_llamacpp_client(monkeypatch):
    class DummySession:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        def post(self, *a, **k):
            class Resp:
                async def json(self): return {"content":"llamacpp reply"}
                async def __aenter__(self): return self
                async def __aexit__(self, *a): pass
                def raise_for_status(self): pass
            return Resp()
    monkeypatch.setattr(llm.aiohttp, "ClientSession", lambda: DummySession())
    client = llm.LlamaCppClient()
    resp = await client.generate("hi")
    assert resp == "llamacpp reply"

def test_factory():
    assert isinstance(llm.get_llm_client("openai", api_key="sk"), llm.OpenAIClient)
    assert isinstance(llm.get_llm_client("anthropic", api_key="sk"), llm.AnthropicClient)
    assert isinstance(llm.get_llm_client("gemini", api_key="a"), llm.GeminiClient)
    assert isinstance(llm.get_llm_client("ollama"), llm.OllamaClient)
    assert isinstance(llm.get_llm_client("llamacpp"), llm.LlamaCppClient)
    with pytest.raises(ValueError):
        llm.get_llm_client("notreal")