"""
Universal embedding model adapter for text and code chunks.
Author:  Kirill — but now it's late and coffee is almost gone.
"""

from typing import List, Optional

# This import is only here because llama_index wants it. Don't ask.
from llama_index.core.base.embeddings.base import BaseEmbedding

class ChonkieAutoEmbedding(BaseEmbedding):
    """
    # This is the adapter for Chonkie AutoEmbeddings. Yeah, the name is weird, but it works.
    # I don't even want to think about how many hours I spent on this.
    """

    model_name: str
    embedder: Optional[object] = None

    def __init__(self, model_name: str):
        super().__init__(model_name=model_name)
        # This import is runtime-only. If it crashes, I'm going to bed.
        from chonkie import AutoEmbeddings
        self.embedder = AutoEmbeddings.get_embeddings(model_name)

    @classmethod
    def class_name(cls) -> str:
        # Because sometimes you just need a name, and this one is good enough.
        return "ChonkieAutoEmbedding"

    def _get_embedding(self, text: str) -> List[float]:
        # Just give me the vector, please. No more questions.
        return self.embedder.embed(text).tolist()

    async def _aget_embedding(self, text: str) -> List[float]:
        # Async, but let's be real, it just calls sync. It's too late to care.
        return self._get_embedding(text)

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Batch embedding. Hope you have enough RAM, because I'm not checking.
        return [e.tolist() for e in self.embedder.embed_batch(texts)]

    async def _aget_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Async batch, but again — who needs true async? Not me, not tonight.
        return self._get_embeddings(texts)

    def _get_query_embedding(self, query: str) -> List[float]:
        # Query, text, whatever. Just vectorize it.
        return self._get_embedding(query)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return await self._aget_embedding(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._get_embedding(text)