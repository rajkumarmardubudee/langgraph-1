from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# 1. Define shared state
class RAGState(TypedDict):
    question: str
    query: str
    context: list[str]
    relevant: bool
    attempts: int
    answer: str


# 2. Sample knowledge base
documents = [
    "Customer data is stored in Mainframe DB2.",
    "The legacy KYC application uses Java and Struts.",
    "IBM WebSphere hosts the legacy KYC application.",
    "The target architecture uses Spring Boot and Angular.",
    "Database connectivity uses JDBC and application configuration."
]


# 3. Configure the LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# 4. Retrieve documents using simple keyword matching
def retrieve(state: RAGState):
    print(f"\nRetrieval attempt: {state['attempts'] + 1}")
    print("Searching for:", state["query"])

    words = set(state["query"].lower().split())

    scored = []

    for document in documents:
        doc_words = set(document.lower().split())
        score = len(words & doc_words)

        if score > 0:
            scored.append((score, document))

    scored.sort(key=lambda item: item[0], reverse=True)

    return {
        "context": [doc for score, doc in scored[:3]],
        "attempts": state["attempts"] + 1
    }


# 5. Define structured output for relevance grading
class RelevanceGrade(BaseModel):
    relevant: bool = Field(
        description="True if the documents contain useful "
                    "information for answering the question"
    )


# 6. Grade the retrieved documents
grader = llm.with_structured_output(RelevanceGrade)


def grade_documents(state: RAGState):
    print("Grading retrieved documents...")

    if not state["context"]:
        return {"relevant": False}

    prompt = f"""
Determine whether the context contains useful evidence
to answer the user's question.

Question: {state['question']}

Context:
{chr(10).join(state['context'])}

Return relevant=true only if the context provides useful
information for answering the question.
"""

    result = grader.invoke(prompt)

    print("Documents relevant:", result.relevant)

    return {"relevant": result.relevant}


# 7. Rewrite the query when retrieval is unsuccessful
def rewrite_query(state: RAGState):
    print("Rewriting search query...")

    prompt = f"""
Rewrite the search query to improve document retrieval.

Original question: {state['question']}
Previous query: {state['query']}

Use important technical terms and likely synonyms.
Return only the rewritten search query.
"""

    response = llm.invoke(prompt)

    return {"query": response.content.strip()}


# 8. Generate the answer
def generate_answer(state: RAGState):
    print("Generating answer...")

    prompt = f"""
Answer the user's question using only the supplied context.
Do not invent unsupported technical details.
If the context is insufficient, say so.

Question: {state['question']}

Context:
{chr(10).join(state['context'])}
"""

    response = llm.invoke(prompt)

    return {"answer": response.content}


# 9. Handle unsuccessful retrieval
def no_answer(state: RAGState):
    return {
        "answer": (
            "I could not find sufficiently relevant information "
            "in the available documents after the permitted "
            "retrieval attempts."
        )
    }


# 10. Conditional routing
def route_after_grading(state: RAGState):
    if state["relevant"]:
        return "answer"

    if state["attempts"] >= 2:
        return "stop"

    return "rewrite"


# 11. Build the graph
builder = StateGraph(RAGState)

builder.add_node("retrieve", retrieve)
builder.add_node("grade", grade_documents)
builder.add_node("rewrite", rewrite_query)
builder.add_node("generate", generate_answer)
builder.add_node("no_answer", no_answer)

builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "grade")

builder.add_conditional_edges(
    "grade",
    route_after_grading,
    {
        "answer": "generate",
        "rewrite": "rewrite",
        "stop": "no_answer"
    }
)

builder.add_edge("rewrite", "retrieve")
builder.add_edge("generate", END)
builder.add_edge("no_answer", END)


# 12. Compile and execute
graph = builder.compile()

result = graph.invoke({
    "question": "Where is customer data stored?",
    "query": "customer data storage",
    "context": [],
    "relevant": False,
    "attempts": 0,
    "answer": ""
})

print("\nFinal answer:")
print(result["answer"])
print("\nTotal retrieval attempts:", result["attempts"])