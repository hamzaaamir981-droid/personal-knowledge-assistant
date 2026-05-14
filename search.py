import chromadb


client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_collection(
    name="knowledge_base"
)

question = input("Search question: ")

results = collection.query(
    query_texts=[question],
    n_results=3
)

print(f"\nQuestion: {question}")

print("\nSearch results:")

for document, metadata in zip(results["documents"][0], results["metadatas"][0]):
    print("\n--- Result ---")
    print(f"Source: {metadata['source']}")
    print(f"Chunk number: {metadata['chunk_number']}")
    print(f"Text: {document[:500]}...")