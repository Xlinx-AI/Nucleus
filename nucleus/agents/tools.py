"""
Модуль инструментов nucleus.agents: базовый класс Tool, декораторы, коллекции, загрузчики, шаблоны описаний, Gradio-интерфейс.
"""

import inspect
import functools
import os
import tempfile
from typing import Any, Dict, List, Optional, Callable, Union

from nucleus.agents.utils import ensure_serializable

SUPPORTED_TYPES = [
    "string", "boolean", "integer", "number", "image", "audio", "array", "object", "any", "null"
]

from abc import ABC, abstractmethod

class BaseTool(ABC):
    """
    Базовый класс для инструментов nucleus.
    Не забудьте реализовать метод execute!
    """
    name: str
    description: str
    inputs: Dict[str, Dict[str, Any]]
    output_type: str

    def __init__(self):
        self._ready = False

    def validate(self):
        # Проверка обязательных атрибутов и типов
        for attr, typ in {"name": str, "description": str, "inputs": dict, "output_type": str}.items():
            val = getattr(self, attr, None)
            if val is None or not isinstance(val, typ):
                raise ValueError(f"Tool.{attr} должен быть типа {typ.__name__}")
        for k, v in self.inputs.items():
            if not isinstance(v, dict) or "type" not in v or "description" not in v:
                raise ValueError(f"Input '{k}' должен быть словарём с ключами 'type' и 'description'.")
            if v["type"] not in SUPPORTED_TYPES:
                raise ValueError(f"Неподдерживаемый тип '{v['type']}' для '{k}'")
        if self.output_type not in SUPPORTED_TYPES:
            raise ValueError(f"Tool.output_type '{self.output_type}' не поддерживается")

    @abstractmethod
    def execute(self, *args, **kwargs):
        """
        Основная логика инструмента.
        """
        ...

    def __call__(self, *args, sanitize_io: bool = False, **kwargs):
        if not self._ready:
            self.setup()
        # Поддержка передачи аргументов как dict
        if len(args) == 1 and not kwargs and isinstance(args[0], dict):
            if all(key in self.inputs for key in args[0]):
                kwargs = args[0]
                args = ()
        result = self.execute(*args, **kwargs)
        return ensure_serializable(result)

    def setup(self):
        """
        Готовит инструмент к работе (например, загрузка модели).
        """
        self._ready = True

    def save_code(self, output_dir):
        """
        Сохраняет исходный код инструмента в output_dir.
        """
        os.makedirs(output_dir, exist_ok=True)
        class_name = self.__class__.__name__
        tool_file = os.path.join(output_dir, "tool.py")
        # Сохраняем только сигнатуру класса и execute
        code = f"""from nucleus.agents.tools import BaseTool

class {class_name}(BaseTool):
    name = "{self.name}"
    description = "{self.description}"
    inputs = {self.inputs}
    output_type = "{self.output_type}"

    def execute(self, *args, **kwargs):
        # Реализуйте здесь свою логику
        pass
"""
        with open(tool_file, "w", encoding="utf-8") as f:
            f.write(code)

def tool(fn: Callable) -> BaseTool:
    """
    Декоратор для создания простого инструмента nucleus из функции.
    """
    sig = inspect.signature(fn)
    params = {
        k: {"type": "string", "description": v.annotation.__name__ if v.annotation != inspect._empty else "Any"}
        for k, v in sig.parameters.items() if k != "self"
    }
    class SimpleTool(BaseTool):
        name = fn.__name__
        description = fn.__doc__ or "Без описания"
        inputs = params
        output_type = "string"
        def execute(self, *args, **kwargs):
            return fn(*args, **kwargs)
    return SimpleTool()

class ToolSet:
    """
    Коллекция инструментов nucleus.
    """
    def __init__(self, tool_list: List[BaseTool]):
        self.tools = {t.name: t for t in tool_list}

    def __getitem__(self, name):
        return self.tools[name]

    def __iter__(self):
        return iter(self.tools.values())

def tool_description(tool: BaseTool) -> str:
    """
    Формирует строковое описание инструмента для промпта.
    """
    desc = f"- {tool.name}: {tool.description}\n  Аргументы: {tool.inputs}\n  Возвращает: {tool.output_type}"
    return desc

def launch_gradio_tool(tool: BaseTool):
    """
    Запускает Gradio-интерфейс для инструмента nucleus.
    """
    try:
        import gradio as gr
    except ImportError:
        raise ImportError("Установите gradio для запуска интерфейса.")
    def wrapper(*args, **kwargs):
        return tool(*args, sanitize_io=True, **kwargs)
    wrapper.__signature__ = inspect.signature(tool.execute)
    gr.Interface(
        fn=wrapper,
        inputs=[gr.Textbox(label=name) for name in tool.inputs.keys()],
        outputs=gr.Textbox(label="Результат"),
        title=tool.name,
        description=tool.description
    ).launch()