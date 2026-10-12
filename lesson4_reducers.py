from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END

class WorkflowState(TypedDict):
    messages: Annotated[list[str], add]


# 2. Define nodes
def receive_message(state: WorkflowState):
    return {
        "messages": ["Message received"]
    }


def process_message(state: WorkflowState):
    return {
        "messages": ["Message processed"]
    }


def finish_workflow(state: WorkflowState):
    return {
        "messages": ["Workflow completed"]
    }

builder = StateGraph(WorkflowState)

builder.add_node("receive", receive_message)
builder.add_node("process", process_message)
builder.add_node("finish", finish_workflow)

builder.add_edge(START, "receive")
builder.add_edge("receive", "process")
builder.add_edge("process", "finish")
builder.add_edge("finish", END)

# 4. Compile and execute
graph = builder.compile()

output = graph.invoke({
    "messages": ["Workflow started"]
})

print(output["messages"])