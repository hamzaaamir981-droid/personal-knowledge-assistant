import streamlit as st
import chromadb
import requests
import subprocess
import sys
from pathlib import Path


st.set_page_config(page_title="Personal Knowledge Assistant")

st.title("Personal Knowledge Assistant")
st.write("Ask questions from your stored documents or generate detailed summaries.")


data_folder = Path("data")
data_folder.mkdir(exist_ok=True)


# -----------------------------
# Upload section
# -----------------------------

uploaded_file = st.file_uploader(
    "Upload a PDF or TXT file",
    type=["pdf", "txt"]
)

if uploaded_file is not None:
    file_path = data_folder / uploaded_file.name

    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    st.success(f"Uploaded: {uploaded_file.name}")
    st.info("Click Rebuild Knowledge Base to make this file searchable.")


# -----------------------------
# Document management section
# -----------------------------

st.divider()
st.subheader("Manage Documents")

files_in_data = [
    file.name
    for file in data_folder.iterdir()
    if file.suffix.lower() in [".pdf", ".txt"]
]

if files_in_data:
    st.write("Files in data folder:")

    for file_name in files_in_data:
        st.write(f"- {file_name}")

    file_to_delete = st.selectbox(
        "Choose a file to delete:",
        files_in_data
    )

    if st.button("Delete Selected File"):
        file_path = data_folder / file_to_delete

        if file_path.exists():
            file_path.unlink()
            st.success(f"Deleted: {file_to_delete}")
            st.warning("Now click Rebuild Knowledge Base to update the searchable database.")
        else:
            st.error("File not found.")
else:
    st.info("No PDF/TXT files found in the data folder.")


# -----------------------------
# Rebuild knowledge base
# -----------------------------

st.divider()

if st.button("Rebuild Knowledge Base"):
    with st.spinner("Rebuilding knowledge base..."):
        result = subprocess.run(
            [sys.executable, "ingest.py"],
            capture_output=True,
            text=True
        )

    if result.returncode == 0:
        st.success("Knowledge base rebuilt successfully.")
        st.code(result.stdout)
    else:
        st.error("Failed to rebuild knowledge base.")
        st.code(result.stderr)


# -----------------------------
# Connect to ChromaDB
# -----------------------------

client = chromadb.PersistentClient(path="chroma_db")

try:
    collection = client.get_collection(
        name="knowledge_base"
    )
except Exception:
    st.warning("No knowledge base found. Upload a PDF/TXT file and click Rebuild Knowledge Base.")
    st.stop()


collection_data = collection.get()

documents_in_data = []

for metadata in collection_data["metadatas"]:
    source_name = metadata["source"]

    if source_name not in documents_in_data:
        documents_in_data.append(source_name)


if not documents_in_data:
    st.warning("No indexed documents found. Upload a PDF/TXT file and rebuild the knowledge base.")
    st.stop()


total_chunks = len(collection_data["ids"])

st.info(f"Indexed documents: {len(documents_in_data)} | Indexed chunks: {total_chunks}")


selected_document = st.selectbox(
    "Choose a document:",
    documents_in_data
)

st.caption(f"Currently using: {selected_document}")


task_mode = st.selectbox(
    "Choose task:",
    [
        "Ask a question",
        "Summarize selected document"
    ]
)


# -----------------------------
# Helper functions
# -----------------------------

def ask_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3:8b",
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()
    return data["response"]


def build_source_label(metadata):
    source = metadata["source"]
    chunk_number = metadata["chunk_number"]
    page_number = metadata.get("page_number", 0)

    if page_number:
        return f"{source} - page {page_number} - chunk {chunk_number}"

    return f"{source} - chunk {chunk_number}"


# -----------------------------
# Ask question mode
# -----------------------------

if task_mode == "Ask a question":
    with st.form("question_form"):
        question = st.text_input("Ask a question:")
        submitted = st.form_submit_button("Ask")

    if submitted:
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            results = collection.query(
                query_texts=[question],
                n_results=3,
                where={"source": selected_document}
            )

            retrieved_documents = results["documents"][0]
            retrieved_metadatas = results["metadatas"][0]

            context = "\n\n".join(retrieved_documents)

            prompt = f"""
You are a helpful knowledge assistant.

Use only the context below to answer the question.

Context:
{context}

Question:
{question}

Rules:
- Answer only from the context.
- Use simple English.
- If the answer has multiple points, write each point on a separate line starting with "- ".
- Never put multiple list items on the same line.
- If the answer is not in the context, say: "I don't know based on the provided documents."

Answer:
"""

            with st.spinner("Thinking..."):
                answer = ask_ollama(prompt)

            st.caption(f"Retrieved chunks used: {len(retrieved_documents)}")

            st.subheader("Answer")
            st.markdown(answer)

            st.text_area(
                "Copy-friendly answer:",
                value=answer,
                height=180
            )

            st.divider()
            st.subheader("Sources")

            for metadata, document in zip(retrieved_metadatas, retrieved_documents):
                source_label = build_source_label(metadata)
                preview = document[:300] + "..."

                with st.expander(source_label):
                    st.write(preview)


# -----------------------------
# Summary mode
# -----------------------------

elif task_mode == "Summarize selected document":
    st.write("Generate a detailed summary of the selected document.")

    if st.button("Generate Detailed Summary"):
        document_data = collection.get(
            where={"source": selected_document}
        )

        document_chunks = document_data["documents"]
        document_metadatas = document_data["metadatas"]

        if not document_chunks:
            st.warning("No chunks found for this document.")
        else:
            full_context = "\n\n".join(document_chunks)

            prompt = f"""
You are a helpful knowledge assistant.

Use only the document content below to create a detailed summary.

Document name:
{selected_document}

Document content:
{full_context}

Rules:
- Write a detailed summary in simple English.
- Cover the main ideas from the document.
- Use clear section headings.
- If listing points, write each item on a new line starting with "- ".
- Do not use the bullet symbol "•".
- Do not put multiple list items on the same line.
- Do not add outside knowledge.
- Do not invent facts.
- If the document content is not enough, mention that clearly.

Detailed summary:
"""

            with st.spinner("Generating detailed summary..."):
                summary = ask_ollama(prompt)

            st.caption(f"Total document chunks used: {len(document_chunks)}")

            st.subheader("Detailed Summary")
            st.markdown(summary)

            st.text_area(
                "Copy-friendly summary:",
                value=summary,
                height=300
            )

            st.divider()
            st.subheader("Chunks Used")

            for metadata, document in zip(document_metadatas, document_chunks):
                source_label = build_source_label(metadata)
                preview = document[:300] + "..."

                with st.expander(source_label):
                    st.write(preview)