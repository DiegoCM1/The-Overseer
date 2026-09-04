# The Overseer

One agent, built on Google ADK, running locally.

## Scope

Build a working local agent with 2 tools. Nothing else.

WhatsApp delivery and cloud deployment are ideas for later, not part of this.

## Status

| | |
|---|---|
| Python 3.12 venv | done |
| FastAPI boots (`GET /health`) | done |
| `google-adk` installed | done |
| `agent.py` loads (`crazy_assistant`, gemini-3.6-flash) | done |
| `GOOGLE_API_KEY` in `backend/.env` | done |
| Agent replies in `adk web` | done |
| Tools | 0 |

## Plan

1. Add two tools: `save_note(text)` (write) and `list_notes()` (read), backed by a local JSON file.

## Run

```bash
# API
cd backend && fastapi dev main.py

# Agent UI
cd backend && adk web

# Agent CLI
cd backend && adk run path_to_agent_folder
```
