# The Overseer

An accountability enforcement system for a real bet between two brothers.

**The contract:** one video published on X per weekday, by 2:00 PM
America/Mexico_City. A miss costs 200 MXN. 30 consecutive clean calendar days
wins three days of chores. Illness, travel and technical failure all count as
misses — there are no exceptions, because an exception is just a loophole with
a sympathetic name.

## Design principle

**The adversary is the author.** I own this code and I have a financial
incentive to find loopholes in it. The goal is not to make cheating impossible.
The goal is to make every cheat require a deliberate, visible act — never a side
effect of a bug or of laziness.

That single constraint decides the architecture:

| Rule | Why |
|---|---|
| Default state is failure | Absence of evidence is a miss. A crashed poller must not read as "nothing was due." |
| The verdict is a pure function `(evidence, now) -> PASS \| FAIL` | Deterministic and replayable. **No LLM in the verdict path, ever** — an LLM judge is a judge you can argue with. |
| Streak is *derived*, never stored | It is a fold over an append-only event log. No endpoint, script, or admin path writes a streak value, so there is nothing to quietly bump. |
| One way in | The only way a fact enters the system is by submitting a post URL. |
| A dead server is louder than a working one | Liveness is checked by an external service I do not control. |
| The LLM writes copy, nothing else | It phrases the message. It decides nothing. |

## What actually runs today

This is a work in progress, and the README is deliberately honest about the gap
between the design above and the code below.

```
APScheduler heartbeat (every POLL_MINUTES)
  └─ GET {LIFEOS_API_URL}/api/v1/misses        ← life-os: a SEPARATE service/repo
      └─ asyncio.to_thread(_process)            ← blocking work off the event loop
          ├─ escalation.desired_level()         ← pure, deterministic, no LLM
          ├─ dedupe against `notifications`     ← unique (log_date, goal_id, level)
          ├─ messages.compose()                 ← LLM copy, template fallback
          └─ Twilio WhatsApp
```

**Working:**

- Three-level escalation ladder — pure, I/O-free, quiet-hours aware
  (`features/monitor/escalation.py`).
- Exactly-once delivery per escalation step, enforced by a DB unique constraint,
  so a restart or an overlapping tick cannot double-send.
- Delivery failures are *not* recorded, so the next poll retries the step.
- LLM copy via OpenRouter/DeepSeek with a template fallback on error or timeout.
- Twilio WhatsApp. Voice/TwiML is built but disabled (`ENABLE_CALLS=false`).
- 29 tests covering escalation levels, backfill, dedupe, quiet hours, and
  delivery failure. They run on SQLite and touch no network.

**Not built yet:**

- No post-URL submission endpoint. Facts currently arrive from life-os rather
  than from submitted evidence — the largest gap from the design principle.
- No append-only event log, and therefore no derived streak.
- No external liveness check. If this process dies, nothing currently notices.
- The 2 PM weekday obligation and the 200 MXN / 30-day rules are not yet
  modelled in code.

**Explicitly out of scope right now:** LangGraph, the AppleScript browser
monitor, the Next.js dashboard, phone-call escalation. A minimal LangGraph
reproduction lives on the `basic-mvp` branch for later.

## Stack

FastAPI · APScheduler · SQLAlchemy + Alembic · Supabase Postgres · Twilio ·
OpenRouter (DeepSeek)

## Running it

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

cp .env.example .env        # then fill it in — see the notes in that file

alembic upgrade head        # schema is owned by Alembic, not by create_all()
uvicorn main:app --reload   # http://127.0.0.1:8000  (docs at /docs)
pytest
```

`POST /debug/tick` fires a poll immediately instead of waiting for the
heartbeat. It is only registered when `APP_ENV=dev`.

### Database

Supabase Postgres, via the **session pooler** (port 5432). Not the transaction
pooler (6543) — it does not support prepared statements and Alembic misbehaves
against it. Not the direct connection either, which is IPv6-only without the
paid IPv4 add-on. `.env.example` spells this out.

Schema changes go through Alembic:

```bash
alembic revision --autogenerate -m "what changed"
alembic upgrade head
alembic downgrade -1
```

`Base.metadata.create_all()` was removed from the app lifespan: it was blocking
DDL on the event loop, and it could only ever CREATE, never ALTER, so any column
change drifted silently.

## Gotchas worth knowing

- **`Settings()` raises at import** if a required env var is missing. The app
  refuses to boot rather than half-run. That is intentional.
- **life-os is a separate repo.** This service is useless on its own; it is a
  consumer of that API, and the payload contract is currently unvalidated.
- **The engine sets `connect_timeout`, `pool_pre_ping` and `pool_recycle`.**
  Without the timeout an unreachable database hangs a tick indefinitely instead
  of failing loudly; the other two exist because a pooler drops idle connections.
- **Scheduler errors and missed runs are logged explicitly** with tracebacks.
  A silently dead job is this system's worst failure mode: the process stays up,
  health checks stay green, and nothing is ever sent.
- **RLS is enabled on `notifications`, with no policies.** Supabase serves the
  `public` schema over its Data API, so without this the idempotency ledger would
  be readable *and writable* by anyone holding the anon key — insert rows to
  suppress messages, delete rows to force duplicates. Deny-all is correct here:
  the app connects as `postgres`, which bypasses RLS. Any new table in `public`
  needs the same treatment.
