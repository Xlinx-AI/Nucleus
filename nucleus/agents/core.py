"""
Ядро агентной архитектуры nucleus: Многошаговый агент, агент с вызовом инструментов, агент-кодогенератор.
Планирование, управление памятью, шаги взаимодействия с инструментами и LLM.
"""

import time
import inspect
from typing import Any, List, Dict, Callable, Optional, Union

from nucleus.agents.memory import (
    ActionEntry, PlanEntry, TaskEntry, SystemPromptEntry, AgentLongTermMemory
)
from nucleus.agents.tools import BaseTool, tool_description
from nucleus.agents.utils import HistoryLogger

from abc import ABC, abstractmethod

class IterativeAgent(ABC):
    """
    Многошаговый агент nucleus: решает задачу по шагам, используя инструменты, LLM и память.
    """
    def __init__(
        self,
        tools: List[BaseTool],
        llm: Callable[[List[Dict[str, str]]], Any],
        system_prompt: Optional[str] = None,
        max_steps: int = 6,
        name: Optional[str] = None,
        description: Optional[str] = None,
        callbacks: Optional[List[Callable]] = None
    ):
        self.agent_name = name or self.__class__.__name__
        self.llm = llm
        self.max_steps = max_steps
        self.step_idx = 0
        self.tools = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt or "Вы агент nucleus. Решайте задачи итеративно."
        self.memory = AgentLongTermMemory(self.system_prompt)
        self._logger = HistoryLogger()
        self.callbacks = callbacks or []

    def build_prompt(self, summary: bool = False) -> List[Dict[str, str]]:
        messages = self.memory.system_prompt.to_messages(summary=summary)
        for entry in self.memory.entries:
            messages.extend(entry.to_messages(summary=summary))
        return messages

    @abstractmethod
    def step(self, action_entry: ActionEntry) -> Optional[Any]:
        """
        Этот метод должен быть реализован в потомках для выполнения одного шага reasoning/действия.
        """
        ...

    def run(self, task: str, images: Optional[List[str]] = None, reset: bool = True) -> Any:
        """
        Запускает решение задачи с нуля (или продолжает с текущей памяти).
        """
        self.task = task
        if reset:
            self.memory.reset()
        self.memory.entries.append(TaskEntry(task=task, images=images))
        self.step_idx = 1
        result = None
        while result is None and self.step_idx <= self.max_steps:
            action = ActionEntry(step_idx=self.step_idx)
            result = self.step(action)
            action.finished_at = time.time()
            self.memory.entries.append(action)
            for cb in self.callbacks:
                cb(action)
            self.step_idx += 1
class ToolCallingAgent(IterativeAgent):
    """
    Агент nucleus, использующий LLM для генерации JSON-вызовов инструментов (интеграция с внешними tool-calls).
    """
    def step(self, action_entry: ActionEntry) -> Optional[Any]:
        messages = self.build_prompt()
        action_entry.model_inputs = messages.copy()
        reply = self.llm(
            messages,
            tools_to_call_from=list(self.tools.values()),
            stop_sequences=["Observation:"]
        )
        action_entry.llm_output_msg = reply
        # Предполагаем, что reply.tool_calls — список вызовов инструментов
        if not getattr(reply, "tool_calls", None):
            action_entry.error = "LLM не вызвал ни одного инструмента. Используйте 'final_answer' для завершения."
            return None
        tool_call = reply.tool_calls[0]
        tool_name = getattr(tool_call.function, "name", None)
        tool_args = getattr(tool_call.function, "arguments", None)
        tool_id = getattr(tool_call, "id", "")
        action_entry.tool_invocations = [ToolInvocation(name=tool_name, args=tool_args, uid=tool_id)]
        if tool_name == "final_answer":
            answer = tool_args.get("answer") if isinstance(tool_args, dict) and "answer" in tool_args else tool_args
            action_entry.result = answer
            return answer
        else:
            # Вызов инструмента
            tool = self.tools.get(tool_name)
            if tool is None:
                action_entry.error = f"Неизвестный инструмент: {tool_name}"
                return None
            try:
                observation = tool(**tool_args) if isinstance(tool_args, dict) else tool(tool_args)
                action_entry.observations = str(observation)
            except Exception as ex:
                action_entry.error = f"Ошибка вызова инструмента {tool_name}: {ex}"
            return None

class CodeGenAgent(IterativeAgent):
    """
    Агент nucleus, который формирует шаги решения в виде кода на Python, парсит и исполняет их.
    """
    def __init__(
        self,
        tools: List[BaseTool],
        llm: Callable[[List[Dict[str, str]]], Any],
        python_executor: Callable[[str, dict], Any],
        system_prompt: Optional[str] = None,
        max_steps: int = 6,
        name: Optional[str] = None,
        description: Optional[str] = None,
        callbacks: Optional[List[Callable]] = None
    ):
        super().__init__(
            tools=tools,
            llm=llm,
            system_prompt=system_prompt,
            max_steps=max_steps,
            name=name,
            description=description,
            callbacks=callbacks
        )
        self._python_executor = python_executor

    def step(self, action_entry: ActionEntry) -> Optional[Any]:
        messages = self.build_prompt()
        action_entry.model_inputs = messages.copy()
        reply = self.llm(
            messages,
            stop_sequences=["<end_code>", "Observation:"]
        )
        action_entry.llm_output_msg = reply
        code_blob = self._extract_code(reply.content)
        action_entry.llm_output = reply.content
        action_entry.tool_invocations = [ToolInvocation(name="python_executor", args=code_blob, uid=f"exec_{self.step_idx}")]
        try:
            output, logs, is_final = self._python_executor(code_blob, {})
            action_entry.observations = logs
            action_entry.result = output
            if is_final:
                return output
            return None
        except Exception as ex:
            action_entry.error = f"Ошибка исполнения кода: {ex}"
            return None

    @staticmethod
    def _extract_code(llm_output: str) -> str:
        """
        Извлекает кодовый блок из ответа LLM (` ```py ... ``` `).
        """
        import re
        pattern = r"```(?:py|python)?\n(.*?)\n```"
        match = re.search(pattern, llm_output, re.DOTALL)
        if match:
            return match.group(1).strip()
        return llm_output
        return result

    def __call__(self, request: str, **kwargs):
        """
        Вызов агента как функции.
        """
        return self.run(request, **kwargs)