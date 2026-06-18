- If a big tool ecosystem, you can use tool_search which will load all tools only when necessary, saving tokens and everything
- We define tools before creating the agent, we test tools on isolation, this way we can debug easier since there are less moving parts

---

- A client is a wrapper that allows you to have http communication without you having to wire it all by yourself:  --- client = OpenAI(base_url=..., api_key=...) ---
- Instantiating is the concept that refers to create an object from a class
- A class is a template that groups data + behaviour together
- Reasoning, Tool calls, Actual response text from the LLM - All of them stay in the conversation, it is important to append their outputs so the LLM can 'remember them' in the next turn