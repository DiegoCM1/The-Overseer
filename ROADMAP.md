# The Overseer — Roadmap

## Shared Infrastructure (Done)
- [x] `notifications/whatsapp.py` — `send_whatsapp_message(str)` via Twilio sandbox
- [ ] Switch to Meta Cloud API when system is functional end-to-end

---

## Feature 1: GH Streak Tracker

GitHub Actions triggers the script on push or schedule. It checks commits, runs them through AI, and sends a WhatsApp message.

### Flow
```
GitHub Actions → main.py → github/client.py (PushEvent)
                         → ai/graph.py (LangGraph → message string)
                         → notifications/whatsapp.py (send to phone)
```

### Status
- [x] `schemas.py` — `Commit` and `PushEvent` models
- [x] `notifications/whatsapp.py` — WA notification layer
- [ ] `github/client.py` — parse GitHub event payload into `PushEvent`
- [ ] `ai/graph.py` — LangGraph node: takes `PushEvent`, returns message string (via OpenRouter)
- [ ] `ai/prompts.py` — prompt templates
- [ ] `main.py` — orchestrator: wires client → AI → notification
- [ ] GitHub Actions workflow — on push + scheduled (10am, 6pm, 11pm)

---

## Feature 2: Activity Tracker (The Overseer)

Monitors browser activity in real time. Detects distractions, roasts you via WhatsApp.

### Flow
```
subprocess polling (AppleScript) → LangGraph brain (stateful, escalating roasts)
                                 → notifications/whatsapp.py
```

### Status
- [x] `tracker/monitor.py` — browser polling exists
- [ ] LangGraph stateful graph — remembers distraction duration, escalates roasts
- [ ] FastAPI layer — background tasks, async
- [ ] Next.js dashboard — blacklist management, shame stats

---

## WA Delivery Fix (Blocked — revisit after system works)
- Twilio sandbox: 5 msg/day limit, unreliable international delivery
- Fix options: Twilio paid number (~$1/mo) or Meta Cloud API (free, needs business setup)
