"""
FastMCPWrapper for nucleus: register tools, resources, prompts, run MCP server, mount other wrappers, and call tools/resources/prompts as a client.
If you want to connect your skills or pipelines to the MCP world, this is your adapter.
"""

import asyncio
from typing import Callable, Dict, List, Any

class FastMCPWrapper:
    """
    Wrapper for FastMCP. Lets you register tools/resources/prompts and run a FastMCP server or client.
    """
    def __init__(self, name="NucleusMCP", dependencies=None):
        try:
            from fastmcp import FastMCP, Client
            self.FastMCP = FastMCP
            self.Client = Client
        except ImportError:
            raise ImportError("FastMCP is not installed. Please install it with 'pip install fastmcp'")
        self.name = name
        self.dependencies = dependencies or []
        self.mcp = self.FastMCP(name, dependencies=self.dependencies)
        self.tools = {}
        self.resources = {}
        self.prompts = {}

    def add_tool(self, func: Callable, **kwargs):
        decorated = self.mcp.tool(**kwargs)(func)
        self.tools[func.__name__] = decorated
        return decorated

    def add_resource(self, uri: str, func: Callable, **kwargs):
        decorated = self.mcp.resource(uri, **kwargs)(func)
        self.resources[uri] = decorated
        return decorated

    def add_prompt(self, func: Callable, **kwargs):
        decorated = self.mcp.prompt(**kwargs)(func)
        self.prompts[func.__name__] = decorated
        return decorated

    def run(self, transport=None, **kwargs):
        self.mcp.run(transport=transport, **kwargs)

    async def call_tool(self, tool_name: str, params: Dict[str, Any], transport=None, **kwargs):
        async with self.Client(self.mcp, transport=transport, **kwargs) as client:
            return await client.call_tool(tool_name, params)

    async def read_resource(self, uri: str, transport=None, **kwargs):
        async with self.Client(self.mcp, transport=transport, **kwargs) as client:
            return await client.read_resource(uri)

    async def get_prompt(self, prompt_name: str, params: Dict[str, Any] = None, transport=None, **kwargs):
        async with self.Client(self.mcp, transport=transport, **kwargs) as client:
            return await client.get_prompt(prompt_name, params or {})

    def mount(self, prefix: str, other_wrapper):
        self.mcp.mount(prefix, other_wrapper.mcp)
        return self