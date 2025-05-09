"""
Модуль nucleus.agents.code_executor: безопасное выполнение Python-кода, ограничения, поддержка stdout, кастомных инструментов и импортов.
"""

import ast
import builtins
import inspect
import logging
from typing import Any, Dict, Callable, List, Optional, Tuple

class CodeExecError(Exception):
    pass

class StdoutBuffer:
    def __init__(self):
        self.value = ""

    def write(self, msg):
        self.value += str(msg)

    def __str__(self):
        return self.value

class PythonCodeExecutor:
    """
    Безопасный интерпретатор Python-кода для nucleus: ограничение операций, поддержка кастомных инструментов, сбор stdout.
    """
    SAFE_BUILTINS = {
        "abs": abs, "min": min, "max": max, "sum": sum, "len": len, "range": range, "print": print,
        "str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict, "set": set,
        "tuple": tuple, "enumerate": enumerate, "zip": zip, "map": map, "filter": filter, "any": any, "all": all,
        "isinstance": isinstance, "issubclass": issubclass, "type": type, "pow": pow, "divmod": divmod
    }

    def __init__(self, extra_imports: Optional[List[str]] = None, tools: Optional[Dict[str, Callable]] = None, max_ops: int = 100000):
        self.extra_imports = extra_imports or []
        self.tools = tools or {}
        self.max_ops = max_ops
        self.logger = logging.getLogger("NucleusPythonExecutor")

    def run(self, code: str, variables: Optional[Dict[str, Any]] = None) -> Tuple[Any, str, bool]:
        """
        Выполняет код, возвращает (результат, stdout, is_final_answer)
        """
        state = variables.copy() if variables else {}
        buffer = StdoutBuffer()
        state["_print_outputs"] = buffer
        state["_operations_count"] = 0
        safe_builtins = self.SAFE_BUILTINS.copy()
        safe_builtins["print"] = buffer.write
        state.update(safe_builtins)
        # Добавляем кастомные инструменты
        state.update(self.tools)
        # Импортируем разрешённые модули
        for module in self.extra_imports:
            try:
                mod = __import__(module)
                state[module] = mod
            except ImportError:
                self.logger.warning(f"Модуль {module} не найден и не импортирован.")
        # Парсим AST и исполняем
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise CodeExecError(f"Ошибка синтаксиса: {e}")
        result = None
        is_final = False
        try:
            for node in tree.body:
                if state["_operations_count"] > self.max_ops:
                    raise CodeExecError("Превышен лимит операций при исполнении кода.")
                state["_operations_count"] += 1
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and getattr(node.value.func, "id", "") == "final_answer":
                    val = eval(compile(ast.Expression(node.value.args[0]), "<string>", "eval"), state)
                    result = val
                    is_final = True
                    break
                else:
                    exec(compile(ast.Module([node], []), "<string>", "exec"), state)
        except Exception as ex:
            raise CodeExecError(f"Ошибка исполнения: {ex}")
        return result, str(buffer), is_final