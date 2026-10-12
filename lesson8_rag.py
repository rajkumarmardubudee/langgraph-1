from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

#1. Define shared state
class RAGState(TypedDict):
    question: str
    context: list[str]
    answer: str

# 2. Our sample knowledge base
documents = [
    "The KYC application uses Java and Struts for its legacy web layer.",
    "The application uses IBM WebSphere as its application server.",
    "The application accesses customer data stored in Mainframe DB2.",
    "The target architecture uses Spring Boot and Angular."
]

# 3. Retrieve relevant documents
def retrieve(state: RAGState):
    print("Retrieving relevant documents...")

    question_words = set(
        state["question"].lower().replace("?", "").split()
    )

    # Simple keyword-based retrieval for learning
    scored_documents = []

    for document in documents:
        document_words = set(
            document.lower().replace(".", "").split()
        )

        score = len(question_words & document_words)

        if score > 0:
            scored_documents.append((score, document))

    # Sort by relevance score, highest first
    scored_documents.sort(key=lambda item: item[0], reverse=True)

    context = [
        document
        for score, document in scored_documents[:3]
    ]

    return {"context": context}


    # 4. Generate an answer using the LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

def generate(state: RAGState):
    print("Generating answer...")

    context = "\n".join(state["context"])

    if not context:
        return {
            "answer": "I could not find relevant information "
                      "in the available documents."
        }

    prompt = f"""
You are an enterprise technical assistant.

Answer the question using only the context below.
If the context does not contain enough information,
say that the available documents do not provide the answer.
Do not invent technical details.

Context:
{context}

Question:
{state["question"]}
"""

    response = llm.invoke(prompt)

    return {"answer": response.content}


# 5. Build the LangGraph workflow
builder = StateGraph(RAGState)

builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)

builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)


# 6. Compile the graph
graph = builder.compile()


# 7. Execute the workflow
result = graph.invoke({
    "question": "Which database stores customer data?",
    "context": [],
    "answer": ""
})

# 8. Display the results
print("\nRetrieved documents:")
for document in result["context"]:
    print("-", document)

print("\nFinal answer:")
print(result["answer"])
