from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from typing import Annotated

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages] # Reducer
    another_field: int