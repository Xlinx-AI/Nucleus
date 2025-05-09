
"""
Async/sync utility decorators, singleton/factory patterns, and error handling helpers.

"""

import functools
import asyncio

class PlatformOops(Exception):
    """
    Custom error for platform-specific problems.
    """
    pass

def do_async(func):
    """
    Decorator for running a function in asyncio, even if your head hurts from callbacks.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            print(f"Oops, async error: {e}")
            raise
    return wrapper

def error_summary(error: Exception, verbose: bool = False):
    """
    Returns a string with error details. If verbose, spill it all out.
    """
    if verbose:
        import traceback
        return f"{error}\n{traceback.format_exc()}"
    return str(error)

def error_report(error: Exception, verbose: bool = False):
    """
    Prints error info to the console.
    """
    msg = error_summary(error, verbose)
    print(f"[Error Report]\n{msg}")

def catch_errors(func):
    """
    Decorator to catch and print errors, so things don't crash at 3am.
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            verbose = kwargs.get("verbose", False)
            error_report(e, verbose)
            return None
    return wrapped

def singleton(cls):
    """
    Singleton pattern. Makes sure only one instance exists.
    """
    instances = {}
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    cls.get_instance = staticmethod(get_instance)
    def reset():
        if cls in instances:
            del instances[cls]
    cls.reset_singleton = staticmethod(reset)
    return cls

def factory(cls):
    """
    Factory pattern for making new objects.
    """
    @functools.wraps(cls)
    def create(*args, **kwargs):
        return cls(*args, **kwargs)
    cls.create = staticmethod(create)
    return cls
import json
import time

class ContextHistory:
    """
    Yeah, this is the chat and reasoning history. 
    It stores every message, thought, plan, skill call, and whatever else your tired brain spits out at 3am.
    Each entry is a dict with:
      - role: user/assistant/skill/plan/thought/system
      - type: msg/plan/skill/thought/system
      - content: some text, probably too long
      - timestamp: yeah, unix time, as usual
      - meta: random metadata (dict)
      - parent_id: for keeping track of weird trees, if you feel like it
    """
    def __init__(self, max_length=2000):
        self.history = []
        self.max_length = max_length

    def _truncate_text(self, text, max_length):
        if text is None:
            return ""
        if len(text) > max_length:
            return text[:max_length - 5] + " [...]"
        return text

    def add_message(self, role, content, type="msg", meta=None, parent_id=None):
        entry = {
            "role": role,
            "type": type,
            "content": self._truncate_text(content, self.max_length // 4),
            "timestamp": time.time(),
            "meta": meta or {},
            "parent_id": parent_id,
        }
        self.history.append(entry)
        self._trim()

    def add_plan(self, plan_text, meta=None, parent_id=None):
        # Plans go here, even if they're terrible.
        self.add_message(role="plan", content=plan_text, type="plan", meta=meta, parent_id=parent_id)

    def add_skill_call(self, skill_name, args, result=None, meta=None, parent_id=None):
        # Logs every skill call, with result if you bothered to pass it.
        content = f"Skill call: {skill_name}({args})"
        if result is not None:
            content += f"\nResult: {self._truncate_text(str(result), self.max_length // 4)}"
        self.add_message(role="skill", content=content, type="skill", meta=meta, parent_id=parent_id)

    def add_thought(self, thought, meta=None, parent_id=None):
        # Sometimes you have a thought. Sometimes it's useless. Still logging it.
        self.add_message(role="thought", content=thought, type="thought", meta=meta, parent_id=parent_id)

    def add(self, action, result):
        # Old interface, just dumps action/result as assistant message.
        self.add_message(role="assistant", content=f"Action: {action}\nResult: {result}", type="msg")

    def add_user(self, msg, meta=None, parent_id=None):
        self.add_message(role="user", content=msg, type="msg", meta=meta, parent_id=parent_id)

    def add_assistant(self, msg, meta=None, parent_id=None):
        self.add_message(role="assistant", content=msg, type="msg", meta=meta, parent_id=parent_id)

    def get_history(self, role_filter=None, type_filter=None):
        hist = self.history
        if role_filter:
            hist = [h for h in hist if h["role"] == role_filter]
        if type_filter:
            hist = [h for h in hist if h["type"] == type_filter]
        return hist

    def as_string(self):
        if not self.history:
            return "<No context yet, go do something>"
        lines = []
        for h in self.history:
            role = h["role"]
            content = h["content"]
            t = h["type"]
            lines.append(f"[{role.upper()}|{t}] {content}")
        return "\n---\n".join(lines)

    def _trim(self):
        # Trims history when it gets too long.
        while len(json.dumps(self.history)) > self.max_length and len(self.history) > 1:
            self.history.pop(0)
import logging
from typing import List, Dict, Any

class OllamaInterface:
    """
    This is a tired junior's wrapper for the Ollama API.
    It gives you chat, embeddings, async chat, and availability checks.
    If Ollama is missing, you'll get error messages and a lecture in the logs.
    """
    def __init__(self, model_name="llama3", host="http://localhost:11434"):
        self.model = model_name
        self.host = host
        self.logger = logging.getLogger(__name__)
        try:
            import ollama
            from ollama import Client, AsyncClient, ResponseError
            self.ollama_available = True
            self.client = Client(host=self.host)
            self.async_client = AsyncClient(host=self.host)
            self._Ollama = ollama
            self._ResponseError = ResponseError
        except ImportError:
            self.ollama_available = False
            self.logger.warning("Ollama package not found. Please install with 'pip install ollama'")

    def chat(self, messages: List[Dict[str, str]], stream=False) -> Dict[str, Any]:
        if not self.ollama_available:
            error_msg = "Ollama is not available. Please install with 'pip install ollama'"
            self.logger.error(error_msg)
            return {"error": error_msg, "message": {"content": error_msg}}
        try:
            return self._Ollama.chat(model=self.model, messages=messages, stream=stream)
        except self._ResponseError as e:
            error_msg = f"Ollama API error: {e.error} (Status code: {e.status_code})"
            self.logger.error(error_msg)
            return {"error": error_msg, "message": {"content": error_msg}}
        except Exception as e:
            error_msg = f"Error communicating with Ollama: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "message": {"content": error_msg}}

    def embeddings(self, text: str) -> List[float]:
        if not self.ollama_available:
            self.logger.error("Ollama is not available. Please install with 'pip install ollama'")
            return []
        try:
            response = self._Ollama.embed(model=self.model, input=text)
            return response.get("embedding", [])
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            return []

    def is_available(self) -> bool:
        if not self.ollama_available:
            return False
        try:
            self._Ollama.list()
            return True
        except Exception as e:
            self.logger.error(f"Ollama is not accessible: {str(e)}")
            return False

    async def async_chat(self, messages: List[Dict[str, str]], stream=False):
        if not self.ollama_available:
            error_msg = "Ollama is not available. Please install with 'pip install ollama'"
            self.logger.error(error_msg)
            return {"error": error_msg, "message": {"content": error_msg}}
        try:
            return await self.async_client.chat(model=self.model, messages=messages, stream=stream)
        except Exception as e:
            error_msg = f"Error in async communication with Ollama: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "message": {"content": error_msg}}
import pandas as pd
import logging

class PandasQueryIntegration:
    """
    This is a DataFrame query helper using LlamaIndex.
    It lets you ask questions about pandas DataFrames in plain English.
    If LlamaIndex or Ollama is missing, don't expect miracles.
    """
    def __init__(self, verbose=True, synthesize_response=True):
        self.verbose = verbose
        self.synthesize_response = synthesize_response
        try:
            from llama_index.experimental.query_engine import PandasQueryEngine
            from llama_index.core import PromptTemplate
            self.PandasQueryEngine = PandasQueryEngine
            self.PromptTemplate = PromptTemplate
            self.llama_index_available = True
        except ImportError:
            self.llama_index_available = False
            logging.warning("LlamaIndex not installed, PandasQueryIntegration will be unavailable.")

    def create_query_engine(self, df: pd.DataFrame, custom_instructions: str = None):
        if not self.llama_index_available:
            raise ImportError("LlamaIndex is not available.")
        engine = self.PandasQueryEngine(
            df=df,
            verbose=self.verbose,
            synthesize_response=self.synthesize_response
        )
        if custom_instructions:
            prompt = self.PromptTemplate(
                f"You are working with a pandas DataFrame called df.\n"
                f"{custom_instructions}\nQuery: {{query_str}}\nExpression:"
            )
            engine.update_prompts({"pandas_prompt": prompt})
        return engine

    def query_dataframe(self, df: pd.DataFrame, query: str, custom_instructions: str = None):
        if not self.llama_index_available:
            return {"error": "LlamaIndex not available.", "response": "", "pandas_instructions": ""}
        try:
            engine = self.create_query_engine(df, custom_instructions)
            response = engine.query(query)
            return {
                "response": str(response),
                "pandas_instructions": response.metadata.get("pandas_instruction_str", ""),
                "raw_response": response
            }
        except Exception as e:
            return {"error": str(e), "response": f"Error: {e}", "pandas_instructions": ""}

    def generate_dataset_insights(self, df: pd.DataFrame, num_insights: int = 5):
        queries = [
            "What is the overall shape and structure of this dataset?",
            "Identify any missing values or data quality issues in the dataset.",
            "What are the key statistical properties of the numerical columns?",
            "Are there any significant correlations between variables?",
            "What insights can you provide about the distribution of categorical variables?"
        ][:num_insights]
        return [
            {
                "query": q,
                "insight": self.query_dataframe(df, q)["response"]
            }
            for q in queries
        ]

    def compare_datasets(self, df1: pd.DataFrame, df2: pd.DataFrame, df1_name="Original", df2_name="Modified", aspects=None):
        if not self.llama_index_available:
            return {"error": "LlamaIndex not available.", "comparison": ""}
        if aspects is None:
            aspects = ["shape", "schema", "missing_values", "statistics", "distributions"]
        df1_copy = df1.copy()
        df2_copy = df2.copy()
        df1_copy['_dataset'] = df1_name
        df2_copy['_dataset'] = df2_name
        common_columns = list(set(df1.columns) & set(df2.columns))
        if not common_columns:
            return {"error": "No common columns", "comparison": ""}
        df1_subset = df1_copy[common_columns + ['_dataset']]
        df2_subset = df2_copy[common_columns + ['_dataset']]
        combined_df = pd.concat([df1_subset, df2_subset], axis=0, ignore_index=True)
        engine = self.create_query_engine(combined_df)
        comparison = {}
        for aspect in aspects:
            try:
                response = engine.query(f"Compare {aspect} between {df1_name} and {df2_name}.")
                comparison[aspect] = str(response)
            except Exception as e:
                comparison[aspect] = f"Error: {e}"
        return comparison

class OllamaLlamaIndexIntegration:
    """
    This is a fallback for pandas DataFrame query using Ollama as the LLM backend.
    It gives you pandas code and tries to execute it. If you break your DataFrame, that's on you.
    """
    def __init__(self, ollama_model="llama3", verbose=True):
        self.ollama_model = ollama_model
        self.verbose = verbose
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            self.ollama = None
            logging.warning("Ollama is not installed, OllamaLlamaIndexIntegration will not work.")

    def query_dataframe_with_ollama(self, df: pd.DataFrame, query: str):
        if not self.ollama:
            return {"error": "Ollama not installed.", "response": "", "pandas_code": ""}
        df_info = f"DataFrame Info:\n{df.info()}\n\nSample:\n{df.head().to_string()}"
        system_prompt = "You are a data analysis assistant. Given a DataFrame description and a question, return ONLY the pandas code to answer the query."
        user_prompt = f"{df_info}\nQuery: {query}"
        try:
            response = self.ollama.chat(
                model=self.ollama_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            code = response['message']['content'].strip()
            import re
            code_match = re.search(r'```(?:python)?\n(.*?)\n```', code, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
            try:
                result = eval(code, {"df": df, "pd": pd})
                result_str = result.to_string() if isinstance(result, pd.DataFrame) else str(result)
                return {"response": result_str, "pandas_code": code, "raw_result": result}
            except Exception as e:
                return {"error": f"Error executing pandas code: {e}", "response": "", "pandas_code": code}
        except Exception as e:
            return {"error": str(e), "response": "", "pandas_code": ""}