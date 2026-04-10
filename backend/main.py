from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import uvicorn

from agents.chat_agent import router as chat_router
from agents.log_analyzer import router as log_router
from agents.pipeline_gen import router as pipeline_router
from agents.infra_gen import router as infra_router
from agents.project_gen import router as project_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 AI DevOps Helper starting up...")
    yield
    print("🛑 AI DevOps Helper shutting down...")


app = FastAPI(
    title="AI DevOps Helper",
    description="Your AI-powered DevOps co-pilot: chat, log analysis, CI/CD & IaC generation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(log_router, prefix="/api/logs", tags=["Log Analyzer"])
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["CI/CD Generator"])
app.include_router(infra_router, prefix="/api/infra", tags=["IaC Generator"])
app.include_router(project_router, prefix="/api/project", tags=["Project Generator"])


@app.get("/")
async def root():
    return {
        "name": "AI DevOps Helper",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/chat/ask",
            "logs": "/api/logs/analyze",
            "pipeline": "/api/pipeline/generate",
            "infra": "/api/infra/generate",
            "project": "/api/project/generate",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
