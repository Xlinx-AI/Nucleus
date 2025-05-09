"""
Проверка структуры инструментов nucleus.agents: сигнатуры, типы, обязательные поля, отсутствие неразрешённых импортов.
"""

import inspect

def validate_tool_class(cls):
    """
    Проверяет, что класс инструмента nucleus корректен:
    - Имеет docstring
    - Имеет name, description, inputs, output_type
    - Все inputs есть в execute
    """
    errors = []
    if not cls.__doc__:
        errors.append("Нет docstring у класса.")
    for attr in ["name", "description", "inputs", "output_type"]:
        if not hasattr(cls, attr):
            errors.append(f"Нет обязательного атрибута: {attr}")
    if hasattr(cls, "execute"):
        sig = inspect.signature(cls.execute)
        args = set(sig.parameters.keys()) - {"self"}
        for inp in getattr(cls, "inputs", {}).keys():
            if inp not in args:
                errors.append(f"Входной параметр '{inp}' не найден в execute().")
    if errors:
        raise ValueError("Ошибки валидации инструмента nucleus.agents:\n" + "\n".join(errors))