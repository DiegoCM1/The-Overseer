# The-Overseer
The Summary: What it Does
The Overseer monitors your browser activity in real-time. If it detects you’re wasting time (Reels, YouTube, etc.) when you should be in "Laptop Mode" or "Deep Work," it executes a "Corrective Action."
Detection: It identifies when you stray from your "Blacklist."
Social Shame: It sends you insults or "reverse psychology" roasts via WhatsApp.
Accountability: It tracks your "Shame Stats" on a dashboard for you to see how much of a "villain" your distractions are.

## Stack:
LangGraph
FastAPI + Pydantic
Nextjs
TS

Tracking: subprocess

## How it works
1. The Eye (Dynamic Polling)
The Tech: Python + AppleScript.

The Action: It constantly "spies" on your active browser window. It pulls the URL and the window title to see exactly what you're looking at.

2. The Brain (LangGraph)
The Tech: LangGraph + Llama 3 (via OpenRouter).

The Action: This is the core state machine. It doesn't just see a URL; it understands context.

Stateful Logic: It remembers if you’ve been on a distraction for 2 minutes vs. 20 minutes.

Intelligence: It uses Llama 3 to generate personalized roasts based on your specific goals and failures.

3. The Mouth (Meta WhatsApp API)
The Tech: Meta’s Cloud API.

The Action: A direct line to your phone. When the Brain decides you need a kick in the ass, the Mouth sends the WhatsApp message. Because it’s WhatsApp, you can’t easily ignore it like a browser notification.

4. The Dashboard (Next.js + Tailwind)
The Tech: Modern Frontend stack. A place where you can modify the system prompt, allow/prohib using tools, see stats, define the black list, etc.

The Action: A clean, "elite" interface that displays your productivity metrics and blacklists. It’s where you face the data of your "Shame Stats" and manage what counts as a distraction.


## Considerations
- API Key will be hardcoded, for me to choose the best model, and if a user wants to use it, they can pay or get a free trial. In the future we'll add the feature of entering your own api key


## Next possible optimizations
-  Only execute the tracking/polling when chrome is open, not every wake moment of the laptop.


-----

GH Streak tracker

Stack:
Ntfy for notifications on phone
Widget Android for displaying streak
GitHub Actions for sending the data to our script containing the AI
AI langgraph analizing the diff on the commit done to check if its worthy or just a trashy commit, Using openrouter for free shit.
Endpoint sending decision from AI to db, and widget getting information from it or from the db itself.


[High Priority] The Sensor: Get a script that can accurately say "Yes/No" to "Did Diego commit today?"

[High Priority] The Mouth (ntfy): Connect that "Yes/No" to a simple notification. This is your immediate replacement for the Duolingo owl.

[Mid Priority] The Brain (LangGraph): Add the Llama 3 personality. Instead of "0 commits," it should say, "Your 741-day discipline is rotting, Diego. Fix the square." or What is the current streak, having personal info about me as well.

[Low Priority] The Eye (Custom Widget): For now, just pin the GitHub widget to your home screen. It’s 0 effort and 100% effective. ✅

---
Trigger 1: on push  → "You did it, you are amazing, keep the x stuff going"                                                 
  Trigger 2: scheduled → "If no commits, 3 messages per day, once 10 am, 6pm and 11pm Roast or
  remind accordingly"




    GitHub Actions triggers main.py
    → main.py calls GitHub API → gets commit diff
    → main.py passes diff to LangGraph (ai/graph.py)
    → LangGraph returns a message string
    → main.py passes string to ntfy.py
    → ntfy.py POSTs to ntfy.sh → Pixel gets notification

  main.py is the orchestrator. It calls the other modules. It doesn't contain the AI — it
   calls it.