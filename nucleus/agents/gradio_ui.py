"""
Интерактивный Gradio-интерфейс для nucleus.agents: потоковое общение с агентом, поддержка истории, файлов, изображений и аудио.
"""

import os
from typing import Optional, List, Any

def stream_steps(agent, task: str, reset: bool = False, extra_args: Optional[dict] = None):
    """
    Потоковая генерация шагов агента nucleus для Gradio.
    """
    for step in agent.run(task, stream=True, reset=reset, additional_args=extra_args):
        # Здесь step — ActionEntry или результат
        msg = {"role": "assistant", "content": str(getattr(step, "llm_output", step))}
        yield msg
    # Финальный вывод
    if hasattr(step, "result"):
        yield {"role": "assistant", "content": f"Финальный ответ: {step.result}"}
    else:
        yield {"role": "assistant", "content": f"Финальный ответ: {str(step)}"}
    return

class GradioAgentUI:
    """
    Быстрый запуск Gradio-интерфейса для nucleus.agents.
    """
    def __init__(self, agent, upload_dir: Optional[str] = None):
        self.agent = agent
        self.upload_dir = upload_dir
        if self.upload_dir and not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def launch(self, **kwargs):
        import gradio as gr

        def chat_fn(prompt, chat_history):
            chat_history = chat_history or []
            for msg in stream_steps(self.agent, prompt, reset=False):
                chat_history.append(msg)
                yield chat_history

        with gr.Blocks() as demo:
            chatbox = gr.Chatbot(label="Nucleus Agent", show_label=True)
            txt = gr.Textbox(label="Ваш вопрос")
            txt.submit(chat_fn, [txt, chatbox], chatbox)
        demo.launch(**kwargs)