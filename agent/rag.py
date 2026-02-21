import os
import chromadb
from chromadb.utils import embedding_functions

from dotenv import load_dotenv

load_dotenv()

# Create embedding function
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Create persistent DB
client = chromadb.Client()

collection = client.get_or_create_collection(
    name="race_knowledge",
    embedding_function=embedding_function
)


def load_documents():
    base_path = "knowledge"
    doc_id = 0

    for filename in os.listdir(base_path):
        with open(os.path.join(base_path, filename), "r") as f:
            content = f.read()

            chunks = content.split("\n\n")

            for chunk in chunks:
                if chunk.strip():
                    collection.add(
                        documents=[chunk],
                        ids=[f"doc_{doc_id}"]
                    )
                    doc_id += 1


def retrieve_context(query, k=3):
    results = collection.query(
        query_texts=[query],
        n_results=k
    )

    return "\n".join(results["documents"][0])
