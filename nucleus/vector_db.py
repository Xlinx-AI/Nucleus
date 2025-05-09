
from typing import Dict, List

class VectorDatabase:
    """
    Stores embeddings and supports iterative search for nearest vectors.
    """
    def __init__(self, backend: str = "mock", **kwargs):
        self.backend = backend
        self.vectors: Dict[str, Dict] = {}

    def store_vectors(self, vectors: List[Dict]):
        """
        Store embeddings in the vector database.
        """
        for v in vectors:
            self.vectors[v["id"]] = v

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """
        Return the top_k vectors from the database (mock implementation).
        """
        # Real implementation: calculate similarity, sort, and return top_k
        return list(self.vectors.values())[:top_k]