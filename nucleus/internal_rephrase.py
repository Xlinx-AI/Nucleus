"""
Async LLM-based prompt rephraser using PromptRouterSkill.
Author: 
"""

import asyncio
from agent.skills.prompt_router import Skill as PromptRouterSkill

def rephrase_prompt(prompt: str) -> str:
    """
    Async call to LLM router for prompt rephrasing.
    (For sync GUI interface — run_until_complete)
    """
    router = PromptRouterSkill()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(router.handle_async(prompt))