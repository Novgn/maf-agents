# Story 1.1: Project Setup and Dependency Installation

**Epic**: Epic 1: Foundation & Workflow Orchestration

## User Story

As a **developer**,
I want **a Python project initialized with Microsoft Agent Framework SDK and all required Azure SDKs**,
so that **I can begin implementing workflow agents on a solid foundation**.

## Acceptance Criteria

1. Python 3.10+ virtual environment is created and activated
2. `requirements.txt` includes Microsoft Agent Framework Python SDK, Azure Kusto Python SDK, Azure DevOps Python SDK (azure-devops), Azure Identity SDK, Azure Key Vault SDK
3. Project structure created with `/workflows`, `/agents`, `/shared`, `/tests`, `/config` directories
4. README.md documents environment setup, dependency installation, and project structure
5. `.gitignore` configured for Python projects (venv, __pycache__, .env, etc.)
6. Project successfully runs `python --version` and `pip list` showing all dependencies installed

## Notes

This is the foundational story that establishes the entire project structure. All subsequent development depends on this setup being complete and correct.

## Related Documents

- PRD: docs/prd.md (Epic 1, Story 1.1)
- Architecture: docs/architecture.md
