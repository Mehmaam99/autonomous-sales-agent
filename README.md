# Autonomous Sales Agent — Days 1–10

## Project Overview

A production-oriented AI sales agent built with Python, Groq, PostgreSQL, and a LangGraph-oriented architecture.

The goal is to research companies, qualify leads using evidence, generate reviewed outreach, classify replies, and hand conversations to a human when needed.

## Tech Stack

- Python 3.12
- Groq LLM API
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic and YAML configuration
- HTTPX and Beautiful Soup
- pytest and Ruff
- Docker

## Day 1 — Project Foundation

- Initialized the autonomous-sales-agent repository.
- Created the initial project structure and development environment.
- Created the initial Git commit.

## Day 2 — Configuration System

- Implemented YAML-based application and LLM configuration.
- Added configuration validation.
- Added automated tests.
- Verified the configuration system with 8 tests.

Commit: `96a5cbe feat: build validated configuration system`

## Day 3 — Database Foundation

- Integrated PostgreSQL and SQLAlchemy.
- Created Company and Lead database models.
- Configured Alembic for database migrations.

## Day 4 — LLM Gateway

- Implemented a centralized LLM gateway using Groq.
- Established a shared interface for model calls.
- Added LLM gateway tests.

## Day 5 — Lead Qualification

- Created qualification schemas, service, and prompts.
- Structured qualification output with:
  - Score
  - Reasons
  - Supporting evidence
  - Qualified/not-qualified decision
- Verified a real Groq model response.

## Day 6 — Qualification Persistence

- Connected qualification results to the database.
- Implemented repository logic to save qualification results.
- Added tests and pushed the changes to GitHub.

## Day 7 — End-to-End Qualification Workflow

- Implemented the workflow for qualifying an existing lead.
- Added `scripts/verify_qualification.py`.
- Verified the qualification flow against the database and LLM.

## Day 8 — Website Research

- Implemented website fetching using HTTPX and Beautiful Soup.
- Extracted page titles and readable text from public HTML pages.
- Added timeouts, redirect limits, response-size limits, HTML content checks, and public-host validation.
- Connected website research to lead qualification.
- Added prompt rules to treat website content as untrusted input and avoid unsupported assumptions.

## Day 9 — Research Persistence

- Added the `WebsiteResearch` database model.
- Implemented `WebsiteResearchRepository`.
- Created an Alembic migration for the `website_research` table.
- Applied and verified the migration.

## Day 10 — Workflow Integration

- Connected website research persistence to the qualification workflow.
- Saved successful research results and failed research attempts.
- Added tests for successful and failed website research.
- Verified the qualification workflow against a sample lead.
- Confirmed that generic website content produces a conservative qualification result.

## Architecture Implemented So Far

1. Configuration and validation
2. PostgreSQL database and SQLAlchemy models
3. Centralized Groq LLM gateway
4. Website research and text extraction
5. Lead qualification service
6. Qualification result persistence
7. Website research history persistence
8. End-to-end qualification workflow

## Verification Status

- Day 1–10 implementation committed and pushed to GitHub.
- Latest test run during Day 11 setup: **25 tests passed**.
- Ruff checks passed after fixing one lint issue.
- Git working tree was clean after the Day 9–10 push.

## Current Limitations

- Website research currently fetches a single page.
- Multi-page research and stronger evidence extraction are planned.
- Outreach generation and review are not implemented yet.
- Human approval, reply classification, conversation handling, and handoff are pending.
- Supervisor orchestration, API, monitoring, evaluation, and deployment hardening remain future work.
- Website security checks are a starting point and do not guarantee complete production-grade SSRF protection.

## Days 11–20 Roadmap

- **Days 11–12:** Multi-page website research, evidence extraction, and tests.
- **Days 13–14:** Qualification reliability, retries, and error handling.
- **Days 15–17:** Outreach writer, reviewer, and human approval.
- **Days 18–20:** Reply classification, conversation workflow, and human handoff.
- Finish with integration tests, Ruff checks, Git commits, and GitHub push.

## Development Principles

- Use evidence instead of guessing company facts.
- Treat external website content as untrusted input.
- Make small, testable changes.
- Keep code understandable and explainable.
- Mark features complete only after implementation and verification.
