import json
from openai import OpenAI
from features.agent.tools import tools, get_current_datetime, do_math
from core.config import settings

# Start client, use OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=settings.OPENROUTER_API_KEY
)



# Then we create a list of inputs that contains dictionaries, one per input
input_list = [
    { 
        "role": "user",
        "content": "This is my first prompt, tell me the current time in Portugal"
    }
]

print(f"This is the input: {input_list}")

# Invoke llm and save response
response = client.responses.create(
    model="deepseek/deepseek-v4-flash", # Using a model from openrouter
    tools=tools, # Load tools to model
    input=input_list # Sending the input to the model
)

print(f"This is the response: {response}")
