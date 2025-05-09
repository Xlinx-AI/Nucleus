import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# Импортируем skills и утилиты nucleus
from nucleus.skills.web_crawler_skill import WebCrawlerSkill
from nucleus.skills.arxiv_search_skill import ArxivSearchSkill
from nucleus.skills.duckduckgo_skill import DuckDuckGoSkill
from nucleus.skills.github_crawler_skill import GitHubCrawlerSkill
from nucleus.skills.conversation_generator_skill import ConversationGeneratorSkill
from nucleus.skills.data_expander_skill import DataExpanderSkill
from nucleus.skills.data_cleaner_skill import DataCleanerSkill
from nucleus.utils import OllamaInterface

class ResearchPipeline:
    """
    This is the main orchestration pipeline for topic research, dataset generation, expansion and cleaning.
    It's like a tired junior's dream: you just call run_topic_pipeline, and it does everything (if nothing breaks).
    """
    def __init__(self, data_dir="./data", model_name="llama3"):
        self.data_dir = Path(data_dir)
        self.model_name = model_name
        self.logger = logging.getLogger("ResearchPipeline")
        os.makedirs(self.data_dir, exist_ok=True)
        self.web_crawler = WebCrawlerSkill()
        self.arxiv_searcher = ArxivSearchSkill()
        self.duckduckgo = DuckDuckGoSkill()
        self.github_crawler = GitHubCrawlerSkill()
        self.llm = OllamaInterface(model_name=model_name)
        self.conversation_generator = ConversationGeneratorSkill(llm_adapter=self.llm)
        self.data_expander = DataExpanderSkill(llm_adapter=self.llm)
        self.data_cleaner = DataCleanerSkill(llm_adapter=self.llm)

    async def run_topic_pipeline(self, topic, max_papers=3, max_search=5, expansion_factor=2, clean=True):
        """
        Full async pipeline: search papers, web, github, generate/expand/clean conversations.
        """
        result = {"topic": topic, "papers": [], "search_results": [], "repos": [], "conversations": [], "expanded": [], "cleaned": []}
        # 1. Arxiv поиск
        arxiv_ids = [topic]  # В реале тут был бы генератор запросов
        for arxiv_id in arxiv_ids[:max_papers]:
            paper_info = await self.arxiv_searcher.execute_async({"intent": "Fetch arxiv paper", "arxiv_id": arxiv_id})
            formatted = await self.arxiv_searcher.execute_async({"intent": "Format arxiv paper", "paper_info": paper_info})
            result["papers"].append({"info": paper_info, "formatted": formatted})
        # 2. Web search
        web = await self.duckduckgo.execute_async({"intent": "DuckDuckGo search", "query": topic, "max_results": max_search})
        result["search_results"] = web
        # 3. GitHub search по теме
        try:
            github_repos = await self.github_crawler.execute_async({
                "intent": "GitHub search",
                "query": topic,
                "max_results": max_search
            })
            result["repos"] = github_repos
        except Exception as e:
            self.logger.error(f"GitHub search error: {e}")
            result["repos"] = []
        # 4. Генерация диалогов
        for paper in result["papers"]:
            conversation = self.conversation_generator.generate_conversation(paper["formatted"], num_turns=3)
            if conversation:
                result["conversations"].append(conversation)
        # 5. Расширение датасета
        expanded = self.data_expander.expand_conversation_dataset(result["conversations"], expansion_factor=expansion_factor)
        result["expanded"] = expanded
        # 6. Чистка датасета
        if clean:
            cleaned = self.data_cleaner.clean_dataset(result["conversations"], expanded.get("expanded_conversations", []))
            result["cleaned"] = cleaned
        # 7. Сохраняем результаты
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = self.data_dir / f"research_{topic.replace(' ','_')}_{timestamp}.json"
        try:
            import json
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save pipeline result: {e}")
        return result