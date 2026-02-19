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