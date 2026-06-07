from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from contextlib import asynccontextmanager
import uvicorn
import os

from agents.chat_agent import router as chat_router
from agents.log_analyzer import router as log_router
from agents.pipeline_gen import router as pipeline_router
from agents.infra_gen import router as infra_router
from agents.project_gen import router as project_router
import logging
from pathlib import Path


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[START] AI DevOps Helper starting up...")
    logging.getLogger("uvicorn").info("Starting AI DevOps Helper; checking environment...")
    # Log presence (not value) of key env vars for debugging
    groq_present = bool(os.getenv("GROQ_API_KEY"))
    a_iops_present = bool(os.getenv("AIOPS_API_URL"))
    logging.getLogger("ai_devops").info(f"GROQ_API_KEY present={groq_present}, AIOPS_API_URL present={a_iops_present}")
    yield
    print("[STOP] AI DevOps Helper shutting down...")


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
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        for path in ["index.html", "../index.html", "/app/index.html"]:
            if os.path.exists(path):
                return FileResponse(path)
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


@app.get("/config.json")
async def config(request: Request):
    """Runtime configuration for the frontend. Returns the backend URL (from env or request)."""
    api = os.getenv("AIOPS_API_URL")
    if not api:
        base = str(request.base_url).rstrip("/")
        api = base
    return {"api_url": api}


def _secret_file_candidates():
    return [
        Path("/etc/secrets/GROQ_API_KEY"),
        Path("/etc/secrets/groq_api_key"),
        Path("./.env"),
        Path("./secrets/GROQ_API_KEY"),
        Path("./secrets/groq_api_key"),
    ]


@app.get("/debug-config")
async def debug_config(request: Request):
    """Return detected configuration sources (does not expose secret values)."""
    api_env = os.getenv("AIOPS_API_URL")
    groq_env = os.getenv("GROQ_API_KEY")
    groq_file = None
    found_files = []
    for p in _secret_file_candidates():
        try:
            if p.exists():
                found_files.append(str(p))
                if groq_file is None and (p.name.lower().startswith("groq") or p.name.lower().startswith("groq_api_key") or p.name == ".env"):
                    groq_file = str(p)
        except Exception:
            continue

    return {
        "api_url_from_env": bool(api_env),
        "api_url_value_preview": api_env if api_env and len(api_env) < 200 else (api_env[:100] + "..." if api_env else None),
        "groq_key_in_env": bool(groq_env),
        "groq_key_file_found": bool(groq_file),
        "found_secret_files": found_files,
        "request_base_url": str(request.base_url).rstrip("/"),
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
