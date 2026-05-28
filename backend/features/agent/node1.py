from features.agent.state import State
from langchain.messages import AIMessage

def node1(state: State):
    new_message = AIMessage("Hey, this is a message!")
    return {"messages": [new_message], "another_field": 96}