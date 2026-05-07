  You want an accountability agent. You define a task + a deadline. The agent monitors whether you've         
  completed that task by checking a data source (like a Notion page), and as the deadline approaches, it
  escalates its harassment — messages first, then calls. If you miss the deadline, it keeps going until you're
   done.          

  The core loop is:
  1. You define: task + completion criteria + deadline
  2. Agent polls/checks your progress against the source of truth (Notion page for now)                       
  3. Pre-deadline: sends WhatsApp reminders with increasing urgency                    
  4. Post-deadline: escalates to calls, blocks apps, whatever it takes         


## TECHNOLOGIES
FastAPI + LangGraph + APScheduler + PostgreSQL + Notion API + Twilio  