"""
Skill registry and utilities for dynamic loading and markdown description of skills.

"""

import os
import importlib.util
import importlib
import inspect
import textwrap

class ToolSpec:
    """
    Tool/skill metadata: name, docstring, signature, call-proxy, markdown description.
    """
    def __init__(self, name, cls, doc, signature, call):
        self.name = name
        self.cls = cls
        self.doc = doc
        self.signature = signature
        self.call = call

    def markdown(self):
        doc = textwrap.dedent(self.doc or "").strip()
        return f"### {self.name}\nSignature: `{self.signature}`\n{doc}"

def get_skill_classes(skills_dir="agent/skills"):
    """
    Dynamically load all Skill classes from a directory and return as ToolSpec objects.
    """
    tools = []
    for fname in os.listdir(skills_dir):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        modname = fname[:-3]
        fpath = os.path.join(skills_dir, fname)
        spec = importlib.util.spec_from_file_location(f"agent.skills.{modname}", fpath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Find class Skill
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name == "Skill":
                doc = inspect.getdoc(obj) or ""
                sig = ""
                # Get handle_async signature
                if hasattr(obj, "handle_async"):
                    sig = str(inspect.signature(obj.handle_async))
                # Proxy for calling handle_async (new instance per call)
                def make_call(modname, obj):
                    async def call(*args, **kwargs):
                        mod = importlib.import_module(f"agent.skills.{modname}")
                        inst = getattr(mod, "Skill")()
                        method = getattr(inst, "handle_async")
                        if inspect.iscoroutinefunction(method):
                            return await method(*args, **kwargs)
                        else:
                            return method(*args, **kwargs)
                    return call
                tools.append(ToolSpec(modname, obj, doc, sig, make_call(modname, obj)))
    return tools