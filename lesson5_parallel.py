from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END


# 1. Define shared state
class WorkflowState(TypedDict):
    findings: Annotated[list[str], add]
    summary: str


# 2. Research node
def research_node(state: WorkflowState):
    print("Research started...")

    return {
        "findings": ["Research completed"]
    }


# 3. Security node
def security_node(state: WorkflowState):
    print("Security check started...")

    return {
        "findings": ["Security check completed"]
    }


# 4. Combine results
def combine_node(state: WorkflowState):
    print("Combining results...")

    return {
        "summary": (
            f"Completed {len(state['findings'])} tasks"
        )
    }


# 5. Create graph
builder = StateGraph(WorkflowState)

builder.add_node("research", research_node)
builder.add_node("security", security_node)
builder.add_node("combine", combine_node)


# 6. Create parallel branches
builder.add_edge(START, "research")
builder.add_edge(START, "security")

# Wait for both branches before combining
builder.add_edge(["research", "security"], "combine")


builder.add_edge("combine", END)


# 7. Compile and execute
graph = builder.compile()

output = graph.invoke({
    "findings": [],
    "summary": ""
})

print("\nFinal output:", output)