from nucleus.skill_manager import Skill

class IngestAnythingSkill(Skill):
    """
    This skill ingests documents or code, chunks, embeds, and indexes them for semantic search.
    Powered by LlamaIndex, chunking, and vector stores. If you want one pipeline for all — this is it.
    """
    def __init__(self, event_bus=None):
        super().__init__(
            name="ingest_anything",
            description="Ingests documents or code, chunks, embeds, indexes into vector store.",
            capability=None
        )
        self.event_bus = event_bus

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Ingest documents",
                "desc": "Ingests files/dirs, chunks and indexes for semantic search.",
                "input_type": "file",
                "output_type": "vector_index",
                "tags": ["ingest", "document", "vector"]
            },
            {
                "intent": "Ingest code",
                "desc": "Ingests code files, chunks and indexes for semantic search.",
                "input_type": "file",
                "output_type": "vector_index",
                "tags": ["ingest", "code", "vector"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me intent ("Ingest documents" or "Ingest code") and config, I'll run the pipeline.
        """
        intent = step.get("intent", "").lower()
        if "document" in intent:
            return self.ingest_documents(**step)
        elif "code" in intent:
            return self.ingest_code(**step)
        else:
            return {"error": "Unknown ingest intent."}

    def ingest_documents(self, files_or_dir, embedding_model, chunker, tokenizer=None, chunk_size=None, chunk_overlap=None,
                        similarity_threshold=None, min_characters_per_chunk=None, min_sentences=None, gemini_model=None):
        # Stub: plug in LlamaIndex and your vector store here
        return {"message": "Document ingestion pipeline would run here."}

    def ingest_code(self, files, embedding_model, language, return_type=None, tokenizer=None, chunk_size=None, include_nodes=None):
        # Stub: plug in LlamaIndex and your vector store here
        return {"message": "Code ingestion pipeline would run here."}