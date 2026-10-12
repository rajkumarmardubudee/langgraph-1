import os

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore

# 1. Configure embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)


# 2. Connect to Elasticsearch
es_url = os.getenv(
    "ELASTICSEARCH_URL",
    "http://localhost:9200"
)

es_user = os.getenv("ELASTICSEARCH_USER")
es_password = os.getenv("ELASTICSEARCH_PASSWORD")

# Initialize connection dictionary
connection = {
    "es_url": es_url
}

if es_user and es_password:
    connection["es_user"] = es_user
    connection["es_password"] = es_password

# 3. Load sample enterprise documents
documents = [
    Document(
        page_content=(
            "The legacy KYC application uses Java and Struts. "
            "Business logic is implemented in Struts Action classes."
        ),
        metadata={
            "source": "kyc_architecture.txt",
            "module": "legacy-web"
        }
    ),
    Document(
        page_content=(
            "The application runs on IBM WebSphere and accesses "
            "customer information stored in Mainframe DB2."
        ),
        metadata={
            "source": "database_architecture.txt",
            "module": "database"
        }
    ),
    Document(
        page_content=(
            "The target architecture moves business logic into "
            "Spring Boot services and uses Angular for the frontend."
        ),
        metadata={
            "source": "target_architecture.txt",
            "module": "modernization"
        }
    )
]


# 4. Split documents into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=250,
    chunk_overlap=40
)


chunks = splitter.split_documents(documents)


print(f"Documents loaded: {len(documents)}")
print(f"Chunks created: {len(chunks)}")


# 5. Connect to the vector store
vector_store = ElasticsearchStore(
    index_name="kyc-knowledge-v1",
    embedding=embeddings,
    **connection
)

# 6. Index documents in Elasticsearch
print("Indexing documents into Elasticsearch...")

ids = vector_store.add_documents(chunks)

print(f"Documents indexed successfully. IDs created: {len(ids)}")