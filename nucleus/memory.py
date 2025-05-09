"""
Agent memory structures: tool calls, planning, action, and task steps for conversational memory.

"""

from dataclasses import dataclass, asdict
from typing import Any, List, Optional, Union, Dict
from abc import ABC, abstractmethod

@dataclass
class ToolCall:
    name: str
    arguments: Any
    id: str

    def dict(self):
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments,
            },
        }

@dataclass
class MemoryStep(ABC):
    def dict(self):
        return asdict(self)

    @abstractmethod
    def to_messages(self, **kwargs) -> List[Dict[str, Any]]:
        ...

@dataclass
class ActionStep(MemoryStep):
    model_input_messages: Optional[List[dict]] = None
    tool_calls: Optional[List[ToolCall]] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    step_number: Optional[int] = None
    error: Optional[str] = None
    duration: Optional[float] = None
    model_output_message: Optional[str] = None
    model_output: Optional[str] = None
    observations: Optional[str] = None
    observations_images: Optional[List[str]] = None
    action_output: Any = None

@dataclass
class PlanningStep(MemoryStep):
    model_input_messages: List[dict]
    model_output_message_facts: str
    facts: str
    model_output_message_plan: str
    plan: str

@dataclass
class TaskStep(MemoryStep):
    task: str
    task_images: Optional[List[str]] = None

@dataclass
class SystemPromptStep(MemoryStep):
    system_prompt: str

class AgentMemory:
    def __init__(self, system_prompt: str):
        self.system_prompt = SystemPromptStep(system_prompt=system_prompt)
        self.steps: List[Union[TaskStep, ActionStep, PlanningStep]] = []

    def reset(self):
        self.steps = []

    def get_succinct_steps(self) -> list:
        return [
            {key: value for key, value in step.dict().items() if key != "model_input_messages"} for step in self.steps
        ]

    def get_full_steps(self) -> list:
        return [step.dict() for step in self.steps]