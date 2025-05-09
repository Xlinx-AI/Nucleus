"""
Модельные структуры nucleus.agents: сообщения чата, роли, аргументы инструментов, базовые абстракции моделей.
"""

import json
from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Optional, Dict, Union

class RoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    TOOL_RESP = "tool_response"

@dataclass
class ToolCallDef:
    args: Any
    name: str
    desc: Optional[str] = None

@dataclass
class ToolCall:
    function: ToolCallDef
    uid: str
    call_type: str

@dataclass
class ChatMsg:
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    raw: Optional[Any] = None

    def to_json(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

def parse_if_json(data: Union[str, dict]) -> Union[dict, str]:
    if isinstance(data, dict):
        return data
    try:
        return json.loads(data)
    except Exception:
        return data

def parse_tool_args(msg: ChatMsg) -> ChatMsg:
    if msg.tool_calls:
        for call in msg.tool_calls:
            call.function.args = parse_if_json(call.function.args)
    return msg

from abc import ABC, abstractmethod

class BaseModel(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.last_input_tokens = None
        self.last_output_tokens = None

    @abstractmethod
    def __call__(self, messages: List[Dict[str, str]], **kwargs) -> ChatMsg:
        """
        Абстрактный вызов модели. Возвращает ChatMsg.
        """
        ...