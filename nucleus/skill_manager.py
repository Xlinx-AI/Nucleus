
import os
import uuid
import inspect
from typing import Any, Dict, List, Optional

from abc import ABC, abstractmethod

class Skill(ABC):
    """
    Base class for all skills in this hub.
    If you want to make a new one, just inherit and go wild.
    Don't forget to implement execute_async, or you'll regret it at runtime.
    """
    def __init__(self, name: str, description: str, capability: Dict[str, Any]):
        self.name = name
        self.description = description
        self.capability = capability

    @abstractmethod
    async def execute_async(self, step: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        This is supposed to run your skill asynchronously.
        If you see NotImplementedError, you forgot to actually code something.
        """
        ...

class SkillManager:
    """
    This thing loads all skills it can find, tries to inject dependencies,
    and then pretends to be smart when matching skills to steps.
    If it breaks, it's probably because you made the constructor too fancy.
    """

    def __init__(self, skills_dir: str = "assets/skills", event_bus: Any = None, llm_adapter: Any = None):
        self.skills_dir = skills_dir
        self.event_bus = event_bus
        self.llm_adapter = llm_adapter
        self.skills: Dict[str, Skill] = {}
        self.capabilities: List[Dict] = []
        self._load_all_skills()

    def _load_all_skills(self):
        """
        Loads all skills from the skills directory, tries to pass dependencies (event_bus, llm_adapter),
        and collects capabilities. If something explodes, check your __init__ signatures.
        """
        self.skills.clear()
        self.capabilities.clear()
        if not os.path.isdir(self.skills_dir):
            os.makedirs(self.skills_dir, exist_ok=True)
        for fname in os.listdir(self.skills_dir):
            if fname.endswith(".py") and not fname.startswith("_"):
                modname = fname[:-3]
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(f"skills.{modname}", os.path.join(self.skills_dir, fname))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, Skill) and obj is not Skill:
                            # Try to inject dependencies. If you made your __init__ weird, this might fail.
                            ctor = inspect.signature(obj.__init__)
                            kwargs = {}
                            if "event_bus" in ctor.parameters and self.event_bus is not None:
                                kwargs["event_bus"] = self.event_bus
                            if "llm_adapter" in ctor.parameters and self.llm_adapter is not None:
                                kwargs["llm_adapter"] = self.llm_adapter
                            try:
                                skill_instance = obj(**kwargs)
                            except Exception:
                                skill_instance = obj()
                            # If the skill has set_event_bus, call it just in case.
                            if hasattr(skill_instance, "set_event_bus") and self.event_bus is not None:
                                try:
                                    skill_instance.set_event_bus(self.event_bus)
                                except Exception:
                                    pass
                            self.skills[skill_instance.name] = skill_instance
                            # Try to gather capabilities in a flexible way.
                            if hasattr(skill_instance, "get_capabilities"):
                                for cap in skill_instance.get_capabilities():
                                    cap = cap.copy()
                                    cap["__skill_name__"] = skill_instance.name
                                    self.capabilities.append(cap)
                            elif hasattr(skill_instance, "capability"):
                                cap = skill_instance.capability.copy()
                                cap["__skill_name__"] = skill_instance.name
                                self.capabilities.append(cap)
                except Exception:
                    # If you want error logs, add them here, but at 3am I just want it to keep going.
                    pass

    def find_skill(self, step: Dict[str, Any]) -> Optional[Skill]:
        """
        Finds the best skill for the step, using a scoring system that
        works most of the time (unless your tags are a mess).
        """
        best_score = -1
        best_skill = None
        for cap in self.capabilities:
            score = 0
            if "intent" in step and "intent" in cap and step["intent"].lower() in cap["intent"].lower():
                score += 5
            if "input_type" in step and "input_type" in cap and step["input_type"] == cap["input_type"]:
                score += 3
            if "output_type" in step and "output_type" in cap and (
                step["output_type"] in cap["output_type"] or cap["output_type"] in step["output_type"]
            ):
                score += 2
            step_tags = set([t.lower() for t in step.get("tags", [])])
            cap_tags = set([t.lower() for t in cap.get("tags", [])])
            if step_tags & cap_tags:
                score += len(step_tags & cap_tags)
            if score > best_score:
                best_score = score
                best_skill = self.skills[cap["__skill_name__"]]
        return best_skill

    async def generate_skill(self, description: str) -> Skill:
        """
        Generates a new skill and registers it. Not magic, just writes a file.
        """
        name = f"skill_{uuid.uuid4().hex[:8]}"
        new_skill = Skill(name, description, {"intent": description, "input_type": "text", "output_type": "text", "tags": []})
        # Save as a Python module (for demonstration)
        skill_code = f'''
from nucleus.skill_manager import Skill
class {name.capitalize()}(Skill):
    def __init__(self):
        super().__init__("{name}", "{description}", {{"intent": "{description}", "input_type": "text", "output_type": "text", "tags": []}})
    async def execute_async(self, step, context):
        return f"Skill {name} executed for step: {{step}}"
'''
        with open(os.path.join(self.skills_dir, f"{name}.py"), "w", encoding="utf-8") as f:
            f.write(skill_code)
        self._load_all_skills()
        return self.skills[name]