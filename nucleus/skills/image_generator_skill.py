from nucleus.skill_manager import Skill
import os
import logging
import asyncio
from typing import Optional, Dict, Any
import aiohttp
from PIL import Image
from io import BytesIO
import base64

class ImageGeneratorSkill(Skill):
    """
    This skill generates images using an AI/ML API.
    Supports async, sync, different output formats, and batch generation.
    If your API key is missing, you'll just get an error and a sad log line.
    """
    def __init__(self, api_key: Optional[str] = None, api_url: str = "https://api.aimlapi.com/v1/images/generations", event_bus=None):
        super().__init__(
            name="image_generator",
            description="Generates images from prompts using an external AI/ML API.",
            capability=None
        )
        self.event_bus = event_bus
        self.api_key = api_key or os.environ.get("AIML_API_KEY")
        self.api_url = api_url
        self.logger = logging.getLogger('ImageGeneratorSkill')
        if not self.api_key:
            self.logger.warning("API key not provided or found in env AIML_API_KEY.")

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Generate image",
                "desc": "Generates an image from a prompt.",
                "input_type": "prompt",
                "output_type": "image",
                "tags": ["image", "generate", "ai"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me a prompt and I'll try to generate an image (async).
        """
        prompt = step.get("prompt", "")
        model = step.get("model", "flux-pro/v1.1")
        size = step.get("size")
        num_images = step.get("num_images", 1)
        negative_prompt = step.get("negative_prompt")
        return_format = step.get("return_format", "json")

        payload = {
            "prompt": prompt,
            "model": model,
            "n": num_images
        }
        if size:
            payload["size"] = size
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        if not self.api_key:
            return {"error": "API key not set for image generation."}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
            if return_format == "json":
                return result
            elif return_format == "image":
                return await self._process_images_async(result)
            elif return_format == "b64":
                return self._extract_b64(result)
            elif return_format == "url":
                return self._extract_urls(result)
            else:
                return {"error": f"Invalid return_format: {return_format}"}
        except Exception as e:
            return {"error": str(e)}

    async def _process_images_async(self, result: Dict[str, Any]):
        images = []
        items = result.get("data", result.get("images", [result]))
        async with aiohttp.ClientSession() as session:
            for item in items:
                if "url" in item:
                    async with session.get(item["url"]) as resp:
                        resp.raise_for_status()
                        content = await resp.read()
                        img = Image.open(BytesIO(content))
                        images.append(img)
                elif "b64_json" in item:
                    img_data = base64.b64decode(item["b64_json"])
                    img = Image.open(BytesIO(img_data))
                    images.append(img)
        return images

    def _extract_b64(self, result: Dict[str, Any]):
        b64_strings = []
        items = result.get("data", result.get("images", [result]))
        for item in items:
            if "b64_json" in item:
                b64_strings.append(item["b64_json"])
        return b64_strings

    def _extract_urls(self, result: Dict[str, Any]):
        urls = []
        items = result.get("data", result.get("images", [result]))
        for item in items:
            if "url" in item:
                urls.append(item["url"])
        return urls