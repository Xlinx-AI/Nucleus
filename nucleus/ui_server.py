
import asyncio
from typing import Any

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    FastAPI = None
    JSONResponse = None
    FileResponse = None
    StaticFiles = None
    uvicorn = None

class UIServer:
    """
    Asynchronous web server for exposing hub features to users.
    Can be extended with custom routes and frontend integration.
    """
    def __init__(self, app_core: Any):
        self.app_core = app_core
        self.app = FastAPI() if FastAPI else None
        if self.app:
            # Монтируем статику webui/
            import os
            static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'webui')
            self.app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
            self._register_routes()

    def _register_routes(self):
        # "/" теперь отдаёт index.html через StaticFiles, не нужен отдельный обработчик

        @self.app.post("/submit_task")
        async def submit_task(payload: dict):
            user_query = payload.get("query", "")
            task_id = self.app_core.submit_task(user_query)
            return JSONResponse(content={"task_id": task_id})

        @self.app.get("/history")
        async def get_history():
            # Вернуть список сообщений истории (массив объектов)
            return JSONResponse(content={"history": getattr(self.app_core.history, "history", [])})

    def run(self, host: str = "127.0.0.1", port: int = 8080):
        """
        Launch the UI server using Uvicorn.
        """
        if not uvicorn or not self.app:
            print("FastAPI or Uvicorn is not installed. UI server cannot start.")
            return
        uvicorn.run(self.app, host=host, port=port)