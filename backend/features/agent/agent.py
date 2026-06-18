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
messages = [
    { 
        "role": "user",
        "content": "Tell me the current time in Tokyo, also, tell me what's the result of 8*8+5+31-99"
    }
]

print(f"This is the input: {messages}")


finished = False
isToolPending = False

while not finished:
    isToolPending = False

    # Invoke llm and save response
    response = client.responses.create(
        model="deepseek/deepseek-v4-flash", # Using a model from openrouter
        tools=tools, # Load tools to model
        input=messages # Sending the input to the model
    )

    # Save tool call outputs for next requests
    messages += response.output

    for item in response.output:
        if item.type == "function_call":
            # Flag for tools being pending
            isToolPending = True

            # Iterate over each tool
            if item.name == "get_current_datetime":
                timezone = json.loads(item.arguments)["timezone"]
                time_result = get_current_datetime(timezone)        
                # Append tool results
                messages.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": time_result
                })
                print("Executed get_current_datetime")


            if item.name == "do_math":
                expression = json.loads(item.arguments)["expression"]
                result = do_math(expression)
                # Append tool results
                messages.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": result
                })
                print("Executed do_math")

    if not isToolPending:
        finished = True

for item in response.output:
    if item.type == "reasoning":
        print(f"""--Reasoning {item.content[0].text} --Reasoning--""")
    if item.type == "message":
        print(item.content[0].text)


