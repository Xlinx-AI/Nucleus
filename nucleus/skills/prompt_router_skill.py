from nucleus.skill_manager import Skill

class PromptRouterSkill(Skill):
    """
    This skill is a tired junior's dream: it takes any user prompt, 
    tries to use an LLM to figure out what agent/trigger to call, 
    and, if the LLM is missing, falls back to a dumb reasoning agent.
    If you want a guarantee, look elsewhere.
    """
    def __init__(self, llm_adapter=None, event_bus=None):
        super().__init__(
            name="prompt_router",
            description="Routes arbitrary user prompts to the right agent type using LLM or fallback.",
            capability={
                "intent": "routing",
                "input_type": "text",
                "output_type": "text",
                "tags": ["router", "llm", "reasoning"]
            }
        )
        self.llm = llm_adapter
        self.event_bus = event_bus

    def set_event_bus(self, bus):
        self.event_bus = bus

    async def handle_async(self, task, task_id=None):
        """
        LLM-powered router. If you gave it an LLM, it tries to be smart.
        If not, it just makes up an answer and hopes for the best.
        """
        if self.llm:
            import asyncio
            user_text = ""
            if isinstance(task, dict):
                user_text = task.get("desc", "") or task.get("task", "")
            else:
                user_text = str(task)
            prompt = (
                "You are an AI command router for a multi-agent system. "
                "Your input is a user request in ANY language. "
                "Your task: decide which agent type (from the list) should handle this request, and output a command in the format: <trigger> <command_in_english>.\n"
                "Available agent types (triggers): researcher, internet, web_search, browser, coder, file, shell, communicator, planner, pollinations, system, mcp_client, summary, pdf, table, email, deploy, expose.\n"
                "Examples:\n"
                "- 'Summarize geopolitical news' → 'researcher summarize geopolitical news'\n"
                "- 'Find news about AI' → 'web_search news about AI'\n"
                "- 'Generate a cat image' → 'pollinations draw a cat'\n"
                "- 'Run command ls' → 'shell ls'\n"
                "- 'Open website example.com' → 'browser open website example.com'\n"
                "- 'Read file readme.txt' → 'file read file readme.txt'\n"
                "- 'Send an email campaign' → 'email send campaign'\n"
                "Always use only one of the known triggers. Do not add explanations, only the command! "
                "Respond ONLY in English, use the trigger and command in English, regardless of the input language."
            )
            prompt = f"{prompt}\n\nUser request: {user_text}\n\nResponse:"
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.llm.completion("rephrase", task=prompt)
                )
                return str(result).strip()
            except Exception:
                # When everything else fails, just send to pollinations like a true survivor.
                return f"pollinations {user_text}"
        else:
            # No LLM? No problem. We'll just chain some fake reasoning.
            try:
                from nucleus.skills.orchestrator_agent import OrchestratorAgent
            except ImportError:
                # If you don't have orchestrator_agent, you get a default answer.
                return {"final_answer": "[Router reasoning fallback] " + str(task)}
            def fake_llm(prompt):
                return {"final_answer": "[Router reasoning] " + str(task)}
            agent = OrchestratorAgent(fake_llm)
            result = await agent.run(str(task))
            return result