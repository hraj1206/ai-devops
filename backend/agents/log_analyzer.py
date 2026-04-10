from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from tools.groq_client import stream_response, get_response
from prompts.system_prompts import LOG_ANALYZER_PROMPT

router = APIRouter()


class LogAnalyzeRequest(BaseModel):
    logs: str
    context: Optional[str] = None  # e.g. "This is a GitHub Actions build log"
    stream: Optional[bool] = True


class LogAnalyzeResponse(BaseModel):
    analysis: str


@router.post("/analyze")
async def analyze_logs(request: LogAnalyzeRequest):
    """
    Paste any logs and get instant root cause analysis with fixes.
    
    Supports logs from:
    - Kubernetes (kubectl logs, kubectl describe, kubectl get events)
    - Docker (docker logs, docker inspect)
    - GitHub Actions / GitLab CI pipeline output
    - Nginx / Traefik / Istio access and error logs
    - Helm install/upgrade failures
    - Terraform apply errors
    """
    context_prefix = ""
    if request.context:
        context_prefix = f"Context provided by user: {request.context}\n\n"

    user_message = f"""{context_prefix}Please analyze the following logs and provide:
1. Root cause identification
2. Severity assessment  
3. Immediate fix commands
4. Long-term solution
5. Prevention steps

LOGS:
```
{request.logs}
```"""

    messages = [{"role": "user", "content": user_message}]

    if request.stream:
        return StreamingResponse(
            stream_response(LOG_ANALYZER_PROMPT, messages),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    else:
        analysis = get_response(LOG_ANALYZER_PROMPT, messages)
        return LogAnalyzeResponse(analysis=analysis)


@router.post("/analyze-file")
async def analyze_log_file(
    file: UploadFile = File(...),
    context: Optional[str] = None,
):
    """Upload a log file directly for analysis."""
    content = await file.read()
    log_text = content.decode("utf-8", errors="replace")

    # Truncate very large files to last 500 lines (most relevant for errors)
    lines = log_text.splitlines()
    if len(lines) > 500:
        log_text = f"[... {len(lines) - 500} earlier lines truncated ...]\n" + "\n".join(lines[-500:])

    request = LogAnalyzeRequest(
        logs=log_text,
        context=context or f"Log file: {file.filename}",
        stream=False,
    )

    user_message = f"""Context: Log file uploaded: {file.filename}
{f'Additional context: {context}' if context else ''}

Please analyze these logs:
```
{log_text}
```"""

    messages = [{"role": "user", "content": user_message}]
    analysis = get_response(LOG_ANALYZER_PROMPT, messages)
    return LogAnalyzeResponse(analysis=analysis)


@router.get("/common-errors")
async def get_common_errors():
    """Reference guide for common K8s/Docker error patterns."""
    return {
        "kubernetes": [
            {"error": "CrashLoopBackOff", "cause": "Container keeps crashing on start", "quick_fix": "kubectl logs <pod> --previous"},
            {"error": "OOMKilled", "cause": "Container exceeded memory limit", "quick_fix": "kubectl describe pod <pod> | grep -A5 OOM"},
            {"error": "ImagePullBackOff", "cause": "Cannot pull container image", "quick_fix": "kubectl describe pod <pod> | grep -A10 Events"},
            {"error": "Pending", "cause": "Pod can't be scheduled (resources, taints, affinity)", "quick_fix": "kubectl describe pod <pod> | grep -A20 Events"},
            {"error": "Evicted", "cause": "Node ran out of resources", "quick_fix": "kubectl get events --sort-by='.lastTimestamp'"},
            {"error": "CreateContainerConfigError", "cause": "ConfigMap or Secret missing", "quick_fix": "kubectl describe pod <pod>"},
        ],
        "docker": [
            {"error": "No space left on device", "cause": "Docker disk full", "quick_fix": "docker system prune -a"},
            {"error": "permission denied", "cause": "Volume mount permissions", "quick_fix": "Check USER in Dockerfile"},
            {"error": "port is already allocated", "cause": "Port conflict", "quick_fix": "docker ps | grep <port>"},
        ],
    }
