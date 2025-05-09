from nucleus.skill_manager import Skill
import csv
import json

class DataAnalyzerSkill(Skill):
    """
    This skill analyzes CSV and JSON files. 
    It reads, counts, summarizes, and sometimes just throws an error if the file is a mess.
    """
    def __init__(self, event_bus=None):
        super().__init__(
            name="data_analyzer",
            description="Analyzes CSV and JSON files, spits out stats or errors.",
            capability=None
        )
        self.event_bus = event_bus

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Analyze CSV",
                "desc": "Analyze a CSV file: stats, aggregation, filtering.",
                "input_type": "csv",
                "output_type": "json, summary",
                "tags": ["csv", "analyze", "stats", "data", "aggregate"]
            },
            {
                "intent": "Analyze JSON",
                "desc": "Analyze JSON data: search, filtering, stats.",
                "input_type": "json",
                "output_type": "summary",
                "tags": ["json", "analyze", "stats", "data"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me a step with a file, and I'll try to summarize it.
        If it fails, you get an error and my sympathy.
        """
        intent = step.get("intent", "").lower()
        file_path = step.get("filepath") or step.get("input") or step.get("desc", "")
        if "csv" in intent:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                summary = {
                    "rows": len(rows),
                    "fields": reader.fieldnames,
                    "samples": rows[:3]
                }
                return {"type": "summary", "summary": summary}
            except Exception as e:
                return {"type": "error", "msg": f"CSV fail: {e}"}
        elif "json" in intent:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                summary = {
                    "type": type(data).__name__,
                    "keys": list(data.keys()) if isinstance(data, dict) else None,
                    "length": len(data) if hasattr(data, "__len__") else None,
                }
                return {"type": "summary", "summary": summary}
            except Exception as e:
                return {"type": "error", "msg": f"JSON fail: {e}"}
        else:
            return {"type": "error", "msg": "No clue what data analysis action you wanted."}