# Twilio WhatsApp: which sends need approved templates

## The rule

WhatsApp splits outbound messages into two kinds:

- **Session replies.** When *the user* messages you, a 24-hour window opens. Inside
  it you may send free-form text — arbitrary strings, including LLM-written copy.
- **Business-initiated messages.** Everything else. These **always** require a
  pre-approved template, and a template is a fixed body with numbered
  placeholders (`{{1}}`, `{{2}}`) that you fill at send time.

The window is opened **only by an inbound user message**. Sending a template does
*not* open one. If Diego never replies, every message to him is business-initiated
forever.

Approval takes between 5 minutes and 24 hours.

## The consequence for this codebase

**`features/enforcement/messages.py` generates free-form LLM copy. That copy is
illegal in a business-initiated message.** You cannot put model output in a
template body — the body is fixed at approval time and only the variables change.

This does not break the design principle (the LLM still decides nothing), but it
does mean the scheduled sends must move from `messages.create(body=...)` to a
Content API template send with variables. The LLM path remains valid for session
replies only.

## Which sends need a template

| # | Send | Initiated by | 24h window open? | Template |
|---|------|--------------|------------------|----------|
| 1 | 13:30 reminder → Diego | us | **No** — he hasn't messaged; that is *why* we are reminding | **REQUIRED** |
| 2 | 14:00 verdict FAIL → Diego | us | **No** — he posted nothing, so he sent nothing | **REQUIRED** |
| 3 | 14:00 verdict FAIL → Daniel | us | **No** — Daniel rarely initiates | **REQUIRED** |
| 4 | Daily heartbeat → Daniel | us | **No** — always business-initiated | **REQUIRED** |
| 5 | Debt claimed → Diego | us | **No** — Daniel messaged, not Diego | **REQUIRED** |
| 6 | "✅ Logged" ack → Diego | reply | **Yes** — he just sent the URL | not needed |
| 7 | "⚠️ bad link" → Diego | reply | **Yes** | not needed |
| 8 | "Already logged" → Diego | reply | **Yes** | not needed |
| 9 | Debt claim confirmation → Daniel | reply | **Yes** — he just sent `págame` | not needed |

**Five templates.** Rows 6–9 keep the LLM/free-form path.

Note the asymmetry in row 5: Daniel's confirmation is a session reply, but the same
event's notice to Diego is business-initiated, because the window belongs to the
person who messaged.

## Templates to submit

All five are `UTILITY` — transactional updates about an existing agreement, not
marketing. Getting recategorised as `MARKETING` changes pricing and raises the
rejection risk, so keep promotional language out of the bodies.

Variables must be actual variables. Do not bake the streak number or the amount
into the fixed body; WhatsApp rejects templates that look like they are dodging
variable substitution, and a hardcoded number would go stale.

### 1. `overseer_deadline_reminder`
```
Recordatorio: quedan {{1}} minutos para las 2:00 PM y no hay publicación registrada. Envía el enlace o cuenta como incumplimiento.
```
`{{1}}` = minutes remaining.

### 2. `overseer_verdict_fail_diego`
```
No se registró publicación antes de las 2:00 PM del {{1}}. Deuda: {{2}} MXN. Racha reiniciada desde {{3}} a 0.
```
`{{1}}` = date, `{{2}}` = amount, `{{3}}` = streak lost.

### 3. `overseer_verdict_fail_daniel`
```
Diego no publicó antes de las 2:00 PM del {{1}}. Te debe {{2}} MXN. Responde "págame" en las próximas 24 horas para reclamar.
```

### 4. `overseer_daily_heartbeat`
```
Reporte diario del {{1}}: la racha actual de Diego es de {{2}} día(s).
```
This one is load-bearing — it is the out-of-band replica Diego cannot rewrite. If
it is rejected, the integrity story weakens, so submit it first.

### 5. `overseer_debt_claimed_diego`
```
Daniel reclamó la deuda de {{1}} MXN correspondiente al {{2}}.
```

## How to submit

Two calls per template — create the content, then request approval.

```bash
# 1. Create
curl -X POST https://content.twilio.com/v1/Content \
  -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "friendly_name": "overseer_daily_heartbeat",
    "language": "es_MX",
    "variables": {"1": "2026-08-01", "2": "12"},
    "types": {
      "twilio/text": {
        "body": "Reporte diario del {{1}}: la racha actual de Diego es de {{2}} día(s)."
      }
    }
  }'
# -> returns a ContentSid, HXxxxxxxxx

# 2. Submit for WhatsApp approval
curl -X POST "https://content.twilio.com/v1/Content/HXxxxxxxxx/ApprovalRequests/whatsapp" \
  -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name": "overseer_daily_heartbeat", "category": "UTILITY"}'
```

Poll approval status, then send by `ContentSid` with `ContentVariables` instead of
`body`. Store the five SIDs in env vars.

## The sandbox will not work for this

The Twilio WhatsApp **sandbox** is not a substitute for a production sender:

- Participants must re-join by messaging the join code after a period of
  inactivity (Twilio documents this as a recurring re-join requirement — treat 72
  hours as the working assumption and verify against your console). A system whose
  whole job is to send an unwelcome message every day at 2 PM will silently stop
  delivering the moment a participant lapses.
- Sandbox numbers are shared and rate-limited.
- **A silently undelivered verdict is worth 200 MXN to Diego.** That is exactly
  the incentive this project exists to remove, so the sandbox is not merely
  inconvenient here — it is a hole in the enforcement.

Before this system is trusted with real money:

1. Register a WhatsApp Business sender (Meta Business verification required).
2. Get all five templates approved.
3. Switch the scheduled sends to `ContentSid` + `ContentVariables`.
4. Confirm `HEALTHCHECKS_URL` is set and that healthchecks.io notifies **Daniel**,
   not Diego. A liveness alarm that only reaches the person with an incentive to
   ignore it is not a control.

## Open item

The scheduled sends in `features/enforcement/service.py` currently call
`send_whatsapp(body=...)`. They will fail for business-initiated messages once off
the sandbox. Migrating them to template sends is the next piece of work; the free-form
LLM path stays for the four session replies.
