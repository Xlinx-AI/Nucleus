from nucleus.skill_manager import Skill

class ArxivSearchSkill(Skill):
    """
    This skill searches arXiv for papers and grabs metadata or formats it for learning.
    If arXiv is down, just go read a book.
    """
    def __init__(self, event_bus=None):
        super().__init__(
            name="arxiv_search",
            description="Searches arXiv, fetches paper metadata, and formats it for learning.",
            capability=None
        )
        self.event_bus = event_bus
        try:
            from oarc_crawlers import ArxivFetcher
            import os
            self.fetcher = ArxivFetcher(data_dir=os.getenv('DATA_DIR', 'data'))
        except Exception:
            self.fetcher = None

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Fetch arxiv paper",
                "desc": "Fetches metadata for an arXiv paper.",
                "input_type": "arxiv_id",
                "output_type": "json",
                "tags": ["arxiv", "paper", "fetch", "metadata"]
            },
            {
                "intent": "Format arxiv paper",
                "desc": "Formats arXiv paper metadata for learning.",
                "input_type": "json",
                "output_type": "markdown",
                "tags": ["arxiv", "paper", "format", "markdown"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me a step with intent and either arxiv_id or paper_info, and I'll fetch or format.
        """
        if not self.fetcher:
            return {"error": "ArxivFetcher not available."}
        intent = step.get("intent", "").lower()
        if "fetch" in intent:
            arxiv_id = step.get("arxiv_id") or step.get("input") or ""
            return await self.fetcher.fetch_paper_info(arxiv_id)
        elif "format" in intent:
            paper_info = step.get("paper_info") or step.get("input") or {}
            return await self.format_paper_for_learning(paper_info)
        else:
            return {"error": "Unknown arxiv search intent."}

    async def format_paper_for_learning(self, paper_info):
        # This just dumps out markdown for the paper, in a way that's readable at 2am.
        try:
            formatted_text = f"# {paper_info.get('title', '')}\n\n"
            formatted_text += f"**Authors:** {', '.join(paper_info.get('authors', []))}\n\n"
            formatted_text += f"**Published:** {paper_info.get('published', '')[:10]}\n\n"
            formatted_text += f"**Categories:** {', '.join(paper_info.get('categories', []))}\n\n"
            formatted_text += "## Abstract\n" + paper_info.get('abstract', '') + "\n\n"
            formatted_text += f"**Links:**\n- [ArXiv Page]({paper_info.get('arxiv_url', '')})\n"
            formatted_text += f"- [PDF Download]({paper_info.get('pdf_link', '')})\n"
            if paper_info.get('comment'):
                formatted_text += f"\n**Comments:** {paper_info['comment']}\n"
            if paper_info.get('journal_ref'):
                formatted_text += f"\n**Journal Reference:** {paper_info['journal_ref']}\n"
            if paper_info.get('doi'):
                formatted_text += f"\n**DOI:** {paper_info['doi']}\n"
            return formatted_text
        except Exception as e:
            return f"Failed to format paper info: {e}"