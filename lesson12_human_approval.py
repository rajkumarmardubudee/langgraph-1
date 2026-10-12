from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

# 1. Define graph state
class KYCState(TypedDict):
    case_id: str
    proposed_action: str
    decision: str
    execution_result: str


# 2. Prepare the proposed action
def propose_action(state: KYCState):
    print("\nPreparing proposed KYC action...")

    return {
        "proposed_action": (
            f"Flag case {state['case_id']} "
            "for enhanced due diligence"
        )
    }


# 3. Pause and request human approval
def request_approval(state: KYCState):
    # Keep side effects out of this node before interrupt().
    # LangGraph may re-run the node when it resumes.
    decision = interrupt({
        "message": "Human approval required",
        "case_id": state["case_id"],
        "proposed_action": state["proposed_action"],
        "allowed_decisions": ["approve", "reject"]
    })

    return {"decision": decision}

# 4. Route based on the human's decision
def route_after_approval(state: KYCState):
    if state["decision"] == "approve":
        return "execute"

    return "reject"  

# 5. Simulate executing the approved action
def execute_action(state: KYCState):
    print("\nExecuting approved action...")

    return {
        "execution_result": (
            f"SIMULATED: {state['proposed_action']}"
        )
    }

# 6. Handle rejection
def reject_action(state: KYCState):
    print("\nAction rejected.")

    return {
        "execution_result": (
            f"NOT EXECUTED: {state['proposed_action']}"
        )
    }

# 7. Build the graph
builder = StateGraph(KYCState)

builder.add_node("propose", propose_action)
builder.add_node("approval", request_approval)
builder.add_node("execute", execute_action)
builder.add_node("reject", reject_action)

builder.add_edge(START, "propose")
builder.add_edge("propose", "approval")

builder.add_conditional_edges(
    "approval",
    route_after_approval,
    {
        "execute": "execute",
        "reject": "reject"
    }
)

builder.add_edge("execute", END)
builder.add_edge("reject", END)

# 8. Compile with a checkpointer
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# 9. Give this workflow a stable thread ID
config = {
    "configurable": {
        "thread_id": "kyc-case-1001"
    }
}


# 10. Start the graph; it pauses at interrupt()
print("Starting KYC approval workflow...")

paused_result = graph.invoke(
    {
        "case_id": "KYC-1002",
        "proposed_action": "",
        "decision": "",
        "execution_result": ""
    },
    config=config
)


# 11. Display the interruption payload
interrupts = paused_result.get("__interrupt__", ())

if not interrupts:
    raise RuntimeError("Expected the graph to pause for approval.")

print("\nApproval request:")
print(interrupts[0].value)


# 12. Collect a human decision
decision = input(
    "\nEnter decision (approve/reject): "
).strip().lower()

while decision not in {"approve", "reject"}:
    decision = input(
        "Invalid decision. Enter approve or reject: "
    ).strip().lower()

# 13. Resume the same graph using the same thread ID
print("\nResuming workflow...")

final_result = graph.invoke(
    Command(resume=decision),
    config=config
)

# 14. Display the final state
print("\nFinal result:")
print("Case ID:", final_result["case_id"])
print("Decision:", final_result["decision"])
print("Execution:", final_result["execution_result"])
