# Ecometrics
AI Financial & Wealth Operating System — modular platform connecting market data, AI,
simulation, risk management, capital allocation, execution, and wealth goals.
Core principle: Build the brain first. Give the brain a body later. Expand the body only when the
system proves it needs more compute.
This repo starts at Phase 2 — Cloud Foundation of the master roadmap.
## Structure
ecometrics/services/api-gateway - First service: FastAPI app, health checks
.devcontainer - GitHub Codespaces config
.github/workflows - CI: lint + test on every push
docs - Architecture and roadmap reference docs
.env.example - Template for secrets/config
## Getting started
1. Open this repo in GitHub Codespaces (Code then Codespaces then Create codespace)
2. Copy .env.example to .env and fill in real values once you have a database
3. Run: cd services/api-gateway && pip install -r requirements.txt && uvicorn app.main:app --reload
4. Visit http://localhost:8000/health
## Deployment
Deployed via Render, connected to this GitHub repo.
