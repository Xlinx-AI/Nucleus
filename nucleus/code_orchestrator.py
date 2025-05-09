
import asyncio
from typing import List, Optional, Dict, Any, Callable

class PulseMonitor:
    """
    Асинхронный heartbeat-монитор для жизненного цикла агентов. Позволяет расширять сигнал (логгирование, метрики и т.д.)
    """
    def __init__(self, interval: int = 10, signal_fn: Optional[Callable[[], None]] = None):
        self.interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.signal_fn = signal_fn

    async def _pulse(self):
        while self._running:
            if self.signal_fn:
                try:
                    self.signal_fn()
                except Exception:
                    pass
            else:
                print("💓 Heartbeat signal sent")
            await asyncio.sleep(self.interval)

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._pulse())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

class FreshCodeAgent:
    """
    Агент для создания и улучшения кода, а также интеллектуального объединения версий с помощью LLM.
    """
    def __init__(self, llm, merger, output_dir: str):
        self.llm = llm
        self.merger = merger
        self.output_dir = output_dir

    async def create_code(self, task_description: str, context_files: Optional[List[str]] = None) -> str:
        """
        Генерирует код для задачи с учётом контекстных файлов.
        """
        prompt = self._build_prompt(task_description, context_files)
        return await self.llm.complete(prompt)

    async def improve_code(self, code: str, improvement_goal: str) -> str:
        """
        Улучшает существующий код по явной цели.
        """
        prompt = f"Improve this code for the following goal: {improvement_goal}\n\n{code}"
        return await self.llm.complete(prompt)

    def _build_prompt(self, task_description: str, context_files: Optional[List[str]]) -> str:
        if context_files:
            files_summary = "\n".join([f"File: {f}" for f in context_files])
            return f"{task_description}\n\nContext:\n{files_summary}"
        return task_description

    async def smart_merge(self, original: str, new_code: str, language: str) -> str:
        """
        Интеллектуальное объединение версий кода через LLM.
        """
        return await self.merger.merge(original, new_code, language)

class CodeMergeWizard:
    """
    Интеллектуальный стратег для объединения версий кода с помощью LLM (асинхронно).
    """
    def __init__(self, llm):
        self.llm = llm

    async def merge(self, original: str, new_code: str, language: str) -> str:
        """
        Сливает две версии кода с помощью LLM.
        """
        prompt = (
            f"Merge the following two code versions in {language}.\n"
            "ORIGINAL:\n"
            f"{original}\n\n"
            "NEW:\n"
            f"{new_code}\n\n"
            "Output a single, functional, clean code result."
        )
        return await self.llm.complete(prompt)

class APIStructureAgent:
    """
    Агент, создающий или расширяющий API на основе предоставленных файлов.
    """
    def __init__(self, llm):
        self.llm = llm

    async def files_to_api(self, file_paths: List[str], base_api: Optional[str] = None) -> str:
        """
        Генерирует API-код из файлов или расширяет существующий API.
        """
        files_summary = "\n".join([f"File: {f}" for f in file_paths])
        base = f"Extend this API: {base_api}\n" if base_api else "Create a new API from the following files:\n"
        prompt = f"{base}{files_summary}\nOutput only the API code, no explanation."
        return await self.llm.complete(prompt)

class CodeAgentRegistry:
    """
    Реестр для управления код-агентами (создание, улучшение, слияние, guard).
    """
    def __init__(self):
        self.agents: Dict[str, Any] = {}

    def register(self, name: str, agent: Any):
        self.agents[name] = agent

    def get(self, name: str) -> Any:
        return self.agents.get(name)