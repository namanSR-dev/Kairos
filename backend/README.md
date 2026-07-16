# Kairos Backend

The Python FastAPI backend engine for Project Kairos.

## Responsibilities
- AI Orchestration (Ollama / Gemini via Instructor)
- SQLite Database Management (SQLModel)
- NLP Parsing & HTML Stripping
- Local Vector Embeddings (SentenceTransformers)

## Getting Started
Uses `uv` for dependency management.
```bash
uv sync
uv run fastapi dev src/main.py
```
