
import asyncio
import uuid
from typing import Any, Dict, Optional, Callable

from .event_bus import EventBus, Event
from .agent_system import AgentSystem
from .skill_manager import SkillManager
from .data_pipeline import DataPipeline
from .vector_db import VectorDatabase
from .crawler_hub import CrawlerHub
from .rl_loop import ReinforcementLoop
from .ui_server import UIServer
from .prompt_engine import PromptEngine
from .utils import ContextHistory

class ApplicationCore:
    """
    This is the agent core. It glues together event bus, skill management,
    planning and all the stuff you wish you could automate at 2am.
    If you need something more, just add it, but don't blame me if it breaks.
    """

    def __init__(self, llm_fn: Optional[Callable[[str], str]] = None, prompt_engine: Optional[PromptEngine] = None):
        # Event bus is where everything yells at each other asynchronously.
        self.event_bus = EventBus()
        # Now we actually get a real history, not just a sad list.
        self.history = ContextHistory()
        # Yeah, autocoder registry is still a stub.
        self.autocoder_registry = None
        # PromptEngine is here, but don't expect magic.
        self.prompt_engine = prompt_engine or PromptEngine()
        # AgentSystem does the planning and step execution, fueled by caffeine.
        self.agent_system = AgentSystem(self.event_bus, self.history, llm_fn=llm_fn, prompt_engine=self.prompt_engine)
        self.skill_manager = SkillManager(llm_adapter=llm_fn)
        self.data_pipeline = DataPipeline(self.history)
        self.vector_db = VectorDatabase()
        self.crawler_hub = CrawlerHub(self.history)
        self.rl_loop = ReinforcementLoop()
        self.ui_server = UIServer(self)
        self.loop = asyncio.get_event_loop()
        self._register_events()

    def _register_events(self):
        """
        Registers all the async event handlers. Because everything is an event when you're tired.
        """
        self.event_bus.subscribe("task", self.handle_task)
        self.event_bus.subscribe("ingest", self.handle_ingest)
        self.event_bus.subscribe("crawl", self.handle_crawl)
        self.event_bus.subscribe("skill_generate", self.handle_skill_generate)
        self.event_bus.subscribe("plan", self.handle_plan)

    async def handle_task(self, event: Event):
        """
        Handles a user task:
        - logs user input
        - builds a plan (if the LLM is awake)
        - executes steps (if skills exist)
        - logs every embarrassing failure
        """
        task_id = event.meta.get("task_id") if event.meta else str(uuid.uuid4())
        user_query = event.payload
        meta = {"task_id": task_id}
        # Log user input for the ages.
        self.history.add_user(user_query, meta=meta)
        await self.event_bus.publish(Event("trace", {"role": "user", "content": user_query, "type": "user", "meta": meta}, meta))
        # Try to build a plan, hope it doesn't timeout.
        plan = await self.agent_system.plan_task(user_query, task_id=task_id)
        self.history.add_plan(str(plan), meta=meta)
        await self.event_bus.publish(Event("trace", {"role": "plan", "content": str(plan), "type": "plan", "meta": meta}, meta))
        # Execute steps, one by one, even if you want to quit.
        results = []
        for idx, step in enumerate(plan):
            progress = {"current": idx + 1, "total": len(plan), "step": step, "task_id": task_id}
            await self.event_bus.publish(Event("progress", {"role": "system", "content": f"Executing step {idx+1}/{len(plan)}: {step}", "type": "progress", "meta": meta}, meta))
            self.history.add_thought(f"Executing step {idx+1}: {step}", meta=meta)
            result = await self.agent_system.execute_step(step, task_id)
            results.append(result)
        self.history.add_assistant(f"Task results: {results}", meta=meta)
        await self.event_bus.publish(Event("result", results, meta))

    async def handle_ingest(self, event: Event):
        """
        Handles data ingestion, chunking, embeddings, and vector DB.
        If it fails, blame the embeddings, not me.
        """
        files = event.payload.get("files")
        params = event.payload.get("params", {})
        chunks = self.data_pipeline.chunk(files, **params)
        vectors = self.data_pipeline.ingest_chunks(chunks, **params)
        self.vector_db.store_vectors(vectors)
        self.history.add_message("pipeline", f"Ingested {len(vectors)} chunks", type="pipeline", meta=event.meta)

    async def handle_crawl(self, event: Event):
        """
        Crawls some data source. Web, github, arxiv, whatever.
        If you want more, write your own crawler.
        """
        crawl_type = event.payload.get("type")
        target = event.payload.get("target")
        crawled_data = await self.crawler_hub.crawl(crawl_type, target)
        self.history.add_message("crawler", f"Crawled {crawl_type} target={target}", type="crawler", meta=event.meta)

    async def handle_skill_generate(self, event: Event):
        """
        Generates a new skill from a description. Don't expect miracles.
        """
        skill_desc = event.payload
        new_skill = await self.skill_manager.generate_skill(skill_desc)
        self.history.add_message("skill", f"Generated skill: {new_skill}", type="skill", meta=event.meta)

    async def handle_plan(self, event: Event):
        """
        Handles replanning. Because sometimes the first plan is garbage.
        """
        task = event.payload
        plan = await self.agent_system.plan_task(task)
        self.history.add_plan(f"Re-planned: {plan}", meta=event.meta)

    def _log(self, role: str, content: str, meta: Optional[Dict] = None, msg_type: str = "msg"):
        """
        This is kept for backward compatibility. It just dumps to ContextHistory now.
        """
        self.history.add_message(role, content, type=msg_type, meta=meta)

    def run(self):
        """
        Starts the event loop. If it hangs, try more coffee. Or Ctrl+C.
        """
        self.loop.run_forever()

    def submit_task(self, user_query: str):
        """
        Publishes a new task to the event bus for async handling.
        """
        task_id = str(uuid.uuid4())
        asyncio.ensure_future(self.event_bus.publish(Event("task", user_query, {"task_id": task_id})))
        return task_id