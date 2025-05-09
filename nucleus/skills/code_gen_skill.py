from nucleus.skill_manager import Skill

class CodeGenSkill(Skill):
    """
    This skill generates code using an LLM. 
    You give it a description, it tries its best, and if it fails, well, that's life.
    """
    def __init__(self, llm_adapter=None, event_bus=None):
        super().__init__(
            name="code_gen",
            description="Generates code for any programming language, based on a text description.",
            capability=None
        )
        self.llm = llm_adapter
        self.event_bus = event_bus

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Generate code",
                "desc": "Generate code in any programming language from a text description.",
                "input_type": "desc",
                "output_type": "code",
                "tags": ["code", "generation", "programming", "codegen", "python", "js", "java"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me a description and a language, and I'll do my best. 
        If the LLM is missing or tired, you'll get what you get.
        """
        if self.llm:
            desc = step.get('desc') or step.get('input') or ""
            tags = step.get('tags', ["python"])
            lang = tags[0] if tags else "python"
            prompt = f"Generate correct code for this description:\n{desc}\nLanguage: {lang}"
            code = self.llm.completion("skill_generator", task_desc=prompt)
            return {"type": "code", "code": code}
        else:
            # Fallback: no LLM, no code, just an apology.
            return {"type": "error", "msg": "No LLM adapter available for code generation."}