"""
Unified ingestion pipeline.
Author: Lavrentiev Kirill — but this rewrite is by a slightly sleep-deprived Russian junior, fueled by too much coffee and not enough sleep.
"""

import uuid
from typing import Optional, List, Union, Literal

# NOTE: These are just interfaces. If something explodes, blame the dependency injection.
# At 2am, DI is the only way I can pretend things are "extensible".

class IngestAnything:
    """
    Yeah, this class ingests and indexes documents. You want chunking? You want embeddings? You got it.
    I wish life was this modular.
    """

    def __init__(self, vector_store, reader=None):
        self.vector_store = vector_store
        self.reader = reader

    def ingest(
        self,
        files_or_dir: Union[str, List[str]],
        embedding_model: str,
        chunker: Literal["token", "sentence", "semantic", "sdpm", "late", "neural", "slumber"],
        tokenizer: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        min_characters_per_chunk: Optional[int] = None,
        min_sentences: Optional[int] = None,
        gemini_model: Optional[str] = None,
        reader_cls=None,
        directory_reader_cls=None,
        text_node_cls=None,
        storage_ctx_cls=None,
        vector_index_cls=None,
        embedding_cls=None,
    ):
        """
        Universal ingestion entrypoint. If this function fails, it's probably 4am and I should go to sleep.
        """
        chunking = Chunking(
            chunker=chunker,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            similarity_threshold=similarity_threshold,
            min_characters_per_chunk=min_characters_per_chunk,
            min_sentences=min_sentences,
            gemini_model=gemini_model,
        )
        ingestion_input = IngestionInput(
            files_or_dir=files_or_dir,
            chunking=chunking,
            tokenizer=tokenizer,
            embedding_model=embedding_model,
        )
        reader = self.reader or (reader_cls() if reader_cls else None)
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
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        index = VectorStoreIndex(
            nodes=nodes,
            embed_model=Embedding(model_name=embedding_model),
            show_progress=True,
            storage_context=storage_context,
        )
        return index

class IngestCode:
    """
    This one ingests and indexes code files. It tries to be smart about chunking and language, but, let's be honest, sometimes it just wants to go home.
    """

    def __init__(self, vector_store):
        self.vector_store = vector_store

    def ingest(
        self,
        files: List[str],
        embedding_model: str,
        language: str,
        return_type: Optional[Literal["chunks", "texts"]] = None,
        tokenizer: Optional[str] = None,
        chunk_size: Optional[int] = None,
        include_nodes: Optional[bool] = None,
        directory_reader_cls=None,
        text_node_cls=None,
        storage_ctx_cls=None,
        vector_index_cls=None,
        embedding_cls=None,
    ):
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
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        index = VectorStoreIndex(
            nodes=nodes,
            embed_model=Embedding(model_name=embedding_model),
            show_progress=True,
            storage_context=storage_context,
        )
        return index