from nucleus.skill_manager import Skill

class EchoSkill(Skill):
    """
    EchoSkill returns the input text as the output.
    This is for testing skills, DI, and async execution.
    """
    def __init__(self):
        super().__init__(
            name="echo",
            description="Echoes the input text.",
            capability={"intent": "echo", "input_type": "text", "output_type": "text", "tags": ["echo", "test"]}
        )

    async def execute_async(self, step, context):
        return f"Echo: {step.get('description', '')}"