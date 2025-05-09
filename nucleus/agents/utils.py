"""
Вспомогательные утилиты nucleus.agents: декораторы, сериализация, обработка ошибок, JSON, преобразования, сокращение строк.
"""

import json
import functools
import time
import inspect

def ensure_serializable(obj):
    """
    Рекурсивно приводит объект к сериализуемому виду для JSON.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        # Пробуем разобрать строку как JSON, если похоже на объект/массив
        if isinstance(obj, str):
            try:
                if (obj.startswith("{") and obj.endswith("}")) or (obj.startswith("[") and obj.endswith("]")):
                    parsed = json.loads(obj)
                    return ensure_serializable(parsed)
            except Exception:
                pass
        return obj
    if isinstance(obj, (list, tuple)):
        return [ensure_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): ensure_serializable(v) for k, v in obj.items()}
    if hasattr(obj, "__dict__"):
        return {"_type": obj.__class__.__name__, **{k: ensure_serializable(v) for k, v in obj.__dict__.items()}}
    return str(obj)

def truncate_str(text, max_len=10000):
    """
    Обрезает строку до max_len, добавляя маркер, если превышено.
    """
    if len(text) <= max_len:
        return text
    return text[:max_len // 2] + "\n...[TRUNCATED]...\n" + text[-max_len // 2:]

def catch_agent_errors(func):
    """
    Декоратор для перехвата и печати ошибок агентов.
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[NucleusAgentError]: {e}")
            return None
    return wrapped

class NucleusAgentError(Exception):
    """
    Базовая ошибка nucleus.agents.
    """
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def as_dict(self):
        return {"type": self.__class__.__name__, "message": str(self.msg)}

class AgentParseError(NucleusAgentError): pass
class AgentExecError(NucleusAgentError): pass
class AgentStepLimitError(NucleusAgentError): pass
class AgentGenError(NucleusAgentError): pass

class HistoryLogger:
    """
    История сообщений, планов, шагов и прочего для nucleus.agents.
    """
    def __init__(self, max_size=2000):
        self.entries = []
        self.max_size = max_size

    def _trim(self):
        while len(json.dumps(self.entries)) > self.max_size and len(self.entries) > 1:
            self.entries.pop(0)

    def add(self, role, content, type="msg", meta=None, parent_id=None):
        entry = {
            "role": role,
            "type": type,
            "content": str(content)[:self.max_size // 4],
            "timestamp": time.time(),
            "meta": meta or {},
            "parent_id": parent_id,
        }
        self.entries.append(entry)
        self._trim()

    def add_plan(self, plan, meta=None, parent_id=None):
        self.add("plan", plan, type="plan", meta=meta, parent_id=parent_id)

    def add_skill(self, skill, args, result=None, meta=None, parent_id=None):
        content = f"Skill: {skill}({args})"
        if result is not None:
            content += f"\nResult: {str(result)[:self.max_size // 4]}"
        self.add("skill", content, type="skill", meta=meta, parent_id=parent_id)

    def add_user(self, msg, meta=None, parent_id=None):
        self.add("user", msg, type="msg", meta=meta, parent_id=parent_id)

    def add_agent(self, msg, meta=None, parent_id=None):
        self.add("agent", msg, type="msg", meta=meta, parent_id=parent_id)

    def as_str(self):
        if not self.entries:
            return "<No history>"
        return "\n---\n".join(f"[{e['role']}|{e['type']}] {e['content']}" for e in self.entries)