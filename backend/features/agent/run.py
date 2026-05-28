from pprint import pprint
from features.agent.graph import graph
from langchain.messages import HumanMessage

# Builds a starting state that will be tested
initial_state = {
    "messages": [HumanMessage("Hi")],
    "another_field": 69
}


# INVOKE / RUN THE GRAPH 
result = graph.invoke(initial_state)
pprint(result)