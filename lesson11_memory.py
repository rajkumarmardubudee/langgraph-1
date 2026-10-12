from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

# 1. Define graph state
class ChatState(TypedDict):
    user_input: str
    messages: Annotated[list[str], operator.add]

# 2. Define the chat node
def chat_node(state: ChatState):
    history = state.get("messages", [])
    user_input = state["user_input"]

    # Find the previous user message
    previous_user = next(
        (
            message
            for message in reversed(history)
            if message.startswith("User:")
        ),
        None
    )

    if previous_user:
        response = (
            f"I remember your previous message: "
            f"{previous_user[5:].strip()}"
        )
    else:
        response = "Hello! This is the beginning of our conversation."

    print("Assistant:", response)

    return {
        "messages": [
            f"User: {user_input}",
            f"Assistant: {response}"
        ]
    }


# 3. Build the graph
builder = StateGraph(ChatState)

builder.add_node("chat", chat_node)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)


# 4. Add the checkpointer
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)


# 5. Use the same thread ID for both messages
config = {
    "configurable": {
        "thread_id": "kyc-user-001"
    }
}

print("\n--- First interaction ---")

result1 = graph.invoke(
    {
        "user_input": "Our KYC application uses Java and Struts.",
        "messages": []
    },
    config=config
)


print("\n--- Second interaction ---")

result2 = graph.invoke(
    {
        "user_input": "What technology did I mention earlier?"
    },
    config=config
)

print("\n--- Saved conversation history ---")

for message in result2["messages"]:
    print(message)
