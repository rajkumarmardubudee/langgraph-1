
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# --------------------------------------------------
# 1. Shared state used by the parent graph
# --------------------------------------------------

class KYCState(TypedDict):
    question: str
    evidence: list[str]
    analysis: str
    review: str
    next_step: str


# --------------------------------------------------
# 2. Simulated enterprise knowledge base
# --------------------------------------------------

KNOWLEDGE_BASE = [
    "The legacy KYC application uses Java and Struts.",
    "Business logic currently resides in Struts Action classes.",
    "The legacy application runs on IBM WebSphere.",
    "Customer information is stored in Mainframe DB2.",
    "The target architecture moves business logic to Spring Boot services.",
    "Angular is the target frontend for the modernization."
]


# --------------------------------------------------
# 3. RAG specialist agent
# --------------------------------------------------

def rag_agent(state: KYCState):
    print("\n[RAG Agent] Retrieving relevant evidence...")

    query_words = set(state["question"].lower().split())

    # Simple keyword matching for this learning example.
    scored = []

    for document in KNOWLEDGE_BASE:
        words = set(document.lower().replace(".", "").split())
        score = len(query_words & words)

        if score > 0:
            scored.append((score, document))

    scored.sort(key=lambda item: item[0], reverse=True)

    evidence = [document for _, document in scored[:5]]

    # Include target architecture facts for modernization questions.
    if "modernization" in state["question"].lower():
        for document in KNOWLEDGE_BASE:
            if (
                "target architecture" in document.lower()
                or "target frontend" in document.lower()
            ):
                if document not in evidence:
                    evidence.append(document)

    print(f"[RAG Agent] Retrieved {len(evidence)} facts.")

    return {"evidence": evidence}


# --------------------------------------------------
# 4. Analysis subgraph
# --------------------------------------------------

class AnalysisState(TypedDict):
    question: str
    evidence: list[str]
    analysis: str


def analyze_architecture(state: AnalysisState):
    print("\n[Analysis Agent] Analyzing architecture...")

    evidence_text = "\n".join(
        f"- {item}" for item in state["evidence"]
    )

    analysis = (
        "Recommended modernization approach:\n"
        "1. Move business logic from Struts Action classes "
        "into Spring Boot services.\n"
        "2. Introduce REST APIs between the frontend and backend.\n"
        "3. Migrate the frontend to Angular incrementally.\n"
        "4. Retain Mainframe DB2 initially to reduce migration risk.\n"
        "5. Validate existing business behavior with regression tests.\n\n"
        "Retrieved evidence:\n"
        f"{evidence_text}"
    )

    return {"analysis": analysis}


def check_migration_risks(state: AnalysisState):
    print("[Analysis Subgraph] Checking migration considerations...")

    analysis = state["analysis"]

    if "regression tests" not in analysis.lower():
        analysis += "\n6. Add regression testing before each migration release."

    return {"analysis": analysis}


analysis_builder = StateGraph(AnalysisState)

analysis_builder.add_node("analyze", analyze_architecture)
analysis_builder.add_node("risk_check", check_migration_risks)

analysis_builder.add_edge(START, "analyze")
analysis_builder.add_edge("analyze", "risk_check")
analysis_builder.add_edge("risk_check", END)

analysis_subgraph = analysis_builder.compile()


# --------------------------------------------------
# 5. Review specialist agent
# --------------------------------------------------

def review_agent(state: KYCState):
    print("\n[Review Agent] Reviewing the recommendation...")

    analysis = state["analysis"].lower()

    required_topics = [
        "spring boot",
        "angular",
        "db2",
        "regression tests"
    ]

    missing = [
        topic
        for topic in required_topics
        if topic not in analysis
    ]

    if missing:
        review = (
            "Review incomplete. Missing topics: "
            + ", ".join(missing)
        )
    else:
        review = (
            "Review passed: Spring Boot, Angular, DB2 retention, "
            "and regression testing are covered."
        )

    print("[Review Agent]", review)

    return {"review": review}


# --------------------------------------------------
# 6. Supervisor
# --------------------------------------------------

def supervisor(state: KYCState):
    if not state["evidence"]:
        next_step = "retrieve"
    elif not state["analysis"]:
        next_step = "analyze"
    elif not state["review"]:
        next_step = "review"
    else:
        next_step = "finish"

    print(f"\n[Supervisor] Next step: {next_step}")

    return {"next_step": next_step}


def route_supervisor(state: KYCState):
    return state["next_step"]


# --------------------------------------------------
# 7. Build the parent graph
# --------------------------------------------------

builder = StateGraph(KYCState)

builder.add_node("supervisor", supervisor)
builder.add_node("retrieve", rag_agent)

# A compiled graph can be used as a node in its parent graph.
builder.add_node("analysis", analysis_subgraph)

builder.add_node("review", review_agent)

builder.add_edge(START, "supervisor")

builder.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {
        "retrieve": "retrieve",
        "analyze": "analysis",
        "review": "review",
        "finish": END
    }
)

# Return control to the supervisor after each specialist.
builder.add_edge("retrieve", "supervisor")
builder.add_edge("analysis", "supervisor")
builder.add_edge("review", "supervisor")

graph = builder.compile()


# --------------------------------------------------
# 8. Run the workflow
# --------------------------------------------------

result = graph.invoke({
    "question": (
        "How should we approach modernization "
        "of the legacy KYC application?"
    ),
    "evidence": [],
    "analysis": "",
    "review": "",
    "next_step": ""
})

print("\n" + "=" * 55)
print("FINAL RESULT")
print("=" * 55)

print("\nQUESTION:")
print(result["question"])

print("\nEVIDENCE:")
for item in result["evidence"]:
    print("-", item)

print("\nANALYSIS:")
print(result["analysis"])

print("\nREVIEW:")
print(result["review"])
