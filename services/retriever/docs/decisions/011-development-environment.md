---
adr: 11
title: Development Environment
status: accepted
date: 2024-12-18
tags:
  - development
  - devcontainer
  - vscode
supersedes: null
superseded_by: null
related: [1]
---

# 011: Development Environment

## Status

Accepted

## Context

Need consistent development environment across contributors. Requirements:
- Works on Mac, Linux, Windows
- Easy onboarding for new developers
- Consistent Python version and dependencies
- Works with VS Code and GitHub Codespaces

## Decision

**Dev Containers** for VS Code and GitHub Codespaces.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Local setup docs only | Inconsistent environments, "works on my machine" |
| Docker Compose only | Heavier, more complex setup |
| Nix | Steeper learning curve |
| pyenv + virtualenv | Manual setup, version drift |

## Consequences

**Easier:**
- One-click setup in VS Code
- Works in GitHub Codespaces (cloud dev)
- Python version locked
- All tools pre-installed

**Harder:**
- Requires Docker
- Container builds can be slow initially
- Some IDE features may need configuration

## Configuration

```json
// .devcontainer/devcontainer.json
{
  "name": "Retriever Dev",
  "build": { "dockerfile": "Dockerfile" },
  "features": {
    "ghcr.io/devcontainers/features/python:1": { "version": "3.13" }
  },
  "postCreateCommand": "pip install -e '.[dev]'",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "charliermarsh.ruff",
        "ms-python.mypy-type-checker"
      ]
    }
  },
  "forwardPorts": [8000]
}
```

## Local Development Without Containers

If you prefer local setup:

```bash
# Requires Python 3.13+
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

# Run dev server
uvicorn src.main:app --reload --port 8000
```

## GitHub Codespaces

Click "Code" → "Codespaces" → "Create codespace on main" for instant cloud development environment.
