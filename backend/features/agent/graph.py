from langgraph.graph import START, END, StateGraph
from features.agent.node1 import node1
from features.agent.state import State

graph_builder = StateGraph(State) #Instantiate StateGraph

# Add nodes
graph_builder.add_node("node1", node1) #Referencing to node

# Edges
graph_builder.add_edge(START, "node1") # Starts the graph, the executes the node.
graph_builder.add_edge("node1", END) # After executing the node, it ends the graph

# Compile
graph = graph_builder.compile() # Outputs compiled graph