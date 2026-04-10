from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Literal

from tools.groq_client import stream_response, get_response
from prompts.system_prompts import INFRA_SYSTEM_PROMPT

router = APIRouter()


class InfraRequest(BaseModel):
    # What to generate
    artifact_type: Literal["dockerfile", "helm-chart", "k8s-manifests", "docker-compose", "terraform"]
    
    # App description
    description: str  # Natural language description of the app
    app_language: Optional[str] = None
    app_framework: Optional[str] = None
    app_port: Optional[int] = 8000
    
    # Dockerfile specific
    base_image: Optional[str] = None  # Override base image
    multi_stage: Optional[bool] = True
    
    # K8s / Helm specific
    replicas: Optional[int] = 2
    namespace: Optional[str] = "default"
    include_hpa: Optional[bool] = True
    include_ingress: Optional[bool] = True
    ingress_host: Optional[str] = "myapp.example.com"
    
    # Resource limits
    cpu_request: Optional[str] = "100m"
    cpu_limit: Optional[str] = "500m"
    memory_request: Optional[str] = "128Mi"
    memory_limit: Optional[str] = "512Mi"
    
    # Extra context
    custom_requirements: Optional[str] = None
    stream: Optional[bool] = True


class InfraResponse(BaseModel):
    code: str


@router.post("/generate")
async def generate_infra(request: InfraRequest):
    """
    Generate production-grade infrastructure code from a plain English description.
    
    Examples:
    - "A Python FastAPI app that connects to PostgreSQL and Redis"
    - "A Node.js microservice with a persistent volume for file uploads"
    - "A stateful MySQL database with backup sidecar"
    """
    artifact_descriptions = {
        "dockerfile": "a production-grade, multi-stage Dockerfile",
        "helm-chart": "a complete Helm chart (Chart.yaml, values.yaml, templates/)",
        "k8s-manifests": "complete Kubernetes manifests (Deployment, Service, HPA, Ingress, NetworkPolicy)",
        "docker-compose": "a docker-compose.yml with all supporting services",
        "terraform": "Terraform configuration for a Kubernetes cluster",
    }

    user_message = f"""Generate {artifact_descriptions[request.artifact_type]} for:

**Application Description:** {request.description}
{f"**Language:** {request.app_language}" if request.app_language else ""}
{f"**Framework:** {request.app_framework}" if request.app_framework else ""}
{f"**Port:** {request.app_port}" if request.app_port else ""}

**Configuration:**
- Replicas: {request.replicas}
- Namespace: {request.namespace}
- CPU: {request.cpu_request} request / {request.cpu_limit} limit
- Memory: {request.memory_request} request / {request.memory_limit} limit
{f"- Ingress host: {request.ingress_host}" if request.include_ingress else ""}
{f"- Include HPA: yes" if request.include_hpa else ""}
{f"- Multi-stage build: yes" if request.multi_stage else ""}
{f"- Base image preference: {request.base_image}" if request.base_image else ""}

{f"**Additional requirements:** {request.custom_requirements}" if request.custom_requirements else ""}

Generate complete, production-ready code. Include comments explaining key decisions.
For Helm charts, generate all required files with proper structure."""

    messages = [{"role": "user", "content": user_message}]

    if request.stream:
        return StreamingResponse(
            stream_response(INFRA_SYSTEM_PROMPT, messages, max_tokens=8000),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    else:
        code = get_response(INFRA_SYSTEM_PROMPT, messages, max_tokens=8000)
        return InfraResponse(code=code)


@router.post("/optimize-dockerfile")
async def optimize_dockerfile(dockerfile_content: str):
    """Paste an existing Dockerfile and get optimization recommendations."""
    user_message = f"""Review and optimize this Dockerfile. Identify issues and rewrite it following best practices:

```dockerfile
{dockerfile_content}
```

Provide:
1. Issues found (security, size, caching, best practices)
2. Optimized Dockerfile
3. Explanation of each change and its impact (size reduction, security improvement, etc.)"""

    messages = [{"role": "user", "content": user_message}]
    result = get_response(INFRA_SYSTEM_PROMPT, messages)
    return {"optimized": result}


@router.get("/examples")
async def get_examples():
    """Example generation requests."""
    return {
        "examples": [
            {
                "artifact_type": "dockerfile",
                "description": "Python FastAPI app with poetry for dependency management",
                "app_language": "Python",
                "app_framework": "FastAPI",
                "app_port": 8000,
            },
            {
                "artifact_type": "k8s-manifests",
                "description": "Node.js API with Redis cache and PostgreSQL database",
                "app_language": "Node.js",
                "replicas": 3,
                "include_hpa": True,
            },
            {
                "artifact_type": "helm-chart",
                "description": "Stateless Go microservice with external secrets",
                "app_language": "Go",
                "app_port": 9090,
            },
            {
                "artifact_type": "docker-compose",
                "description": "Django app with PostgreSQL, Redis, Celery worker, and Nginx",
                "app_language": "Python",
                "app_framework": "Django",
            },
        ]
    }
