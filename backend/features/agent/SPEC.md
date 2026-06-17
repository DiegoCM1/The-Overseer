# Overseer Agent — Bare Python MVP

## Goal
Build a working AI agent using only the OpenAI-compatible API (no LangChain, no LangGraph).
Understand the agentic loop from scratch before adding any framework on top.

## What We're Building
A single agent loop that can reason, call tools, and produce a final answer.

## Tools
| Tool | Purpose |
|------|---------|
| `get_current_time` | Returns current UTC datetime — no args needed |
| `calculator` | Evaluates a basic math expression — args: `expression: str` |

## Files
```
features/agent/
├── SPEC.md          ← this file
├── tools.py         ← tool functions (pure Python, no AI)
├── agent.py         ← the loop (LLM calls + tool dispatch)
└── run.py           ← entry point to test it
```

## The Loop (what we're implementing)
```
send messages to LLM
  → if LLM wants a tool: run it, append result, loop again
  → if LLM gives final answer: print and stop
```

## Why bare Python first
Feel the pain of manual state management and tool dispatch.
That pain is exactly what LangGraph solves — you'll know why every abstraction exists.

## Stack
- `openai` SDK (OpenAI-compatible, works with OpenRouter later via base_url swap)
- `python-dotenv` for env vars
- Zero other dependencies
