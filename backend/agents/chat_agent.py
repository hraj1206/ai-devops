from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from tools.groq_client import stream_response, get_response
from prompts.system_prompts import CHAT_SYSTEM_PROMPT

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[list[ChatMessage]] = []
    stream: Optional[bool] = True


class ChatResponse(BaseModel):
    response: str


@router.post("/ask")
async def ask(request: ChatRequest):
    """
    Ask any DevOps question. Supports multi-turn conversation history.
    
    Example questions:
    - "Why is my pod in CrashLoopBackOff?"
    - "How do I set up HPA for my deployment?"
    - "What's the difference between Deployment and StatefulSet?"
    - "Write me a Kubernetes network policy that blocks all ingress"
    """
    messages = []

    # Add conversation history
    for msg in (request.history or []):
        messages.append({"role": msg.role, "content": msg.content})

    # Add the new user message
    messages.append({"role": "user", "content": request.message})

    if request.stream:
        return StreamingResponse(
            stream_response(CHAT_SYSTEM_PROMPT, messages),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        response_text = get_response(CHAT_SYSTEM_PROMPT, messages)
        return ChatResponse(response=response_text)


@router.get("/examples")
async def get_examples():
    """Return example questions to get users started."""
    return {
        "examples": [
            "My pod keeps crashing with OOMKilled. How do I debug this?",
            "How do I roll back a Kubernetes deployment to the previous version?",
            "Explain the difference between ClusterIP, NodePort, and LoadBalancer services",
            "How do I set up pod autoscaling based on custom metrics?",
            "What's the best way to manage secrets in Kubernetes?",
            "How do I configure liveness and readiness probes correctly?",
            "My Docker image is 2GB. How do I make it smaller?",
            "How do I drain a node safely before maintenance?",
            "Explain Kubernetes RBAC with a practical example",
            "How do I debug a service that's not routing traffic correctly?",
        ]
    }
