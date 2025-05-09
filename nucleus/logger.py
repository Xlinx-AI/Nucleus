
"""
Logger: log levels, pretty printing, markdown/code blocks, and task/status output.

"""

from enum import IntEnum

class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40

class Logger:
    """
    Logger that can print normal, markdown, code, and even rule-based messages.
    """
    def __init__(self, level: LogLevel = LogLevel.INFO):
        self.level = level

    def log(self, msg: str, level: LogLevel = LogLevel.INFO):
        if level >= self.level:
            print(f"[{level.name}] {msg}")

    def log_markdown(self, content: str, title: str = None, level: LogLevel = LogLevel.INFO):
        if level >= self.level:
            head = f"## {title}\n" if title else ""
            print(f"[{level.name}] {head}{content}")

    def log_code(self, title: str, code: str, level: LogLevel = LogLevel.INFO):
        if level >= self.level:
            print(f"[{level.name}] --- {title} ---\n```python\n{code}\n```")

    def log_rule(self, title: str, level: LogLevel = LogLevel.INFO):
        if level >= self.level:
            print(f"[{level.name}] --- {title} ---" + "-" * 40)

    def log_task(self, content: str, subtitle: str = "", level: LogLevel = LogLevel.INFO):
        if level >= self.level:
            print(f"[{level.name}] TASK: {subtitle}\n{content}")