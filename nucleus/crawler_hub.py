
from typing import Any, Dict, List, Optional

from abc import ABC, abstractmethod

class BaseCrawler(ABC):
    """
    Base class for all crawlers in the CrawlerHub.
    """
    def __init__(self, name: str, description: str, capability: Dict[str, Any]):
        self.name = name
        self.description = description
        self.capability = capability

    @abstractmethod
    async def crawl_async(self, target: str, params: Optional[Dict] = None) -> Dict:
        """
        Asynchronous method to crawl the specified target.
        Should be implemented by subclasses.
        """
        ...

class WebCrawler(BaseCrawler):
    """
    Example implementation of a simple web crawler (mock).
    """
    def __init__(self):
        super().__init__(
            name="web_crawler",
            description="Crawls web pages and extracts content.",
            capability={"type": "web"}
        )

    async def crawl_async(self, target: str, params: Optional[Dict] = None) -> Dict:
        # Replace with real HTTP request/parse logic
        return {"url": target, "content": f"Fetched content from {target}"}

class GithubCrawler(BaseCrawler):
    """
    Example implementation of a simple GitHub crawler (mock).
    """
    def __init__(self):
        super().__init__(
            name="github_crawler",
            description="Crawls GitHub repositories.",
            capability={"type": "github"}
        )

    async def crawl_async(self, target: str, params: Optional[Dict] = None) -> Dict:
        # Replace with real GitHub API logic
        return {"repo": target, "content": f"Fetched repo data from {target}"}

class ArxivCrawler(BaseCrawler):
    """
    Example implementation of a simple Arxiv crawler (mock).
    """
    def __init__(self):
        super().__init__(
            name="arxiv_crawler",
            description="Crawls Arxiv articles.",
            capability={"type": "arxiv"}
        )

    async def crawl_async(self, target: str, params: Optional[Dict] = None) -> Dict:
        # Replace with real Arxiv API logic
        return {"arxiv_id": target, "content": f"Fetched arXiv article {target}"}

class CrawlerHub:
    """
    Central hub for managing and dispatching crawlers.
    All crawling is performed iteratively through registered crawler classes.
    """
    def __init__(self, history: Optional[List[Dict]] = None):
        self.history = history
        self.crawlers = {
            "web": WebCrawler(),
            "github": GithubCrawler(),
            "arxiv": ArxivCrawler()
        }

    async def crawl(self, crawler_type: str, target: str, params: Optional[Dict] = None) -> Any:
        """
        Dispatch the crawl request to the appropriate crawler and return the result.
        """
        crawler = self.crawlers.get(crawler_type)
        if not crawler:
            if self.history is not None:
                self.history.append({
                    "role": "crawler",
                    "content": f"No crawler found for type: {crawler_type}",
                    "meta": {},
                    "type": "error"
                })
            return None
        try:
            result = await crawler.crawl_async(target, params)
            if self.history is not None:
                self.history.append({
                    "role": "crawler",
                    "content": f"Crawled {crawler_type} target={target}",
                    "meta": {},
                    "type": "crawl"
                })
            return result
        except Exception as exc:
            if self.history is not None:
                self.history.append({
                    "role": "crawler",
                    "content": f"Crawl error ({crawler_type}): {exc}",
                    "meta": {},
                    "type": "error"
                })
            return None