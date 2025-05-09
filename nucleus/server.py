from fastapi import FastAPI, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging

# Импортируем nucleus skills и pipeline
from nucleus.skills.prompt_router_skill import PromptRouterSkill
from nucleus.skills.heartbeat_skill import HeartbeatSkill
from nucleus.skills.image_generator_skill import ImageGeneratorSkill
from nucleus.pipeline import ResearchPipeline

app = FastAPI()
logger = logging.getLogger("NucleusServer")

# CORS для dev, в проде ограничить!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DI: skills и pipeline
skills = {
    "prompt_router": PromptRouterSkill(),
    "heartbeat": HeartbeatSkill(),
    "image_generator": ImageGeneratorSkill(),
}
pipeline = ResearchPipeline()

@app.get("/")
async def root():
    return {"message": "Welcome to Nucleus API"}

@app.post("/api/heartbeat/start")
async def start_heartbeat(interval: int = 5):
    await skills["heartbeat"].execute_async({"intent": "Start heartbeat", "interval": interval})
    return {"status": "heartbeat started", "interval": interval}

@app.post("/api/heartbeat/stop")
async def stop_heartbeat():
    await skills["heartbeat"].execute_async({"intent": "Stop heartbeat"})
    return {"status": "heartbeat stopped"}

@app.post("/api/image/generate")
async def generate_image(prompt: str):
    result = await skills["image_generator"].execute_async({"intent": "Generate image", "prompt": prompt, "return_format": "url"})
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/prompt/route")
async def route_prompt(text: str):
    result = await skills["prompt_router"].execute_async({"intent": "Route prompt", "desc": text})
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/research")
async def run_research(topic: str):
    result = await pipeline.run_topic_pipeline(topic)
    return result