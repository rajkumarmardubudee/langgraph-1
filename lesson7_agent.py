from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition


# 1. Define a tool
@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers and return the result. """

    return a * b

tools = [multiply]


# 2. Configure the LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

llm_with_tools = llm.bind_tools(tools)

#3. Define the assistant node
def assistant(state: MessagesState):
    response = llm_with_tools.invoke(state["messages"])

    return {
        "messages": [response]
    }

#4. Create the graph

builder = StateGraph(MessagesState)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

# 5. Connect the nodes
builder.add_edge(START, "assistant")

# Route based on the LLM response

builder.add_conditional_edges(
    "assistant",
    tools_condition
)

# Return tool results to the LLM
builder.add_edge("tools", "assistant")

#6. Compile
graph = builder.compile()

#7. Invoke the agent

result = graph.invoke({
    "messages": [
        {
            "role": "user",
            "content": "What is your name"
        }
    ]

})

#8. Print the conversation

for message in result["messages"]:
    print(f"\n{message.type}: {message.content}")