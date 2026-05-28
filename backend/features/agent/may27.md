REDUCERS
    - Reducers are applied directly into the state, in the same file
    - To apply reducers you use import Annotated from typing (stdlib, not langgraph), the pattern is Annotated[<type>, <reducer>]
    - A state defined with no reducers will

StateGraph
    - Compiling your graph is a necessary step: checks for errors, orphaned nodes, etc
    - Compiling returns a new Object: CompiledStateGraph which can be executed, before that, its impossible to run the graph: graph = graphbuilder.compile(...)

EDGES
    - Edges go inside graph.py (The StateGraph)
    - Edges follow this pattern:  add_edge[<"node_name">, <"node name">]

MESSAGES IN GRAPH
    - Use -add_messages- when making an agent remember, instead of simply using -operator.add-