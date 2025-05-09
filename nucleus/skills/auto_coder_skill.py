from nucleus.skill_manager import Skill

class AutoCoderSkill(Skill):
    """
    This skill is a multi-agent code generation orchestrator.
    It spawns a code generation agent, a code improvement agent, an alignment agent, and a guard agent.
    If you want to generate, improve, merge, and validate code in one go, this is the tired junior's dream.
    """
    def __init__(self, llm_adapter=None, event_bus=None):
        super().__init__(
            name="auto_coder",
            description="Orchestrates code generation, improvement, merge, and guard checks using multiple agents.",
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
                "desc": "Generates code for a task from scratch.",
                "input_type": "desc",
                "output_type": "code",
                "tags": ["code", "generate", "multi-agent"]
            },
            {
                "intent": "Improve code",
                "desc": "Improves or refactors existing code.",
                "input_type": "code",
                "output_type": "code",
                "tags": ["code", "improve", "refactor"]
            },
            {
                "intent": "Merge code",
                "desc": "Merges code intelligently, resolves conflicts and aligns with project goals.",
                "input_type": "code",
                "output_type": "code",
                "tags": ["merge", "intelligent", "align"]
            },
            {
                "intent": "Guard code",
                "desc": "Validates code for security and alignment with directives.",
                "input_type": "code",
                "output_type": "bool",
                "tags": ["guard", "validate", "security"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me a step with intent and code/desc, and I'll try to orchestrate the agents.
        """
        intent = step.get("intent", "").lower()
        if "generate" in intent:
            desc = step.get("desc", "")
            return self._generate_code(desc)
        elif "improve" in intent:
            code = step.get("code", "")
            return self._improve_code(code)
        elif "merge" in intent:
            original = step.get("original", "")
            new_code = step.get("new_code", "")
            return self._merge_code(original, new_code)
        elif "guard" in intent:
            code = step.get("code", "")
            return self._guard_code(code)
        else:
            return {"error": "Unknown auto coder intent."}

    def _generate_code(self, desc):
        if not self.llm:
            return {"error": "No LLM adapter available."}
        prompt = f"Write code from scratch for this task:\n{desc}"
        return {"code": self.llm.completion("code_gen", task_desc=prompt)}

    def _improve_code(self, code):
        if not self.llm:
            return {"error": "No LLM adapter available."}
        prompt = f"Improve this code:\n{code}"
        return {"code": self.llm.completion("code_improve", task_desc=prompt)}

    def _merge_code(self, original, new_code):
        if not self.llm:
            return {"error": "No LLM adapter available."}
        prompt = f"Merge the following code changes intelligently:\nOriginal:\n{original}\nNew:\n{new_code}"
        return {"code": self.llm.completion("code_merge", task_desc=prompt)}

    def _guard_code(self, code):
        if not self.llm:
            return {"error": "No LLM adapter available."}
        prompt = f"Check this code for malicious or unsafe content:\n{code}"
        result = self.llm.completion("code_guard", task_desc=prompt)
        return {"is_safe": "unsafe" not in result.lower()}