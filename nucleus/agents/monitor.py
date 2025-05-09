"""
Модуль nucleus.agents.monitor: логирование шагов агента, уровни логов, мониторинг метрик, визуализация структуры.
"""

from enum import IntEnum
from typing import List, Optional, Any

class LogLevel(IntEnum):
    CRITICAL = 0
    INFO = 1
    DEBUG = 2

YELLOW = "#e5e000"

class AgentLogger:
    """
    Логгер для агентов nucleus: поддержка уровней, markdown, код, дерево, задачи и шаги.
    """
    def __init__(self, level: LogLevel = LogLevel.INFO):
        self.level = level

    def log(self, msg: Any, level: LogLevel = LogLevel.INFO):
        if level <= self.level:
            print(f"[{level.name}] {msg}")

    def log_markdown(self, content: str, title: Optional[str] = None, level: LogLevel = LogLevel.INFO):
        if level <= self.level:
            head = f"== {title} ==\n" if title else ""
            print(f"[{level.name}] {head}{content}")

    def log_code(self, title: str, code: str, level: LogLevel = LogLevel.INFO):
        if level <= self.level:
            print(f"[{level.name}] --- {title} ---\n```python\n{code}\n```")

    def log_tree(self, agent):
        def walk(node, indent=0):
            print("    " * indent + f"- {getattr(node, 'agent_name', node.__class__.__name__)}")
            if hasattr(node, "tools"):
                for t in getattr(node, "tools", {}).values():
                    print("    " * (indent+1) + f"* Tool: {t.name}")
            if hasattr(node, "managed_agents"):
                for sub in getattr(node, "managed_agents", {}).values():
                    walk(sub, indent+1)
        walk(agent)

class AgentMonitor:
    """
    Мониторирует шаги и метрики агента nucleus (длительность, токены, шаги).
    """
    def __init__(self, model, logger: AgentLogger):
        self.durations = []
        self.model = model
        self.logger = logger
        self.input_tokens = 0
        self.output_tokens = 0

    def update(self, step_log):
        dur = getattr(step_log, "duration", None)
        if dur is not None:
            self.durations.append(dur)
        if hasattr(self.model, "last_input_token_count"):
            self.input_tokens += getattr(self.model, "last_input_token_count", 0)
            self.output_tokens += getattr(self.model, "last_output_token_count", 0)
        self.logger.log(f"Step #{len(self.durations)}: {dur}s | Input tokens: {self.input_tokens} | Output: {self.output_tokens}", level=LogLevel.DEBUG)

    def reset(self):
        self.durations = []
        self.input_tokens = 0
        self.output_tokens = 0