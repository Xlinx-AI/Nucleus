from nucleus.skill_manager import Skill
import logging
import os
import json
import pandas as pd

class DataExpanderSkill(Skill):
    """
    This skill expands conversations by generating paraphrases and variations.
    It can also chunk papers, generate synthetic dialogs, and save them in whatever format you want.
    If you want more, bring more RAM.
    """
    def __init__(self, llm_adapter=None, event_bus=None):
        super().__init__(
            name="data_expander",
            description="Expands conversation datasets by generating paraphrases and new dialogs.",
            capability=None
        )
        self.llm = llm_adapter
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Expand conversations",
                "desc": "Generates paraphrased/varied conversations.",
                "input_type": "json",
                "output_type": "json",
                "tags": ["expand", "paraphrase", "dataset"]
            },
            {
                "intent": "Generate from paper",
                "desc": "Chunks a paper and generates conversations from it.",
                "input_type": "text",
                "output_type": "json",
                "tags": ["generate", "paper", "conversation"]
            },
            {
                "intent": "Convert format",
                "desc": "Converts conversations to jsonl, parquet, csv, or DataFrame.",
                "input_type": "json",
                "output_type": "file",
                "tags": ["convert", "format", "dataset"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me a step with intent and data, and I'll try to expand or convert it.
        """
        intent = step.get("intent", "").lower()
        if "expand" in intent:
            conversations = step.get("conversations", [])
            expansion_factor = step.get("expansion_factor", 3)
            static_fields = step.get("static_fields", {'human': False, 'gpt': False})
            reference_fields = step.get("reference_fields", [])
            return self.expand_conversation_dataset(conversations, expansion_factor, static_fields, reference_fields)
        elif "generate from paper" in intent:
            paper_content = step.get("paper_content", "")
            generator = step.get("conversation_generator")  # Should be an instance of ConversationGeneratorSkill
            num_chunks = step.get("num_chunks", 5)
            num_turns = step.get("num_turns", 3)
            expansion_factor = step.get("expansion_factor", 2)
            static_fields = step.get("static_fields", {'human': False, 'gpt': False})
            reference_fields = step.get("reference_fields", [])
            return self.generate_conversations_from_paper(
                paper_content, generator, num_chunks, num_turns, expansion_factor, static_fields, reference_fields
            )
        elif "convert" in intent:
            conversations = step.get("conversations", [])
            base_filename = step.get("base_filename", "dataset")
            formats = step.get("formats", ['jsonl', 'parquet', 'csv', 'df'])
            return self.convert_to_multi_format(conversations, base_filename, formats)
        else:
            return {"error": "Unknown data expander intent."}

    def expand_conversation_dataset(self, conversations, expansion_factor=3, static_fields=None, reference_fields=None):
        # Identity: возвращает исходные данные без изменений
        return {"expanded_conversations": conversations}

    def generate_conversations_from_paper(self, paper_content, generator, num_chunks=5, num_turns=3, expansion_factor=2, static_fields=None, reference_fields=None):
        """
        Разбивает текст статьи на чанки и генерирует диалоги для каждого чанка.
        generator — объект с методом generate_conversation(chunk, num_turns, expansion_factor, static_fields, reference_fields)
        """
        if not paper_content or not generator:
            return {"error": "Не переданы paper_content или generator"}

        # Простое разбиение по символам
        chunk_size = max(1, len(paper_content) // num_chunks)
        chunks = [paper_content[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks-1)]
        chunks.append(paper_content[(num_chunks-1)*chunk_size:])  # Последний чанк — остаток

        all_conversations = []
        for idx, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            # Предполагаем, что generator имеет метод generate_conversation(...)
            conversations = generator.generate_conversation(
                chunk,
                num_turns=num_turns,
                expansion_factor=expansion_factor,
                static_fields=static_fields,
                reference_fields=reference_fields
            )
            # conversations может быть dict или list
            if isinstance(conversations, dict):
                all_conversations.append(conversations)
            elif isinstance(conversations, list):
                all_conversations.extend(conversations)
            else:
                self.logger.warning(f"generator.generate_conversation вернул неизвестный тип: {type(conversations)}")
        return {"generated_conversations": all_conversations}

    def convert_to_multi_format(self, conversations, base_filename, formats):
        """
        Сохраняет conversations в различные форматы: jsonl, parquet, csv, DataFrame.
        """
        if not conversations:
            return {"error": "Пустой список conversations"}

        results = {}
        os.makedirs("outputs", exist_ok=True)
        df = pd.DataFrame(conversations)

        for fmt in formats:
            fmt = fmt.lower()
            if fmt == "jsonl":
                jsonl_path = os.path.join("outputs", f"{base_filename}.jsonl")
                with open(jsonl_path, "w", encoding="utf-8") as f:
                    for conv in conversations:
                        f.write(json.dumps(conv, ensure_ascii=False) + "\n")
                results["jsonl"] = jsonl_path
            elif fmt == "parquet":
                parquet_path = os.path.join("outputs", f"{base_filename}.parquet")
                df.to_parquet(parquet_path, index=False)
                results["parquet"] = parquet_path
            elif fmt == "csv":
                csv_path = os.path.join("outputs", f"{base_filename}.csv")
                df.to_csv(csv_path, index=False, encoding="utf-8")
                results["csv"] = csv_path
            elif fmt == "df" or fmt == "dataframe":
                results["df"] = df
            else:
                self.logger.warning(f"Неизвестный формат конвертации: {fmt}")

        return results