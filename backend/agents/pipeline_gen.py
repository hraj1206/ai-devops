from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Literal

from tools.groq_client import stream_response, get_response
from prompts.system_prompts import PIPELINE_SYSTEM_PROMPT

router = APIRouter()


class PipelineRequest(BaseModel):
    # App info
    app_language: str  # e.g. "Python", "Node.js", "Go", "Java"
    app_framework: Optional[str] = None  # e.g. "FastAPI", "Express", "Spring Boot"
    
    # Pipeline platform
    platform: Literal["github-actions", "gitlab-ci", "jenkins"] = "github-actions"
    
    # Deployment target
    deploy_target: Literal["kubernetes", "docker-compose", "ecs", "none"] = "docker-compose"
    
    # Features to include
    include_tests: bool = True
    include_docker_build: bool = True
    include_security_scan: bool = True
    include_notifications: bool = False
    notification_channel: Optional[str] = None  # "slack", "teams"
    
    # K8s specific
    k8s_namespace: Optional[str] = "default"
    registry: Optional[str] = "ghcr.io"  # or "dockerhub", "ecr", "gcr"
    
    # Additional requirements
    custom_requirements: Optional[str] = None
    stream: Optional[bool] = True


class PipelineResponse(BaseModel):
    pipeline_yaml: str
    explanation: str


@router.post("/generate")
async def generate_pipeline(request: PipelineRequest):
    """
    Generate a complete, production-ready CI/CD pipeline.
    
    Provide your app details and get a working pipeline with:
    - Lint & test stages
    - Docker build with layer caching  
    - Security scanning (Trivy)
    - Kubernetes deployment with health checks
    - Rollback on failure
    """
    features = []
    if request.include_tests:
        features.append("unit tests and linting")
    if request.include_docker_build:
        features.append(f"Docker build and push to {request.registry}")
    if request.include_security_scan:
        features.append("container security scanning with Trivy")
    if request.include_notifications and request.notification_channel:
        features.append(f"{request.notification_channel} notifications on success/failure")
    if request.deploy_target == "kubernetes":
        features.append(f"Kubernetes deployment to {request.k8s_namespace} namespace")
        features.append("rollback on deployment failure")
        features.append("post-deploy smoke test")

    user_message = f"""Generate a complete {request.platform} pipeline for:

**Application:**
- Language: {request.app_language}
- Framework: {request.app_framework or 'standard'}

**Pipeline Platform:** {request.platform}

**Deployment Target:** {request.deploy_target}
{"- Namespace: " + request.k8s_namespace if request.k8s_namespace else ""}
{"- Registry: " + request.registry if request.registry else ""}

**Features to include:**
{chr(10).join(f"- {f}" for f in features)}

{f"**Additional requirements:** {request.custom_requirements}" if request.custom_requirements else ""}

Generate the complete pipeline YAML with all stages. Make it production-ready with proper caching, 
error handling, and security practices. After the YAML, explain the key design decisions."""

    messages = [{"role": "user", "content": user_message}]

    if request.stream:
        return StreamingResponse(
            stream_response(PIPELINE_SYSTEM_PROMPT, messages, max_tokens=6000),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    else:
        response = get_response(PIPELINE_SYSTEM_PROMPT, messages, max_tokens=6000)
        return PipelineResponse(pipeline_yaml=response, explanation="See above")


@router.get("/templates")
async def get_templates():
    """Available pipeline templates."""
    return {
        "templates": [
            {
                "name": "Python FastAPI → Docker Compose",
                "platform": "github-actions",
                "app_language": "Python",
                "app_framework": "FastAPI",
                "deploy_target": "docker-compose",
            },
            {
                "name": "Node.js Express → Docker Compose",
                "platform": "github-actions",
                "app_language": "Node.js",
                "app_framework": "Express",
                "deploy_target": "docker-compose",
            },
            {
                "name": "Go → Docker Compose",
                "platform": "github-actions",
                "app_language": "Go",
                "deploy_target": "docker-compose",
            },
            {
                "name": "Java Spring Boot → Docker Compose",
                "platform": "github-actions",
                "app_language": "Java",
                "app_framework": "Spring Boot",
                "deploy_target": "docker-compose",
            },
        ]
    }
