"""
Chunking and ingestion configuration models.
This rewrite by a Russian junior who just wants his pipeline to not crash at 4am. If it does, I'm blaming the dependencies.
"""

from pydantic import BaseModel, model_validator
from typing import List, Literal, Optional, Union
from tokenizers import Tokenizer
import pathlib

class Chunking(BaseModel):
    """
    # Configuration for text chunking. If you don't set the params, I'll try to guess them for you.
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
        # If you forgot the model for "slumber", I'll just use something random and hope for the best.
        if self.chunker == "slumber" and not self.gemini_model:
            self.gemini_model = "gemini-2.0-flash"
        return self

class CodeFiles(BaseModel):
    """
    # Checks that all the code files actually exist. Because nothing hurts more than debugging a missing file error at 2am.
    """
    files: List[str]

    @model_validator(mode="after")
    def ensure_files_exist(self) -> "CodeFiles":
        existing = [f for f in self.files if pathlib.Path(f).is_file()]
        if not existing:
            raise ValueError("No valid files found in the provided list. Seriously?")
        self.files = existing
        return self

class CodeChunking(BaseModel):
    """
    # Configuration for code chunking. If it's not perfect, well, at least I tried.
    """
    language: str
    return_type: Literal["chunks", "texts"] = "chunks"
    tokenizer: str = "gpt2"
    chunk_size: int = 512
    include_nodes: bool = False

    @model_validator(mode="after")
    def build_chunker(self) -> "CodeChunking":
        # I'm not even sure if this tokenizer is always available.
        self.tokenizer_obj = Tokenizer.from_pretrained(self.tokenizer)
        # Actual chunker instantiation? Not my problem, that's for the pipeline.
        return self

class IngestionInput(BaseModel):
    """
    # Validates and prepares ingestion configuration. If you pass garbage, I'll try to catch it before something explodes.
    """
    files_or_dir: Union[str, List[str]]
    chunking: Chunking
    tokenizer: Optional[str] = None
    embedding_model: str

    @model_validator(mode="after")
    def prepare(self) -> "IngestionInput":
        # If you pass a path that doesn't exist, don't blame me when it fails.
        if isinstance(self.files_or_dir, str):
            if not pathlib.Path(self.files_or_dir).exists():
                raise ValueError("Provided path does not exist. Go check your typing.")
        elif isinstance(self.files_or_dir, list):
            if not self.files_or_dir or not all(pathlib.Path(f).exists() for f in self.files_or_dir):
                raise ValueError("No valid input files provided. It's not my fault.")
        return self