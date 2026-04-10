#!/usr/bin/env python3
"""
AI DevOps Helper CLI
Your AI-powered DevOps co-pilot right in the terminal.

Usage:
    aiops ask "Why is my pod in CrashLoopBackOff?"
    aiops logs --file crash.log
    aiops logs --paste
    aiops generate pipeline --lang python --framework fastapi --platform github-actions
    aiops generate dockerfile --lang python --framework fastapi --port 8000
    aiops generate k8s --description "FastAPI app with Redis"
"""

import typer
import httpx
import sys
import os
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

app = typer.Typer(
    name="aiops",
    help="🤖 AI DevOps Helper — Your intelligent DevOps co-pilot",
    add_completion=False,
    rich_markup_mode="rich",
)
generate_app = typer.Typer(help="Generate infrastructure code, pipelines, and more")
app.add_typer(generate_app, name="generate")

console = Console()

# Default API base URL (override with AIOPS_API_URL env var)
API_BASE = os.getenv("AIOPS_API_URL", "http://localhost:8000")


def get_client():
    return httpx.Client(base_url=API_BASE, timeout=120.0)


def stream_and_print(url: str, payload: dict):
    """Stream response from API and print with rich formatting."""
    full_response = ""
    
    with httpx.Client(base_url=API_BASE, timeout=120.0) as client:
        with client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                console.print(f"[red]Error {response.status_code}:[/red] {response.text}")
                raise typer.Exit(1)
            
            console.print()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    full_response += chunk
                    print(chunk, end="", flush=True)
    
    print("\n")
    return full_response


@app.command()
def ask(
    question: str = typer.Argument(..., help="Your DevOps question"),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming"),
):
    """
    [bold green]Ask any DevOps question.[/bold green]
    
    Examples:
        aiops ask "Why is my pod in CrashLoopBackOff?"
        aiops ask "How do I set up HPA for my deployment?"
        aiops ask "What's the difference between Deployment and StatefulSet?"
    """
    console.print(
        Panel(
            f"[bold cyan]Question:[/bold cyan] {question}",
            title="🤖 AI DevOps Helper",
            border_style="cyan",
        )
    )

    payload = {"message": question, "stream": not no_stream}

    if not no_stream:
        stream_and_print("/api/chat/ask", payload)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Thinking...", total=None)
            with get_client() as client:
                response = client.post("/api/chat/ask", json=payload)
                data = response.json()
        
        console.print(Markdown(data["response"]))


@app.command()
def logs(
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Log file to analyze"),
    paste: bool = typer.Option(False, "--paste", "-p", help="Paste logs interactively"),
    context: Optional[str] = typer.Option(None, "--context", "-c", help="Context about the logs (e.g. 'GitHub Actions build')"),
):
    """
    [bold green]Analyze logs and get instant root cause analysis.[/bold green]
    
    Examples:
        aiops logs --file crash.log
        aiops logs --file /var/log/nginx/error.log --context "nginx ingress"
        kubectl logs my-pod | aiops logs
        aiops logs --paste
    """
    log_content = ""

    if file:
        if not file.exists():
            console.print(f"[red]File not found:[/red] {file}")
            raise typer.Exit(1)
        log_content = file.read_text()
        console.print(f"[dim]Reading {file} ({len(log_content.splitlines())} lines)...[/dim]")
    elif paste:
        console.print("[yellow]Paste your logs below. Press Ctrl+D (or Ctrl+Z on Windows) when done:[/yellow]")
        log_content = sys.stdin.read()
    elif not sys.stdin.isatty():
        # Piped input: e.g. kubectl logs my-pod | aiops logs
        log_content = sys.stdin.read()
    else:
        console.print("[red]Error:[/red] Provide logs via --file, --paste, or pipe")
        console.print("Example: [cyan]kubectl logs my-pod | aiops logs[/cyan]")
        raise typer.Exit(1)

    if not log_content.strip():
        console.print("[red]Error:[/red] No log content found")
        raise typer.Exit(1)

    console.print(
        Panel(
            f"Analyzing [bold]{len(log_content.splitlines())}[/bold] lines of logs...",
            title="🔍 Log Analyzer",
            border_style="yellow",
        )
    )

    payload = {
        "logs": log_content,
        "context": context,
        "stream": True,
    }
    stream_and_print("/api/logs/analyze", payload)


@generate_app.command("pipeline")
def generate_pipeline(
    lang: str = typer.Option(..., "--lang", "-l", help="App language (python, node, go, java)"),
    framework: Optional[str] = typer.Option(None, "--framework", "-f", help="Framework (fastapi, express, etc.)"),
    platform: str = typer.Option("github-actions", "--platform", "-p", help="CI platform: github-actions, gitlab-ci, jenkins"),
    deploy: str = typer.Option("kubernetes", "--deploy", "-d", help="Deploy target: kubernetes, docker-compose, none"),
    registry: str = typer.Option("ghcr.io", "--registry", "-r", help="Container registry"),
    namespace: str = typer.Option("default", "--namespace", "-n", help="K8s namespace"),
    no_scan: bool = typer.Option(False, "--no-scan", help="Skip security scanning"),
    extra: Optional[str] = typer.Option(None, "--extra", "-e", help="Additional requirements"),
):
    """
    [bold green]Generate a production-ready CI/CD pipeline.[/bold green]
    
    Examples:
        aiops generate pipeline --lang python --framework fastapi
        aiops generate pipeline --lang node --platform gitlab-ci --deploy kubernetes
        aiops generate pipeline --lang go --registry gcr.io --namespace production
    """
    console.print(
        Panel(
            f"[bold cyan]{lang.title()}[/bold cyan] → [bold green]{platform}[/bold green] → [bold yellow]{deploy}[/bold yellow]",
            title="⚙️  CI/CD Pipeline Generator",
            border_style="green",
        )
    )

    payload = {
        "app_language": lang.title(),
        "app_framework": framework,
        "platform": platform,
        "deploy_target": deploy,
        "registry": registry,
        "k8s_namespace": namespace,
        "include_security_scan": not no_scan,
        "custom_requirements": extra,
        "stream": True,
    }
    stream_and_print("/api/pipeline/generate", payload)


@generate_app.command("dockerfile")
def generate_dockerfile(
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Describe your app"),
    lang: Optional[str] = typer.Option(None, "--lang", "-l", help="App language"),
    framework: Optional[str] = typer.Option(None, "--framework", "-f", help="Framework"),
    port: int = typer.Option(8000, "--port", "-p", help="App port"),
    extra: Optional[str] = typer.Option(None, "--extra", "-e", help="Additional requirements"),
):
    """
    [bold green]Generate an optimized, production-grade Dockerfile.[/bold green]
    
    Examples:
        aiops generate dockerfile --lang python --framework fastapi --port 8000
        aiops generate dockerfile --description "Node.js app with Puppeteer for PDF generation"
        aiops generate dockerfile --lang go --port 9090
    """
    desc = description or f"{lang or 'application'} app{f' using {framework}' if framework else ''}"
    
    console.print(
        Panel(
            f"Generating Dockerfile for: [bold cyan]{desc}[/bold cyan]",
            title="🐳 Dockerfile Generator",
            border_style="blue",
        )
    )

    payload = {
        "artifact_type": "dockerfile",
        "description": desc,
        "app_language": lang,
        "app_framework": framework,
        "app_port": port,
        "custom_requirements": extra,
        "stream": True,
    }
    stream_and_print("/api/infra/generate", payload)


@generate_app.command("k8s")
def generate_k8s(
    description: str = typer.Argument(..., help="Describe what you're deploying"),
    replicas: int = typer.Option(2, "--replicas", "-r", help="Number of replicas"),
    namespace: str = typer.Option("default", "--namespace", "-n", help="K8s namespace"),
    port: int = typer.Option(8000, "--port", "-p", help="App port"),
    no_hpa: bool = typer.Option(False, "--no-hpa", help="Skip HPA"),
    no_ingress: bool = typer.Option(False, "--no-ingress", help="Skip Ingress"),
    host: str = typer.Option("myapp.example.com", "--host", "-H", help="Ingress host"),
):
    """
    [bold green]Generate complete Kubernetes manifests.[/bold green]
    
    Examples:
        aiops generate k8s "FastAPI app with Redis cache"
        aiops generate k8s "Stateful MySQL database" --no-hpa --replicas 1
        aiops generate k8s "Node.js API" --namespace production --host api.mycompany.com
    """
    console.print(
        Panel(
            f"Generating K8s manifests for: [bold cyan]{description}[/bold cyan]",
            title="☸️  Kubernetes Manifest Generator",
            border_style="magenta",
        )
    )

    payload = {
        "artifact_type": "k8s-manifests",
        "description": description,
        "app_port": port,
        "replicas": replicas,
        "namespace": namespace,
        "include_hpa": not no_hpa,
        "include_ingress": not no_ingress,
        "ingress_host": host,
        "stream": True,
    }
    stream_and_print("/api/infra/generate", payload)


@generate_app.command("helm")
def generate_helm(
    description: str = typer.Argument(..., help="Describe your application"),
    lang: Optional[str] = typer.Option(None, "--lang", "-l", help="App language"),
    port: int = typer.Option(8000, "--port", "-p", help="App port"),
):
    """
    [bold green]Generate a complete Helm chart.[/bold green]
    
    Examples:
        aiops generate helm "Python FastAPI microservice" --lang python
        aiops generate helm "Go gRPC service" --lang go --port 50051
    """
    console.print(
        Panel(
            f"Generating Helm chart for: [bold cyan]{description}[/bold cyan]",
            title="⛵ Helm Chart Generator",
            border_style="cyan",
        )
    )

    payload = {
        "artifact_type": "helm-chart",
        "description": description,
        "app_language": lang,
        "app_port": port,
        "stream": True,
    }
    stream_and_print("/api/infra/generate", payload)


@app.command()
def chat():
    """
    [bold green]Start an interactive DevOps chat session.[/bold green]
    
    Multi-turn conversation with your AI DevOps co-pilot.
    Type 'exit' or 'quit' to end the session.
    """
    console.print(
        Panel(
            "Welcome to [bold cyan]AI DevOps Helper[/bold cyan] interactive mode!\n"
            "Ask anything about Kubernetes, Docker, CI/CD, infrastructure...\n"
            "Type [bold red]exit[/bold red] to quit.",
            title="🤖 DevOps Co-pilot",
            border_style="cyan",
        )
    )

    history = []

    while True:
        try:
            question = Prompt.ask("\n[bold cyan]You[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! 👋[/dim]")
            break

        if question.lower() in ("exit", "quit", "bye"):
            console.print("[dim]Goodbye! 👋[/dim]")
            break

        if not question.strip():
            continue

        console.print("\n[bold green]AI DevOps Helper[/bold green]")

        payload = {
            "message": question,
            "history": history,
            "stream": True,
        }

        response = stream_and_print("/api/chat/ask", payload)

        # Build up conversation history for multi-turn
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": response})

        # Keep history manageable (last 10 exchanges)
        if len(history) > 20:
            history = history[-20:]


@app.command()
def examples():
    """Show example commands to get you started."""
    console.print(
        Panel(
            """[bold cyan]Chat & Ask[/bold cyan]
  aiops ask "Why is my pod in CrashLoopBackOff?"
  aiops ask "How do I drain a Kubernetes node safely?"
  aiops chat  [dim]# Interactive multi-turn mode[/dim]

[bold yellow]Log Analysis[/bold yellow]
  kubectl logs my-pod | aiops logs
  aiops logs --file /var/log/nginx/error.log
  aiops logs --paste --context "GitHub Actions build failure"

[bold green]Generate CI/CD Pipelines[/bold green]
  aiops generate pipeline --lang python --framework fastapi
  aiops generate pipeline --lang node --platform gitlab-ci
  aiops generate pipeline --lang go --registry gcr.io --namespace prod

[bold blue]Generate Infrastructure[/bold blue]
  aiops generate dockerfile --lang python --framework fastapi
  aiops generate k8s "FastAPI app with Redis and PostgreSQL"
  aiops generate helm "Go microservice with gRPC" --port 50051
  aiops generate k8s "MySQL database" --replicas 1 --no-hpa""",
            title="📚 Example Commands",
            border_style="green",
        )
    )


if __name__ == "__main__":
    app()
