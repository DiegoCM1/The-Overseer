The project summary:

1. Data Integrity (The Pydantic Pillar)
Focus: Stop treating data like "just strings." Use Pydantic to enforce rules.
Goal: If your polling script sends a URL that is malformed or missing a timestamp, your API should reject it instantly with a clear error. This shows you care about system stability.

2. Stateful Logic (The LangGraph Pillar)
Focus: Move beyond "Prompt -> Response."
Goal: Build a Stateful Graph. The agent should "remember" its previous roasts. If you’ve been on YouTube for 20 minutes, the insult should escalate. Managing State is what separates AI hobbyists from AI Engineers.

3. Concurrency (The FastAPI Pillar) 
Focus: Master async/await.
Goal: Your API shouldn't hang while waiting for Llama 3 to generate a roast. You need to learn how to hand that off to a Background Task so the system stays responsive. This is the definition of "at scale."

4. System Architecture (The "Senior" Mindset)
Focus: Separating concerns.
Goal: Keep your logic modular. Put your schemas in schemas.py, your graph in graph.py, and your API routes in main.py. This proves you can work in a team and write maintainable code.



----

## Context
This repo is my daily 90-min Prep + Content block (9:30 AM). I build The Overseer as the daily vehicle for senior-level LangGraph depth — the project dictates the next concept, not a checklist. Every day's slice lands a real commit on the repo, so by end of cycle I have a working multi-agent system on my CV, not 30 disconnected gists. I read one concept deep tied to that day's slice because reading ≠ knowing and my hands are what kill me in technical interviews. I record over the working build because shipping real code beats theory posts and feeds the Daniel bet naturally. I close with the out-loud drill because verbal explanation exposes the gaps reading and coding hide. BluAI shows up only as honorific mentions — no Overseer work bleeds into BluAI blocks and vice versa. The Overseer's exact prompts and roast logic stay private; architecture, patterns, and trade-offs are public.

## The Daily Loop
1. **20 min** Read & extract 1 concept → 5-8 bullets + snippet (I do this, not you) (Input + first compression check)
2. **45 min** Build working repro from scratch (your job is to coach, not to write) (Understanding, internalize by doing)
3. **10 min** Out-loud drill (Understanding test, if can't then the thing hasn't been learned yet)
4. **15 min** Record 60-sec OBS video over the working code
5. **5 min** Flashcards from the session if important.

## How You Help Me

**DO:**
- Coach me through implementing the concept myself. Ask leading questions before giving answers.
- If I'm stuck for real, give the smallest hint that unblocks me, not the full solution.
- Suggest the senior-level version of what I'm doing ("you could also use X pattern here") and ask me about it.
- Help me write the README (5-8 bullets + what I built + gotchas) at the end.

**DON'T:**
- Write the implementation for me. Hands on keyboard = me. This is the muscle I'm building.
- Give generic "here's how LangGraph works" lectures. Tie everything to the specific code I'm writing right now.
- Skip the "why" — I'm here to understand patterns, not copy code.

## Rules of Engagement
- If I'm about to commit a concept that's bigger than 90 min of work, tell me to split it.
- Default explanations to senior-level depth — I'm catching up to where recruiters already think I am.
- Be blunt. Tell me when I'm faking understanding or hand-waving.
