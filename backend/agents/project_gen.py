from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Literal

from tools.groq_client import stream_response, get_response
from prompts.system_prompts import PROJECT_SYSTEM_PROMPT

router = APIRouter()


class ProjectRequest(BaseModel):
    # Project description
    description: str  # Natural language description of the complete project
    
    # Tech stack preferences
    tech_stack: Optional[Literal[
        "auto", "react-node", "vue-nest", "angular-spring", 
        "nextjs", "fastapi-react", "django-react", "flask-vue"
    ]] = "auto"
    
    # Complexity level
    complexity: Optional[Literal["minimal", "standard", "advanced"]] = "standard"
    
    # Include options
    include_docker: Optional[bool] = True
    include_git: Optional[bool] = True
    include_tests: Optional[bool] = True
    include_docs: Optional[bool] = True
    include_deployment: Optional[bool] = True
    
    # Additional features
    additional_features: Optional[str] = None
    
    # Streaming
    stream: Optional[bool] = True


class ProjectResponse(BaseModel):
    files: dict  # Dictionary of filename -> content


@router.post("/generate")
async def generate_project(request: ProjectRequest):
    """
    Generate a complete project structure from a plain English description.
    
    Examples:
    - "Create a full-stack web app with React frontend, Node.js API, PostgreSQL database"
    - "Build a microservices architecture with 3 services, API gateway, and monitoring"
    - "Develop an e-commerce platform with user auth, product catalog, and payment integration"
    """
    
    tech_stack_descriptions = {
        "auto": "automatically detect the best tech stack",
        "react-node": "React frontend + Node.js/Express backend",
        "vue-nest": "Vue.js frontend + NestJS backend",
        "angular-spring": "Angular frontend + Spring Boot backend",
        "nextjs": "Next.js full-stack application",
        "fastapi-react": "FastAPI backend + React frontend",
        "django-react": "Django backend + React frontend",
        "flask-vue": "Flask backend + Vue.js frontend"
    }
    
    complexity_descriptions = {
        "minimal": "basic project structure with essential files",
        "standard": "production-ready with best practices, error handling, and testing",
        "advanced": "enterprise-grade with advanced features, security, monitoring, and scalability"
    }

    user_message = f"""Generate a complete project structure for:

**Project Description:** {request.description}

**Tech Stack:** {tech_stack_descriptions[request.tech_stack]}
**Complexity Level:** {complexity_descriptions[request.complexity]}

**Include Components:**
{f"- Docker setup: yes" if request.include_docker else "- Docker setup: no"}
{f"- Git repository: yes" if request.include_git else "- Git repository: no"}
{f"- Unit tests: yes" if request.include_tests else "- Unit tests: no"}
{f"- Documentation: yes" if request.include_docs else "- Documentation: no"}
{f"- Deployment configuration: yes" if request.include_deployment else "- Deployment configuration: no"}

{f"**Additional Features:** {request.additional_features}" if request.additional_features else ""}

**Requirements:**
1. Generate ALL necessary files for a complete, runnable project
2. Include proper project structure and folder organization
3. Add all required dependencies and configuration files
4. Include environment files (.env.example)
5. Add README.md with setup and run instructions
6. Include proper .gitignore file
7. Add package.json, requirements.txt, or equivalent dependency files
8. Include basic application code that demonstrates the functionality
9. Add database schemas/migrations if needed
10. Include API documentation if applicable

**Output Format:**
Return a structured response with file paths as keys and file contents as values.
Use proper file extensions and directory structure.
Ensure all code is production-ready and follows best practices.

Example structure:
```
project-root/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
├── backend/
│   ├── src/
│   ├── requirements.txt
│   └── ...
├── docker-compose.yml
├── README.md
└── .gitignore
```"""

    messages = [{"role": "user", "content": user_message}]

    if request.stream:
        return StreamingResponse(
            stream_response(PROJECT_SYSTEM_PROMPT, messages, max_tokens=12000),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    else:
        files = get_response(PROJECT_SYSTEM_PROMPT, messages, max_tokens=12000)
        return ProjectResponse(files=files)