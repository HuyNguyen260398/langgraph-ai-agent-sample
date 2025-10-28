from typing import Annotated
from dotenv import load_dotenv

from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command


load_dotenv()
llm = init_chat_model("anthropic:claude-3-haiku-20240307")


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    print(f"🤔 Assistant requesting human help: {query}")
    # For testing purposes, simulate a human response
    human_response = "For building an AI agent, I recommend starting with LangGraph for orchestration, using a strong LLM like Claude, implementing tools for specific capabilities, and ensuring proper state management. Focus on clear tool definitions, robust error handling, and iterative testing."
    print(f"✅ Human provided: {human_response}")
    return human_response


tool = TavilySearch(max_results=2)
tools = [tool, human_assistance]
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    assert len(message.tool_calls) <= 1
    return {"messages": [message]}


graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)

graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "1"}}


def stream_graph_updates(user_input: str):
    print(f"User: {user_input}")
    for event in graph.stream(
        {"messages": [{"role": "user", "content": user_input}]}, config=config
    ):
        for value in event.values():
            if "messages" in value:
                message = value["messages"][-1]
                # Handle regular text responses
                if hasattr(message, "content") and message.content:
                    # Skip tool call messages that just show raw tool data
                    if not (hasattr(message, "tool_calls") and message.tool_calls):
                        print("Assistant:", message.content)
                # Handle tool calls
                elif hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        if tool_call["name"] == "tavily_search_results_json":
                            print(
                                f"🔍 Searching for: {tool_call['args'].get('query', 'information')}"
                            )


if __name__ == "__main__":
    # Test the human assistance functionality
    stream_graph_updates(
        "I need some expert guidance for building an AI agent. Could you request assistance for me?"
    )
    print("\n" + "=" * 50 + "\n")

    # Test a search functionality
    stream_graph_updates("What are the latest developments in AI agents?")
    print("\n" + "=" * 50 + "\n")

    # Test a simple conversation
    stream_graph_updates("Hello, how are you?")
