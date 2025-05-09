from nucleus.skill_manager import Skill

class DuckDuckGoSkill(Skill):
    """
    This skill wraps DuckDuckGo search from oarc-crawlers.
    If you want Google, well, that's for another time.
    """
    def __init__(self, event_bus=None):
        super().__init__(
            name="duckduckgo_search",
            description="Does DuckDuckGo search and returns formatted results.",
            capability=None
        )
        self.event_bus = event_bus
        try:
            from oarc_crawlers import DuckDuckGoSearcher as OARCDuckDuckGoSearcher
            import os
            self.searcher = OARCDuckDuckGoSearcher(data_dir=os.getenv('DATA_DIR', 'data'))
        except Exception:
            self.searcher = None

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "DuckDuckGo search",
                "desc": "Searches DuckDuckGo and returns results in markdown.",
                "input_type": "query",
                "output_type": "markdown",
                "tags": ["duckduckgo", "search", "web", "results"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me a step with a query, and I'll try to fetch results.
        """
        if not self.searcher:
            return {"error": "DuckDuckGo searcher not available."}
        query = step.get("query") or step.get("input") or ""
        max_results = step.get("max_results", 5)
        return await self.searcher.text_search(query, max_results=max_results)