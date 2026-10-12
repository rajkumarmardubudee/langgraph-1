from typing import TypedDict
from langgraph.graph import StateGraph, START, END

#1. Define shared state
class WorkflowState(TypedDict):
    result: str
    attempts: str
    is_valid: bool

#2. Generate a greeting

def generate_greetings(state: WorkflowState):
    attempt = state["attempts"] + 1
    print(f"Generating greeting: attempt {attempt}")

    # Simulate a failed first attempt
    if attempt == 1:
        greeting = "Hi, Raj"
    else:
        greeting = "Hello, Raj"

    return {
        "result": greeting,
        "attempts": attempt
    }

# 3. Validate the greeting
def validate_greeting(state: WorkflowState):
    print(f"Validating: {state['result']}")

    return {
        "is_valid": state["result"].startswith("Hello,")
    }

# 4. Decide whether to retry
def route_after_validation(state: WorkflowState):
    if state["is_valid"]:
        return "success"

    if state["attempts"] >= 3:
        return "failed"

    return "retry"

#5 Build the graph

builder = StateGraph(WorkflowState)

builder.add_node("generate", generate_greetings)
builder.add_node("validate", validate_greeting)

builder.add_edge(START, "generate")
builder.add_edge("generate", "validate")

builder.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "success": END,
        "failed": END,
        "retry": "generate"


    }
)

graph = builder.compile()

output = graph.invoke({
    "result": "",
    "attempts": 0,
    "is_valid": False
})

print("\nFinal output:", output)