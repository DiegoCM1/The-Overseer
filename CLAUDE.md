# The Overseer

## What this is

An accountability enforcement system for a real bet between Diego and his
brother Daniel. It is NOT a task nagger and NOT a browsing monitor.

## The contract it enforces

- Obligation: 1 video published on X per weekday (Mon-Fri)
- Deadline: 2:00 PM America/Mexico_City
- Miss = 200 MXN owed, Diego -> Daniel
- Streak: +1 per CALENDAR day (Mon-Sun). Any weekday miss resets to 0.
  Weekends require no post but do advance the streak.
- 30 consecutive days clean = Daniel does Diego's chores for 3 days
- No exceptions. Illness, travel, technical failure all count as misses.

## Design principle (this dictates every decision)

The adversary is the author. Diego owns this code and has a financial
incentive to find loopholes. The goal is not to make cheating impossible —
it is to make every cheat require a deliberate, visible act. Cheating must
never be a side effect of a bug or of laziness.

Consequences that are NOT negotiable:

- DEFAULT STATE IS FAILURE. Absence of evidence is a miss.
- The verdict function is pure and deterministic: (evidence, now) -> PASS|FAIL.
  NO LLM in the verdict path, ever. An LLM verdict is a judge that can be
  argued with.
- Streak is DERIVED by folding an append-only event log. It is never stored
  as a mutable integer. There is no endpoint, script, or admin path that
  writes a streak value.
- The ONLY way a fact enters the system is Diego submitting a post URL.
- A dead server must be louder than a working one. Liveness is verified by
  an external service Diego does not control.
- LLM output is confined to message copy. It decides nothing.

## What is out of scope right now

LangGraph, the AppleScript browser monitor, the Next.js dashboard, phone-call
escalation. Do not add them. A minimal graph exists on the `basic-mvp` branch
for later.

---

## Current state of the code (read this before planning work)

The section above describes the system being built. It is **not** what the code
does today. Do not confuse the two — that confusion is exactly what made the
previous CLAUDE.md useless.

What exists today, in `backend/`:

- A scheduled poller. APScheduler fires `features/monitor/service.tick()` every
  `POLL_MINUTES`, which GETs `{LIFEOS_API_URL}/api/v1/misses` from **life-os, a
  separate service in a different repo**, and escalates anything overdue.
- A three-level escalation ladder (`features/monitor/escalation.py`) — pure,
  I/O-free, quiet-hours aware. This is the closest thing to a verdict function
  that exists, and it is already the right shape: deterministic, no LLM.
- Idempotent delivery. One row per `(log_date, goal_id, level)` in
  `notifications`, enforced by a DB unique constraint, so a step never re-fires.
- Twilio WhatsApp delivery, plus voice/TwiML that is built but off
  (`ENABLE_CALLS=False`).
- LLM message copy via OpenRouter/DeepSeek, with a template fallback when the
  call fails. Already correctly confined to copy — it decides nothing.
- 29 tests over escalation, dedupe, quiet hours, and delivery-failure handling.

The gap between this and the contract above:

- There is **no post-URL submission path**. Facts currently enter the system
  from life-os, not from Diego submitting evidence. This is the single biggest
  divergence from the design principle.
- There is **no event log and no derived streak**. Nothing folds an append-only
  log.
- There is **no external liveness check**. If this process dies, nothing notices.
- The 2 PM weekday obligation and the 200 MXN / 30-day rules are not modelled
  anywhere in code.

## Commands

```bash
cd backend
source venv/bin/activate

alembic upgrade head            # apply schema. NOT create_all() — that is gone.
alembic revision --autogenerate -m "what changed"

uvicorn main:app --reload       # http://127.0.0.1:8000  (docs at /docs)
pytest                          # 29 tests, sqlite-backed, no network

curl -X POST localhost:8000/debug/tick   # fire a poll now (APP_ENV=dev only)
```

Config lives in one place: `core/config.py`. Copy `.env.example` to `.env`.
Missing required vars raise at import — the app refuses to boot rather than
half-run.

## Working agreement

- Hands on keyboard = Diego. Coach through the implementation, ask leading
  questions first; give the smallest hint that unblocks, not the full solution.
- Tie every explanation to the specific code being written. No generic lectures.
- Default to senior-level depth. Be blunt about hand-waving or faked
  understanding.
- If a concept is bigger than one 90-minute block, say so and split it.
