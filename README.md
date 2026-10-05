# Autonomous Sales Agent

A production-oriented autonomous AI sales agent designed to automate the sales outreach lifecycle from lead discovery to qualification, personalized outreach, follow-ups, reply handling, and human handoff.

The project is being built with a strong focus on **production engineering, agent reliability, safety, observability, evaluation, and maintainability**.

---

## Project Status

**Current Phase:** Foundation
**Current Day:** Day 1 — Architecture & Configuration Foundation
**Status:** 🟢 In Progress

> This project is being built step-by-step. Architecture and engineering quality are prioritized over speed.

---

## Goal

Build an autonomous sales system capable of:

1. Discovering leads
2. Researching and qualifying leads
3. Retrieving relevant business knowledge using RAG
4. Generating personalized outreach
5. Reviewing generated messages
6. Requesting human approval before sending
7. Sending emails
8. Scheduling follow-ups
9. Reading and classifying replies
10. Answering suitable questions automatically
11. Handing interested leads to a human
12. Handling unsubscribe/suppression requests safely
13. Maintaining an audit trail
14. Measuring agent quality through evaluations
15. Observing production behavior through tracing and monitoring

---

## High-Level Architecture

```text
Existing n8n Lead Pipeline
        ↓
Lead Ingestion API
        ↓
PostgreSQL
        ↓
LangGraph Supervisor
        │
        ├── Research + Qualification
        │
        ├── Outreach
        │     ├── Writer
        │     ├── Reviewer
        │     └── Human Approval
        │
        └── Conversation
              ├── Classifier
              ├── Responder
              └── Handoff
        ↓
Policy Engine / Guardrails
        ↓
MCP Tools
        ├── Lead MCP
        └── Email MCP
```

---

## Technology Stack

### Core

* Python 3.12+
* LangGraph
* Pydantic
* FastAPI
* FastMCP
* PostgreSQL
* Redis
* ChromaDB

### AI / LLM

* Groq
* LiteLLM
* Embeddings
* RAG

### Automation / Integration

* n8n
* SerpAPI
* Gmail

### Observability

* LangSmith
* OpenTelemetry
* Prometheus
* Grafana
* Structured JSON logging

### Engineering

* pytest
* Ruff
* Docker
* Docker Compose
* GitHub Actions
* YAML configuration
* Environment variables
* Secrets management

---

## Project Structure

```text
autonomous-sales-agent/
│
├── config/
│   ├── app.yaml
│   └── llm.yaml
│
├── docs/
│
├── scripts/
│
├── src/
│   └── app/
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── settings.py
│       │
│       ├── __init__.py
│       └── main.py
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

# Development Progress

## Day 1 — Architecture & Configuration Foundation

**Status:** 🟢 Completed

### Completed

* [x] Created Git repository
* [x] Created Python 3.12 virtual environment
* [x] Created `src/` project layout
* [x] Created `pyproject.toml`
* [x] Added project dependencies
* [x] Added development dependencies
* [x] Added `.gitignore`
* [x] Added `.env.example`
* [x] Added configuration directory
* [x] Added Pydantic Settings
* [x] Added YAML configuration loader
* [x] Added `app.yaml`
* [x] Added `llm.yaml`
* [x] Added basic application entry point
* [x] Verified environment configuration loading
* [x] Verified YAML configuration loading
* [x] Verified application startup

### Current Configuration Flow

```text
.env
 ↓
Pydantic Settings
 ↓
settings.py

config/*.yaml
 ↓
YAML Loader
 ↓
Application
```

### Current Startup Test

```text
Environment: development
Application: autonomous-sales-agent
LLM Provider: groq
Default Model: llama-3.3-70b-versatile
```

### Key Engineering Decision

Configuration is separated from application behavior.

* `.env` → secrets and environment-specific values
* YAML → application configuration
* Python code → application behavior

This allows configuration changes without modifying agent logic.

---

# Architecture Principles

## 1. Config-Driven

Business and model configuration should not be hard-coded into agent logic.

Avoid:

```python
if niche == "real_estate":
    ...
```

Prefer configuration-driven behavior.

---

## 2. Agent vs Policy vs Tools

The system separates responsibilities:

```text
Agent
  ↓
Reason / Decide
  ↓
Policy Engine
  ↓
Check whether action is allowed
  ↓
Tool
  ↓
Execute action
```

The agent should not directly bypass policy controls.

---

## 3. Untrusted External Data

Lead websites, scraped content, emails, and replies are treated as **untrusted data**.

External content must never automatically become instructions for the agent.

Prompt-injection scenarios will be explicitly tested.

---

## 4. Human Approval

Email sending will initially use:

```text
DRAFT
  ↓
REVIEW
  ↓
APPROVAL_PENDING
  ↓
APPROVED
  ↓
SEND
```

Default development behavior:

```text
dry_run = true
require_human_approval = true
```

---

## 5. Durable Execution

The agent should survive:

* Process crashes
* Worker restarts
* API failures
* LLM failures
* Tool timeouts
* Network failures

LangGraph checkpointing and persistent state will be used for recovery.

---

## 6. Idempotency

The system must prevent duplicate actions, especially duplicate emails.

Retries must not accidentally send the same email multiple times.

---

## 7. Observability

Important agent actions should be traceable:

```text
API Request
 ↓
Supervisor
 ↓
Research
 ↓
RAG
 ↓
LLM
 ↓
Qualification
 ↓
Writer
 ↓
Reviewer
 ↓
MCP Tool
 ↓
Email
```

---

## 8. Evaluation

Agent quality will be measured using fixed evaluation datasets.

Planned evaluation areas:

* Qualification
* Personalization
* Grounding
* Email quality
* Reply classification
* Safety
* Prompt injection resistance
* End-to-end behavior

Metrics will only be reported after actual evaluation.

---

# Development Plan

| Day | Focus                         | Status |
| --: | ----------------------------- | ------ |
|   1 | Architecture & Configuration  | 🟢     |
|   2 | Configuration System          | ⬜      |
|   3 | PostgreSQL & Domain Model     | ⬜      |
|   4 | LLM Gateway                   | ⬜      |
|   5 | Pydantic Contracts            | ⬜      |
|   6 | n8n Integration               | ⬜      |
|   7 | MCP Layer                     | ⬜      |
|   8 | RAG                           | ⬜      |
|   9 | Research Agent                | ⬜      |
|  10 | Qualification                 | ⬜      |
|  11 | Writer + Reviewer             | ⬜      |
|  12 | Guardrails + Policy Engine    | ⬜      |
|  13 | Human-in-the-Loop             | ⬜      |
|  14 | Conversation Agent            | ⬜      |
|  15 | Scheduler + Durable Execution | ⬜      |
|  16 | LangGraph Supervisor          | ⬜      |
|  17 | Evaluation Framework          | ⬜      |
|  18 | Observability                 | ⬜      |
|  19 | Monitoring                    | ⬜      |
|  20 | API Gateway + Security        | ⬜      |
|  21 | Audit & Compliance            | ⬜      |
|  22 | Testing                       | ⬜      |
|  23 | Failure Testing               | ⬜      |
|  24 | Dockerization                 | ⬜      |
|  25 | CI/CD                         | ⬜      |
|  26 | Production Configuration      | ⬜      |
|  27 | Deployment                    | ⬜      |
|  28 | Security Hardening            | ⬜      |
|  29 | Full Evaluation               | ⬜      |
|  30 | Production Demo               | ⬜      |

---

# Development Log

## 2026-10-05

### Day 1

**Completed:**

* Project initialized
* Python 3.12 environment configured
* `src/` package layout established
* Dependency management configured through `pyproject.toml`
* Pydantic Settings implemented
* YAML configuration loader implemented
* Application configuration created
* LLM configuration created
* Application startup verified

**Learning:**

* Python project structure
* Virtual environments
* `pyproject.toml`
* Pydantic Settings
* `.env` configuration
* YAML configuration
* Configuration vs application logic
* Basic package structure

**Next:**

* Finish Day 1 testing/tooling
* Start Day 2 configuration system

---

# Important Commands

Activate virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Install project + development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Run application:

```powershell
python -m app.main
```

Run tests:

```powershell
python -m pytest
```

Run Ruff:

```powershell
ruff check .
```

Check Git status:

```powershell
git status
```

---

# Notes

This project intentionally prioritizes:

**Correctness → Reliability → Security → Observability → Evaluation → Performance → Speed**

The goal is not to build a simple chatbot or demo. The goal is to demonstrate how an autonomous AI system can be designed and operated as a production-oriented engineering system.
