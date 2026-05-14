import chromadb
import requests


QUESTION = input("Ask a question: ")

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_collection(
    name="knowledge_base"
)

results = collection.query(
    query_texts=[QUESTION],
    n_results=3
)

retrieved_documents = results["documents"][0]
retrieved_metadatas = results["metadatas"][0]

context = "\n\n".join(retrieved_documents)

sources = []

for metadata in retrieved_metadatas:
    sources.append(f"{metadata['source']} - chunk {metadata['chunk_number']}")

prompt = f"""
You are a helpful knowledge assistant.

Use only the context below to answer the question.

Context:
{context}

Question:
{QUESTION}

Rules:
- Answer only from the context.
- Use simple English.
- If the answer has multiple points, write each point on a separate line starting with "- ".
- Never put multiple list items on the same line.
- If the answer is not in the context, say: "I don't know based on the provided documents."

Answer:
"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3:8b",
        "prompt": prompt,
        "stream": False
    }
)

data = response.json()

print("\nQuestion:")
print(QUESTION)

print("\nAnswer:")
print(data["response"])

print("\nSources:")
for source, document in zip(sources, retrieved_documents):
    preview = document[:250] + "..."
    print(f"\n- {source}")
    print(f"  Preview: {preview}")