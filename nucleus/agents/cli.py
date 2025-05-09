"""
CLI-интерфейс nucleus.agents: запуск reasoning- и tool-calling-агентов через командную строку.
"""

import argparse
import os

from nucleus.agents.core import IterativeAgent, ToolCallingAgent, CodeGenAgent
from nucleus.agents.tools import BaseTool
from nucleus.agents.prompts import CODE_AGENT_PROMPT, TOOL_AGENT_PROMPT
from nucleus.agents.code_executor import PythonCodeExecutor

def parse_args():
    parser = argparse.ArgumentParser(description="Nucleus Agents CLI")
    parser.add_argument("prompt", type=str, help="Запрос для агента")
    parser.add_argument("--mode", choices=["code", "tool"], default="code", help="Режим агента")
    parser.add_argument("--model", type=str, default="stub", help="ID/тип LLM-модели")
    parser.add_argument("--tools", nargs="*", default=[], help="Список инструментов")
    parser.add_argument("--imports", nargs="*", default=[], help="Дополнительные разрешённые импорты")
    return parser.parse_args()

def dummy_llm(messages, **kwargs):
    # Заглушка для LLM: возвращает последний запрос пользователя как assistant-ответ
    last = messages[-1]["content"] if messages else "ok"
    class DummyReply:
        content = last
        tool_calls = None
    return DummyReply()

def main():
    args = parse_args()
    # Инициализация инструментов
    tools = []
    for tool_name in args.tools:
        # В реальности здесь должен быть загрузчик инструментов
        t = BaseTool()
        t.name = tool_name
        t.description = f"Инструмент {tool_name}"
        t.inputs = {"input": {"type": "string", "description": "Вход"}}
        t.output_type = "string"
        t.execute = lambda input: f"{tool_name} получил {input}"
        tools.append(t)
    # Инициализация Python-кодового исполнителя
    executor = PythonCodeExecutor(extra_imports=args.imports)
    # Выбор агента
    if args.mode == "code":
        agent = CodeGenAgent(
            tools=tools,
            llm=dummy_llm,
            python_executor=executor.run,
            system_prompt=CODE_AGENT_PROMPT.format(tool_descriptions=", ".join([t.name for t in tools]))
        )
    else:
        agent = ToolCallingAgent(
            tools=tools,
            llm=dummy_llm,
            system_prompt=TOOL_AGENT_PROMPT.format(tool_descriptions=", ".join([t.name for t in tools]))
        )
    result = agent.run(args.prompt)
    print("Ответ агента:", result)

if __name__ == "__main__":
    main()