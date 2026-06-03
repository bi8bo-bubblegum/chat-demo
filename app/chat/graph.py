from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.chat.nodes import chat_node
from app.chat.state import ChatState


def build_graph(checkpointer: AsyncPostgresSaver):
    graph = StateGraph(ChatState)
    graph.add_node('chat_node', chat_node)
    graph.add_edge(START, 'chat_node')
    graph.add_edge('chat_node', END)
    return graph.compile(checkpointer=checkpointer)