# 🤖 AI DevOps Helper

<div align="center">

**Your AI-powered DevOps co-pilot — chat, debug, generate, deploy.**

[![CI/CD](https://github.com/hraj1206/ai-devops/actions/workflows/ci.yml/badge.svg)](https://github.com/hraj1206/ai-devops/actions)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/kubernetes-native-326CE5.svg)](https://kubernetes.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[**Quick Start**](#-quick-start) • [**Features**](#-features) • [**CLI Usage**](#-cli-usage) • [**API Docs**](#-api-reference) • [**Deploy**](#-deploy-to-kubernetes) • [**Roadmap**](#-roadmap)

</div>

---

## Why This Exists

DevOps engineers spend hours every week doing the same things: Googling why a pod is crashing, writing boilerplate Dockerfiles, copying CI/CD YAML from Stack Overflow, and staring at cryptic error logs.

**AI DevOps Helper** puts an expert DevOps engineer in your terminal. One command to debug a crash, generate a production-grade pipeline, or create Kubernetes manifests that actually follow best practices.

```bash
# Debug a crashing pod in seconds
kubectl logs my-pod | aiops logs

# Generate a full GitHub Actions pipeline
aiops generate pipeline --lang python --framework fastapi

# Get an expert answer instantly
aiops ask "What's the safest way to drain a node during maintenance?"
```

---

## ✨ Features

### 💬 DevOps Chat Assistant
Ask anything about Kubernetes, Docker, CI/CD, and infrastructure. Get expert answers with working commands, YAML examples, and real explanations — not vague theory.

```bash
aiops ask "My HPA isn't scaling. How do I debug it?"
aiops chat   # Multi-turn interactive session
```

### 🔍 Log Analyzer
Paste any log — Kubernetes events, Docker output, GitHub Actions failures, Nginx errors — and get instant root cause analysis with fix commands.

```bash
# Pipe directly from kubectl
kubectl logs my-pod --previous | aiops logs

# Analyze a log file
aiops logs --file build-failure.log --context "GitHub Actions"

# Paste interactively
aiops logs --paste
```

**Output includes:**
- 🎯 Root cause (not just symptoms)
- 🚨 Severity: CRITICAL / HIGH / MEDIUM / LOW  
- ⚡ Immediate fix commands you can run right now
- 🛠️ Long-term permanent solution
- 🛡️ Prevention strategy

### ⚙️ CI/CD Pipeline Generator
Describe your app, get a complete production-ready pipeline with caching, security scanning, Docker build, and Kubernetes deployment.

```bash
aiops generate pipeline --lang python --framework fastapi
aiops generate pipeline --lang node --platform gitlab-ci --namespace production
aiops generate pipeline --lang go --registry gcr.io --no-scan
```

**Generates:**
- GitHub Actions / GitLab CI / Jenkins
- Docker build with layer caching
- Trivy security scanning
- K8s rolling deployment with health checks
- Automatic rollback on failure
- Slack/Teams notifications (optional)

### 🏗️ Infrastructure as Code Generator
Describe your app in plain English, get production-grade infrastructure code that actually follows best practices.

```bash
# Dockerfile with multi-stage build, non-root user, healthcheck
aiops generate dockerfile --lang python --framework fastapi

# Full K8s manifests: Deployment, Service, HPA, Ingress, NetworkPolicy, PDB
aiops generate k8s "FastAPI app with Redis cache and PostgreSQL"

# Complete Helm chart with values.yaml, helpers, NOTES.txt
aiops generate helm "Go gRPC microservice" --port 50051
```

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone
git clone https://github.com/hraj1206/ai-devops.git
cd ai-devops

# 2. Set your API key
cp .env.example .env
echo "GROQ_API_KEY=your_key_here" > .env

# 3. Start
docker compose up -d

# 4. Verify
curl http://localhost:8000/health
# {"status":"healthy"}

# 5. Open API docs
open http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# 1. Clone & setup
git clone https://github.com/hraj1206/ai-devops.git
cd ai-devops/backend

# 2. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set API key
export GROQ_API_KEY=your_key_here

# 5. Run
uvicorn main:app --reload --port 8000
```

### Install the CLI

```bash
# From the repo root
pip install -r backend/requirements.txt

# Add to PATH (or run directly)
alias aiops="python cli/main.py"

# Or install as a script
pip install typer rich httpx
ln -s $(pwd)/cli/main.py /usr/local/bin/aiops
chmod +x /usr/local/bin/aiops
```

**Get your Anthropic API key:** [console.groq.com](https://console.groq.com)

---

## 📟 CLI Usage

### Ask Questions

```bash
# Single question
aiops ask "Why is my pod stuck in Pending state?"

# Interactive multi-turn session
aiops chat

# See all example commands
aiops examples
```

### Analyze Logs

```bash
# From kubectl (most common)
kubectl logs my-pod | aiops logs
kubectl logs my-pod --previous | aiops logs
kubectl describe pod my-pod | aiops logs --context "pod describe output"
kubectl get events --sort-by='.lastTimestamp' | aiops logs

# From a file
aiops logs --file /var/log/nginx/error.log
aiops logs --file build.log --context "GitHub Actions Node.js build"

# Paste interactively
aiops logs --paste
```

### Generate CI/CD Pipelines

```bash
# GitHub Actions (default)
aiops generate pipeline --lang python --framework fastapi

# GitLab CI
aiops generate pipeline --lang node --framework express --platform gitlab-ci

# Jenkins
aiops generate pipeline --lang java --framework spring --platform jenkins

# Custom options
aiops generate pipeline \
  --lang python \
  --framework fastapi \
  --registry gcr.io \
  --namespace production \
  --no-scan   # skip Trivy if needed
```

### Generate Infrastructure Code

```bash
# Dockerfile
aiops generate dockerfile --lang python --framework fastapi --port 8000
aiops generate dockerfile --lang node --port 3000
aiops generate dockerfile --description "Go app with CGO disabled for Alpine"

# Kubernetes Manifests
aiops generate k8s "Python FastAPI with PostgreSQL and Redis"
aiops generate k8s "Nginx serving static files" --replicas 3 --no-hpa
aiops generate k8s "MySQL database" --replicas 1 --no-hpa --no-ingress

# Helm Chart
aiops generate helm "FastAPI microservice" --lang python --port 8000
aiops generate helm "Go gRPC service" --lang go --port 50051
```

---

## 🌐 API Reference

The backend exposes a REST API with streaming support. Interactive docs at `/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/ask` | Ask a DevOps question (streaming) |
| `GET` | `/api/chat/examples` | Example questions |
| `POST` | `/api/logs/analyze` | Analyze log text |
| `POST` | `/api/logs/analyze-file` | Upload a log file |
| `GET` | `/api/logs/common-errors` | K8s/Docker error reference |
| `POST` | `/api/pipeline/generate` | Generate CI/CD pipeline |
| `GET` | `/api/pipeline/templates` | Available templates |
| `POST` | `/api/infra/generate` | Generate IaC (Dockerfile, K8s, Helm) |
| `POST` | `/api/infra/optimize-dockerfile` | Optimize existing Dockerfile |
| `GET` | `/health` | Health check |

### Example API Call

```bash
# Chat (streaming)
curl -N -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I set up pod autoscaling?", "stream": true}'

# Log analysis
curl -X POST http://localhost:8000/api/logs/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "logs": "Error: OOMKilled - container exceeded memory limit",
    "context": "Kubernetes pod logs",
    "stream": false
  }'

# Generate pipeline
curl -X POST http://localhost:8000/api/pipeline/generate \
  -H "Content-Type: application/json" \
  -d '{
    "app_language": "Python",
    "app_framework": "FastAPI",
    "platform": "github-actions",
    "deploy_target": "kubernetes",
    "stream": false
  }'
```

---

## ☸️ Deploy to Kubernetes

```bash
# 1. Create namespace and secret
kubectl apply -f k8s/manifests.yaml
kubectl create secret generic ai-devops-secrets \
  --from-literal=GROQ_API_KEY=your_key_here \
  -n ai-devops

# 2. Update the image in manifests.yaml with your registry, then:
kubectl apply -f k8s/manifests.yaml

# 3. Verify
kubectl get pods -n ai-devops
kubectl get svc -n ai-devops

# 4. Access
kubectl port-forward svc/ai-devops-backend 8000:8000 -n ai-devops
```

---

## 🗂️ Project Structure

```
ai-devops/
├── .github/
│   └── workflows/
│       └── ci.yml              # Self-hosted CI pipeline (dogfooding!)
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile              # Multi-stage, non-root, production-ready
│   ├── agents/
│   │   ├── chat_agent.py       # DevOps Q&A with streaming
│   │   ├── log_analyzer.py     # Log root cause analysis
│   │   ├── pipeline_gen.py     # CI/CD YAML generation
│   │   └── infra_gen.py        # Dockerfile / K8s / Helm generation
│   ├── prompts/
│   │   └── system_prompts.py   # Expert-level AI system prompts
│   └── tools/
│       └── claude_client.py    # Anthropic API client + streaming
├── cli/
│   └── main.py                 # Typer CLI with Rich formatting
├── k8s/
│   └── manifests.yaml          # K8s Deployment, HPA, Ingress, PDB
├── tests/
│   └── test_api.py
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🛣️ Roadmap

- [x] DevOps chat assistant with streaming
- [x] Log analyzer (paste / pipe / file upload)
- [x] CI/CD pipeline generator (GitHub Actions, GitLab CI, Jenkins)
- [x] Dockerfile generator with multi-stage builds
- [x] Kubernetes manifest generator
- [x] Helm chart generator
- [x] Docker Compose generator
- [x] Production K8s deployment with HPA, PDB, Ingress
- [ ] Web UI (React dashboard)
- [ ] Slack bot integration
- [ ] `kubectl` plugin (`kubectl ai`)
- [ ] VS Code extension
- [ ] Conversation memory / context persistence
- [ ] GitHub PR review agent (auto-reviews Dockerfiles and K8s YAML)
- [ ] Cost estimator for K8s resource configs
- [ ] Multi-cluster support

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

```bash
git clone https://github.com/hraj1206/ai-devops.git
cd ai-devops
cp .env.example .env   # Add your API key
docker compose up -d
```

**Good first issues:**
- Add a new agent (e.g., Terraform generator, cost estimator)
- Improve system prompts for better output quality
- Add more test coverage
- Build the React frontend

Please open an issue before starting large features.

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
Built with ❤️ using <a href="https://groq.com">Groq LLM</a> • <a href="https://fastapi.tiangolo.com">FastAPI</a> • <a href="https://kubernetes.io">Kubernetes</a>
</div>
