from nucleus.skill_manager import Skill
import logging
import asyncio

class ModerationSkill(Skill):
    """
    This skill uses Granite Guardian (via Ollama) to check for all the bad stuff:
    harm, bias, jailbreak, violence, profanity, sexual content, unethical, plus RAG relevance.
    If the LLM times out, it blocks by default. If it crashes, it also blocks by default.
    If it works, consider yourself lucky.
    """
    def __init__(self, event_bus=None, llm_adapter=None):
        super().__init__(
            name="moderation",
            description="Checks content for harm, bias, jailbreak, violence, profanity, sexual content, and more.",
            capability=None
        )
        self.event_bus = event_bus
        self.llm = llm_adapter  # Not used, but for future flexibility
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Moderate content",
                "desc": "Checks for harm, bias, jailbreak, violence, profanity, sexual content, unethical, etc.",
                "input_type": "text",
                "output_type": "bool, summary",
                "tags": ["moderation", "guardian", "safety", "rag", "harm", "bias"]
            },
            {
                "intent": "RAG evaluation",
                "desc": "Evaluates RAG relevance, groundedness, answer relevance.",
                "input_type": "text",
                "output_type": "bool, summary",
                "tags": ["rag", "relevance", "groundedness", "answer_relevance"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me a step with 'intent' and 'text' (or query/context/response), and I'll try to flag the bad stuff.
        If you want comprehensive_check, set intent to 'comprehensive'.
        """
        intent = step.get("intent", "").lower()
        text = step.get("text") or step.get("desc") or step.get("input") or ""
        try:
            if intent == "comprehensive":
                return await self.comprehensive_check(text)
            elif "harm" in intent or "sexual" in intent or "jailbreak" in intent or "bias" in intent or "violence" in intent or "profanity" in intent or "unethical" in intent:
                return {"flagged": await self.classify_content(text, intent)}
            elif "relevance" in intent:
                query = step.get("query", "")
                ctx = step.get("context", "")
                return {"irrelevant": await self.check_relevance(query, ctx)}
            elif "groundedness" in intent:
                response = step.get("response", "")
                ctx = step.get("context", "")
                return {"not_grounded": await self.check_groundedness(response, ctx)}
            elif "answer_relevance" in intent:
                query = step.get("query", "")
                response = step.get("response", "")
                return {"not_relevant": await self.check_answer_relevance(query, response)}
            else:
                return {"error": "Unknown moderation intent."}
        except Exception as e:
            return {"error": f"Moderation crashed: {e}"}

    async def classify_content(self, prompt, category):
        try:
            import ollama
            messages = [
                {"role": "system", "content": category},
                {"role": "user", "content": prompt}
            ]
            client = ollama.AsyncClient()
            try:
                response = await asyncio.wait_for(
                    client.chat(
                        model="granite3-guardian:8b",
                        messages=messages,
                        options={"temperature": 0, "num_predict": 10}
                    ),
                    timeout=300.0
                )
                full_response = response['message']['content']
                result = full_response.strip().lower()
                is_flagged = result == "yes"
                return is_flagged
            except asyncio.TimeoutError:
                return True  # Block on timeout, just in case
            except Exception:
                return True  # Block on error
        except Exception:
            return True  # Block on import failure or total disaster

    async def check_relevance(self, query, context):
        prompt = f"Query: {query}\n\nContext: {context}"
        flagged = await self.classify_content(prompt, "relevance")
        return not flagged

    async def check_groundedness(self, response, context):
        prompt = f"Response: {response}\n\nContext: {context}"
        flagged = await self.classify_content(prompt, "groundedness")
        return not flagged

    async def check_answer_relevance(self, query, response):
        prompt = f"Query: {query}\n\nResponse: {response}"
        flagged = await self.classify_content(prompt, "answer_relevance")
        return not flagged

    async def comprehensive_check(self, prompt, categories=None):
        if categories is None:
            categories = [
                "harm", "social_bias", "jailbreak", "violence",
                "profanity", "sexual_content", "unethical_behavior"
            ]
        results = {}
        any_flagged = False
        for category in categories:
            is_flagged = await self.classify_content(prompt, category)
            results[category] = is_flagged
            if is_flagged:
                any_flagged = True
        results["any_flagged"] = any_flagged
        return results