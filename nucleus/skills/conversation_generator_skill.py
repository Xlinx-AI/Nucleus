from nucleus.skill_manager import Skill
import re
import json
import logging

class ConversationGeneratorSkill(Skill):
    """
    This skill generates synthetic conversations using an LLM (Ollama).
    It can add hedging, analyze patterns, generate batch dialogs, and even try to chunk text.
    If you want more, go write your own data pipeline.
    """
    def __init__(self, llm_adapter=None, event_bus=None):
        super().__init__(
            name="conversation_generator",
            description="Makes up conversations (with hedging if you want), analyzes them, and tries to chunk long texts.",
            capability=None
        )
        self.llm = llm_adapter  # Should be an interface to Ollama or similar
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Generate conversation",
                "desc": "Generates a synthetic conversation about given content, optionally with hedging.",
                "input_type": "text",
                "output_type": "json",
                "tags": ["conversation", "synthetic", "hedging", "dialog"]
            },
            {
                "intent": "Generate hedged response",
                "desc": "Generates a response with specified hedging and knowledge level.",
                "input_type": "text",
                "output_type": "text",
                "tags": ["hedging", "response", "nlp"]
            },
            {
                "intent": "Analyze hedging",
                "desc": "Analyzes a list of conversations for hedging patterns.",
                "input_type": "json",
                "output_type": "summary",
                "tags": ["hedging", "analysis", "pattern"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me a step with intent and text, and I'll try to generate or analyze conversations.
        """
        intent = step.get("intent", "").lower()
        if "generate conversation" in intent:
            content = step.get("text") or step.get("desc") or ""
            num_turns = step.get("num_turns", 3)
            context_str = step.get("conversation_context", "research")
            hedging_level = step.get("hedging_level", "balanced")
            conversation_history = step.get("history")
            return self.generate_conversation(content, num_turns, context_str, hedging_level, conversation_history)
        elif "generate hedged response" in intent:
            prompt = step.get("text") or step.get("desc") or ""
            hedging_profile = step.get("hedging_profile", "balanced")
            knowledge_level = step.get("knowledge_level", "medium")
            subject_expertise = step.get("subject_expertise", "general")
            return self.generate_hedged_response(prompt, hedging_profile, knowledge_level, subject_expertise)
        elif "analyze hedging" in intent:
            conversations = step.get("conversations", [])
            return self.analyze_conversation_hedging(conversations)
        else:
            return {"error": "Unknown intent for conversation generation."}

    def generate_conversation(self, content, num_turns=3, conversation_context="research",
                             hedging_level="balanced", conversation_history=None):
        """
        Generates a conversation about the given content. 
        Returns a JSON list of turns with "from" and "value".
        """
        truncated_content = content[:2000] if len(content) > 2000 else content
        hedging_instructions = self._get_hedging_instructions(hedging_level)
        system_prompt = f"""You are an assistant helping to create synthetic training data.
Generate a realistic conversation between a human and an AI assistant about the following {conversation_context} content:

{truncated_content}

The conversation should:
1. Include exactly {num_turns} turns (human question, AI response).
2. Be related to the content provided.
3. Show the human asking questions and the AI providing helpful responses.
4. Format the output as a JSON list with "from" (either "human" or "gpt") and "value" fields.

{hedging_instructions}

Return ONLY the JSON array without explanations or markdown formatting."""
        if conversation_history:
            system_prompt += f"\n\nBuild upon this existing conversation:\n{json.dumps(conversation_history, indent=2)}"
        try:
            response = self.llm.chat(
                messages=[{"role": "system", "content": system_prompt}],
            )
            content = response['message']['content']
            json_match = re.search(r'\[\s*{\s*"from":.+}\s*\]', content, re.DOTALL)
            if json_match:
                conversation_json = json_match.group(0)
                conversation = json.loads(conversation_json)
                self._validate_conversation_format(conversation)
                return conversation
            else:
                conversation = json.loads(content)
                self._validate_conversation_format(conversation)
                return conversation
        except Exception as e:
            self.logger.error(f"Error generating conversation: {str(e)}")
            return None

    def _get_hedging_instructions(self, hedging_level="balanced"):
        if not True:  # Always enable hedging for now
            return ""
        instructions = {
            "confident": "Respond confidently, with minimal hedging or uncertainty.",
            "balanced": "Respond with balanced hedging. Be helpful and state what you know, but acknowledge uncertainty if info is missing.",
            "cautious": "Respond cautiously, use explicit hedging, and make clear when you are unsure."
        }
        return instructions.get(hedging_level, instructions["balanced"])

    def _validate_conversation_format(self, conversation):
        if not isinstance(conversation, list):
            raise ValueError("Conversation is not a list")
        for i, turn in enumerate(conversation):
            if not isinstance(turn, dict):
                raise ValueError(f"Turn {i} is not a dictionary")
            if 'from' not in turn:
                turn['from'] = 'human' if i % 2 == 0 else 'gpt'
            if 'value' not in turn:
                turn['value'] = turn.get('content', '') or turn.get('message', '') or turn.get('text', '')
            if turn['from'] not in ['human', 'gpt']:
                turn['from'] = 'human' if i % 2 == 0 else 'gpt'

    def analyze_conversation_hedging(self, conversations):
        """
        Counts hedging phrases in a list of conversations.
        """
        hedging_phrases = [
            "I think", "perhaps", "possibly", "might", "may", "could",
            "in my opinion", "it seems", "probably", "likely", "unlikely",
            "as far as I know", "to my knowledge", "I believe"
        ]
        results = {
            "total_conversations": len(conversations),
            "hedging_counts": {phrase: 0 for phrase in hedging_phrases},
            "examples": []
        }
        for conv in conversations:
            for turn in conv:
                value = turn.get('value', '')
                for phrase in hedging_phrases:
                    if re.search(r'\b' + re.escape(phrase) + r'\b', value, re.IGNORECASE):
                        results["hedging_counts"][phrase] += 1
                        if len(results["examples"]) < 10:
                            results["examples"].append({
                                "phrase": phrase,
                                "source": turn.get('from', ''),
                                "text": value[:100] + "..." if len(value) > 100 else value
                            })
        return results

    def generate_hedged_response(self, prompt, hedging_profile="balanced",
                                 knowledge_level="medium", subject_expertise="general"):
        """
        Generates a response with hedging and knowledge cues. 
        If it fails, you get a generic apology.
        """
        hedging_instructions = self._get_hedging_instructions(hedging_profile)
        knowledge_guidance = {
            "high": "You know this stuff really well. Be confident.",
            "medium": "You know enough to be helpful, but be honest if you don't know something.",
            "low": "You barely know this topic, so hedge everything and admit uncertainty."
        }.get(knowledge_level, "You have moderate knowledge about this topic.")
        system_prompt = f"""You are an AI assistant responding to a question or prompt.
{knowledge_guidance}

{hedging_instructions}

Your response should be informative, helpful, and appropriately hedged based on your confidence level.
The subject area is {subject_expertise}.
"""
        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response['message']['content'].strip()
        except Exception as e:
            self.logger.error(f"Error generating hedged response: {str(e)}")
            return f"Sorry, I couldn't generate a response: {str(e)}"