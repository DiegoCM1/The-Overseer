

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