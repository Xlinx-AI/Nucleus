
import uuid
from typing import Any, Callable, Dict, List, Optional, Union

class DataPipeline:
    """
    Responsible for chunking input data, transforming it into embeddings, and preparing for vector storage.
    All algorithms are strictly iterative.
    """
    def __init__(self, history: Optional[List[Dict]] = None):
        self.history = history

    def chunk(self, input_data: Union[str, List[str]], strategy: str = "sentence", chunk_size: int = 512, overlap: int = 128, **kwargs) -> List[str]:
        """
        Split input data into chunks using the specified strategy.
        """
        if isinstance(input_data, str):
            data = [input_data]
        else:
            data = input_data
        chunks = []
        for text in data:
            if strategy == "sentence":
                sents = text.split(". ")
                for i in range(0, len(sents), chunk_size):
                    chunk = ". ".join(sents[i:i + chunk_size])
                    if chunk:
                        chunks.append(chunk)
            elif strategy == "token":
                tokens = text.split()
                for i in range(0, len(tokens), chunk_size):
                    chunk = " ".join(tokens[i:i + chunk_size])
                    if chunk:
                        chunks.append(chunk)
            else:
                # Default: split by chunk_size characters
                for i in range(0, len(text), chunk_size):
                    chunk = text[i:i + chunk_size]
                    if chunk:
                        chunks.append(chunk)
        return chunks

    def ingest_chunks(self, chunks: List[str], embedding_fn: Optional[Callable[[str], List[float]]] = None, **kwargs) -> List[Dict]:
        """
        Transform chunks into embeddings and prepare for storage.
        """
        results = []
        for chunk in chunks:
            emb = embedding_fn(chunk) if embedding_fn else self._mock_embedding(chunk)
            results.append({
                "id": str(uuid.uuid4()),
                "chunk": chunk,
                "embedding": emb
            })
            if self.history is not None:
                self.history.append({
                    "role": "ingest",
                    "content": f"Ingested chunk: {chunk[:60]}",
                    "meta": {},
                    "type": "ingest"
                })
        return results

    def _mock_embedding(self, text: str) -> List[float]:
        """
        Generate a pseudo-embedding for demonstration or testing purposes.
        """
        h = hash(text)
        return [(h % 1000) / 1000.0 for _ in range(384)]