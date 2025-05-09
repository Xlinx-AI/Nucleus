
"""
Ingestion engine: chunking, embedding, and universal data/code ingestion pipeline.
Author: 
"""

import uuid
from typing import Any, Callable, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, model_validator
from tokenizers import Tokenizer
import pathlib

# --- Embedding Engines ---

class EmbeddingEngine:
    """
    Simple embedding engine that just hashes text for embeddings. For real work, use something smarter.
    """
    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name

    def embed(self, text: str) -> List[float]:
        h = hash(text)
        return [(h % 1000) / 1000.0 for _ in range(384)]

# Optional: ChonkieAutoEmbedding (adapter for Chonkie AutoEmbeddings)
try:
    from llama_index.core.base.embeddings.base import BaseEmbedding

    class ChonkieAutoEmbedding(BaseEmbedding):
        """
        Adapter for Chonkie AutoEmbeddings (real embeddings, not just hashes).
        """
        model_name: str
        embedder: Optional[object] = None

        def __init__(self, model_name: str):
            super().__init__(model_name=model_name)
            from chonkie import AutoEmbeddings
            self.embedder = AutoEmbeddings.get_embeddings(model_name)

        @classmethod
        def class_name(cls) -> str:
            return "ChonkieAutoEmbedding"

        def _get_embedding(self, text: str) -> List[float]:
            return self.embedder.embed(text).tolist()

        async def _aget_embedding(self, text: str) -> List[float]:
            return self._get_embedding(text)

        def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
            return [e.tolist() for e in self.embedder.embed_batch(texts)]

        async def _aget_embeddings(self, texts: List[str]) -> List[List[float]]:
            return self._get_embeddings(texts)

        def _get_query_embedding(self, query: str) -> List[float]:
            return self._get_embedding(query)

        async def _aget_query_embedding(self, query: str) -> List[float]:
            return await self._aget_embedding(query)

        def _get_text_embedding(self, text: str) -> List[float]:
            return self._get_embedding(text)
except ImportError:
    pass

# --- Chunking/Config Models (from ingest_types) ---

class Chunking(BaseModel):
    """
    Configuration for text chunking.
    """
    chunker: Literal["token", "sentence", "semantic", "sdpm", "late", "slumber", "neural"]
    chunk_size: int = 512
    chunk_overlap: int = 128
    similarity_threshold: float = 0.7
    min_characters_per_chunk: int = 24
    min_sentences: int = 1
    gemini_model: Optional[str] = None

    @model_validator(mode="after")
    def fill_defaults(self) -> "Chunking":
        if self.chunker == "slumber" and not self.gemini_model:
            self.gemini_model = "gemini-2.0-flash"
        return self

class CodeFiles(BaseModel):
    """
    Validates code file paths.
    """
    files: List[str]

    @model_validator(mode="after")
    def ensure_files_exist(self) -> "CodeFiles":
        existing = [f for f in self.files if pathlib.Path(f).is_file()]
        if not existing:
            raise ValueError("No valid files found in the provided list.")
        self.files = existing
        return self

class CodeChunking(BaseModel):
    """
    Configuration for code chunking.
    """
    language: str
    return_type: Literal["chunks", "texts"] = "chunks"
    tokenizer: str = "gpt2"
    chunk_size: int = 512
    include_nodes: bool = False

    @model_validator(mode="after")
    def build_chunker(self) -> "CodeChunking":
        self.tokenizer_obj = Tokenizer.from_pretrained(self.tokenizer)
        return self

class IngestionInput(BaseModel):
    """
    Validates and prepares ingestion configuration.
    """
    files_or_dir: Union[str, List[str]]
    chunking: Chunking
    tokenizer: Optional[str] = None
    embedding_model: str

    @model_validator(mode="after")
    def prepare(self) -> "IngestionInput":
        if isinstance(self.files_or_dir, str):
            if not pathlib.Path(self.files_or_dir).exists():
                raise ValueError("Provided path does not exist.")
        elif isinstance(self.files_or_dir, list):
            if not self.files_or_dir or not all(pathlib.Path(f).exists() for f in self.files_or_dir):
                raise ValueError("No valid input files provided.")
        return self

# --- Main Engine ---

class IngestionEngine:
    """
    Ingestion engine: supports chunking, embedding, and universal data/code ingestion pipeline.
    """
    def __init__(self, embedding_engine: EmbeddingEngine = None):
        self.embedding_engine = embedding_engine or EmbeddingEngine()

    def chunk(self, input_data: Union[str, List[str]], config: Chunking = None) -> List[str]:
        if config is None:
            config = Chunking(chunker="sentence")
        config.fill_defaults()
        if isinstance(input_data, str):
            data = [input_data]
        else:
            data = input_data
        chunks = []
        for text in data:
            if config.chunker == "sentence":
                sents = text.split(". ")
                for i in range(0, len(sents), config.chunk_size):
                    chunk = ". ".join(sents[i:i+config.chunk_size])
                    if chunk:
                        chunks.append(chunk)
            elif config.chunker == "token":
                tokens = text.split()
                for i in range(0, len(tokens), config.chunk_size):
                    chunk = " ".join(tokens[i:i+config.chunk_size])
                    if chunk:
                        chunks.append(chunk)
            else:
                # Just split by chars. It's late, don't judge me.
                for i in range(0, len(text), config.chunk_size):
                    chunk = text[i:i+config.chunk_size]
                    if chunk:
                        chunks.append(chunk)
        return chunks

    def ingest(self, chunks: List[str], embedding_fn: Optional[Callable[[str], List[float]]] = None) -> List[Dict]:
        results = []
        for chunk in chunks:
            emb = embedding_fn(chunk) if embedding_fn else self.embedding_engine.embed(chunk)
            results.append({
                "id": str(uuid.uuid4()),
                "chunk": chunk,
                "embedding": emb
            })
        return results

    def ingest_anything(self, files_or_dir, embedding_model, chunker, tokenizer=None, chunk_size=None, chunk_overlap=None,
                       similarity_threshold=None, min_characters_per_chunk=None, min_sentences=None, gemini_model=None,
                       reader_cls=None, directory_reader_cls=None, text_node_cls=None, storage_ctx_cls=None,
                       vector_index_cls=None, embedding_cls=None):
        """
        Universal ingestion entrypoint for anything. If it crashes, it's probably 4am.
        """
        chunking = Chunking(
            chunker=chunker,
            chunk_size=chunk_size or 512,
            chunk_overlap=chunk_overlap or 128,
            similarity_threshold=similarity_threshold or 0.7,
            min_characters_per_chunk=min_characters_per_chunk or 24,
            min_sentences=min_sentences or 1,
            gemini_model=gemini_model,
        )
        ingestion_input = IngestionInput(
            files_or_dir=files_or_dir,
            chunking=chunking,
            tokenizer=tokenizer,
            embedding_model=embedding_model,
        )
        reader = reader_cls() if reader_cls else None
        DirectoryReader = directory_reader_cls
        TextNode = text_node_cls
        StorageContext = storage_ctx_cls
        VectorStoreIndex = vector_index_cls
        Embedding = embedding_cls

        docs = DirectoryReader(
            input_files=ingestion_input.files_or_dir,
            file_extractor={".pdf": reader},
        ).load_data()
        text = "\n\n---\n\n".join([d.text for d in docs])
        chunks = ingestion_input.chunking.chunk(text)
        nodes = [TextNode(text=c.text, id_=str(uuid.uuid4())) for c in chunks]
        storage_context = StorageContext.from_defaults(vector_store=self.embedding_engine)
        index = VectorStoreIndex(
            nodes=nodes,
            embed_model=Embedding(model_name=embedding_model),
            show_progress=True,
            storage_context=storage_context,
        )
        return index

    def ingest_code(self, files, embedding_model, language, return_type=None, tokenizer=None, chunk_size=None, include_nodes=None,
                   directory_reader_cls=None, text_node_cls=None, storage_ctx_cls=None, vector_index_cls=None, embedding_cls=None):
        """
        Universal ingestion for code files. If you see this in logs, I'm probably debugging something at night.
        """
        code_files = CodeFiles(files=files)
        chunking = CodeChunking(
            language=language,
            return_type=return_type or "chunks",
            tokenizer=tokenizer or "gpt2",
            chunk_size=chunk_size or 512,
            include_nodes=include_nodes if include_nodes is not None else False,
        )
        DirectoryReader = directory_reader_cls
        TextNode = text_node_cls
        StorageContext = storage_ctx_cls
        VectorStoreIndex = vector_index_cls
        Embedding = embedding_cls

        docs = DirectoryReader(input_files=code_files.files).load_data()
        text = "\n\n---\n\n".join([d.text for d in docs])
        chunks = chunking.chunker.chunk(text)
        nodes = [TextNode(text=c.text, id_=str(uuid.uuid4())) for c in chunks]
        storage_context = StorageContext.from_defaults(vector_store=self.embedding_engine)
        index = VectorStoreIndex(
            nodes=nodes,
            embed_model=Embedding(model_name=embedding_model),
            show_progress=True,
            storage_context=storage_context,
        )
        return index