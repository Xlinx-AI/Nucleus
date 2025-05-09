"""
GroqMagic for nucleus: unified interface for Groq AI models (text, vision, moderation, audio, code).
Supports sync/async, streaming, CLI, and history. If you want to plug Groq into your nucleus skills, use this.
"""

import os
import logging

try:
    from groq import Groq
except ImportError:
    Groq = None

class GroqMagic:
    """
    Unified interface for Groq AI models: text, vision, moderation, audio, code.
    Handles API key, sync/async, streaming, and history.
    """
    def __init__(self, api_key=None, timeout=60):
        if not Groq:
            raise ImportError("Groq Python SDK not installed. pip install groq")
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set.")
        self.client = Groq(api_key=self.api_key, timeout=timeout)
        self.history = {}
        self.logger = logging.getLogger("GroqMagic")

    def chat(self, model, messages, temperature=0.7, max_tokens=1024, stream=False, conversation_id=None):
        # Minimal chat, no vision, just text
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
                stream=stream
            )
            if stream:
                text = ""
                for chunk in completion:
                    content = chunk.choices[0].delta.content or ""
                    text += content
                    print(content, end="", flush=True)
                print()
                return text
            else:
                return completion.choices[0].message.content
        except Exception as e:
            self.logger.error(f"GroqMagic chat error: {e}")
            return {"error": str(e)}

    async def chat_async(self, *args, **kwargs):
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.chat(*args, **kwargs))