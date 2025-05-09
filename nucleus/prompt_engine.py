
from typing import Dict, Any

class PromptEngine:
    """
    Builds and parses prompts for LLMs. Uses curly braces, not black magic.
    """
    def __init__(self, templates: Dict[str, str] = None):
        self.templates = templates or {}

    def add_template(self, name: str, template: str):
        """
        Registers a new prompt template.
        """
        self.templates[name] = template

    def build(self, name: str, variables: Dict[str, Any]) -> str:
        """
        Builds a prompt from a template and variables. If something's missing, just leaves a blank.
        """
        template = self.templates.get(name, "")
        try:
            return template.format(**variables)
        except KeyError as e:
            print(f"Warning: Missing variable {e} in prompt '{name}'")
            return template

    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        Tries to parse LLM response into a dict. If can't, just wraps as text.
        """
        import json
        try:
            return json.loads(response)
        except Exception:
            return {"text": response}