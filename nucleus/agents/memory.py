"""
Модуль memory для nucleus: шаги памяти, записи вызова инструментов, сериализация истории, преобразование в сообщения для LLM.
"""

from dataclasses import dataclass, asdict
from typing import Any, List, Dict, Optional, Union

from nucleus.agents.types import NucleusTextResult, NucleusImageResult, NucleusAudioResult

@dataclass
class ToolInvocation:
    name: str
    args: Any
    uid: str

    def as_dict(self):
        return {
            "id": self.uid,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.args,
            }
        }

@dataclass
class MemoryEntry:
    def as_dict(self):
        return asdict(self)

    def to_messages(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Базовая реализация: не возвращает сообщений.
        """
        return []

@dataclass
class ActionEntry(MemoryEntry):
    model_inputs: Optional[List[dict]] = None
    tool_invocations: Optional[List[ToolInvocation]] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    step_idx: Optional[int] = None
    error: Optional[str] = None
    elapsed: Optional[float] = None
    llm_output_msg: Optional[Any] = None
    llm_output: Optional[str] = None
    observations: Optional[str] = None
    obs_images: Optional[List[str]] = None
    result: Any = None

    def to_messages(self, summary: bool = False, show_inputs: bool = False) -> List[Dict[str, Any]]:
        messages = []
        if self.model_inputs and show_inputs:
            messages.append({"role": "system", "content": self.model_inputs})
        if self.llm_output and not summary:
            messages.append({
                "role": "assistant",
                "content": [{"type": "text", "text": self.llm_output.strip()}]
            })
        if self.tool_invocations:
            messages.append({
                "role": "assistant",
                "content": [{
                    "type": "text",
                    "text": "Вызовы инструментов:\n" + str([t.as_dict() for t in self.tool_invocations])
                }]
            })
        if self.observations:
            messages.append({
                "role": "tool_response",
                "content": [{
                    "type": "text",
                    "text": f"Call id: {self.tool_invocations[0].uid if self.tool_invocations else ''}\nObservation:\n{self.observations}"
                }]
            })
        if self.error:
            error_msg = "Ошибка:\n" + str(self.error) + "\nПопробуйте другой подход для устранения ошибки."
            msg = f"Call id: {self.tool_invocations[0].uid if self.tool_invocations else ''}\n" + error_msg
            messages.append({"role": "tool_response", "content": [{"type": "text", "text": msg}]})
        if self.obs_images:
            img_msgs = [{"type": "image", "image": img} for img in self.obs_images]
            messages.append({"role": "user", "content": [{"type": "text", "text": "Получены изображения:"}] + img_msgs})
        return messages

@dataclass
class PlanEntry(MemoryEntry):
    model_inputs: List[dict]
    model_output_facts: Any
    facts: str
    model_output_plan: Any
    plan: str

    def to_messages(self, summary: bool = False, **kwargs) -> List[Dict[str, Any]]:
        msgs = []
        msgs.append({"role": "assistant", "content": [{"type": "text", "text": f"[ФАКТЫ]:\n{self.facts.strip()}"}]})
        if not summary:
            msgs.append({"role": "assistant", "content": [{"type": "text", "text": f"[ПЛАН]:\n{self.plan.strip()}"}]})
        return msgs

@dataclass
class TaskEntry(MemoryEntry):
    task: str
    images: Optional[List[str]] = None

    def to_messages(self, summary: bool = False, **kwargs) -> List[Dict[str, Any]]:
        content = [{"type": "text", "text": f"Постановка задачи:\n{self.task}"}]
        if self.images:
            content += [{"type": "image", "image": img} for img in self.images]
        return [{"role": "user", "content": content}]

@dataclass
class SystemPromptEntry(MemoryEntry):
    system_prompt: str

    def to_messages(self, summary: bool = False, **kwargs) -> List[Dict[str, Any]]:
        if summary:
            return []
        return [{"role": "system", "content": [{"type": "text", "text": self.system_prompt.strip()}]}]

class AgentLongTermMemory:
    """
    Класс для хранения и сериализации шагов агента.
    """
    def __init__(self, system_prompt: str):
        self.system_prompt = SystemPromptEntry(system_prompt=system_prompt)
        self.entries: List[Union[TaskEntry, ActionEntry, PlanEntry]] = []

    def reset(self):
        self.entries = []

    def get_steps(self, full: bool = False) -> List[dict]:
        if full:
            return [entry.as_dict() for entry in self.entries]
        return [{k: v for k, v in entry.as_dict().items() if k != "model_inputs"} for entry in self.entries]