from pathlib import Path
import re
import fitz
import chromadb


def read_txt(file_path):
    text = file_path.read_text(encoding="utf-8")

    return [
        {
            "text": text,
            "page_number": None
        }
    ]


def read_pdf(file_path):
    document = fitz.open(file_path)
    pages = []

    for page_number, page in enumerate(document, start=1):
        page_text = page.get_text()

        if page_text.strip():
            pages.append(
                {
                    "text": page_text,
                    "page_number": page_number
                }
            )

    return pages


def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def chunk_text(text, max_words=120):
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = len(sentence.split())

        if current_word_count + sentence_word_count > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_word_count = 0

        current_chunk.append(sentence)
        current_word_count += sentence_word_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


data_folder = Path("data")

client = chromadb.PersistentClient(path="chroma_db")

try:
    client.delete_collection(name="knowledge_base")
except Exception:
    pass

collection = client.get_or_create_collection(
    name="knowledge_base"
)

all_ids = []
all_documents = []
all_metadatas = []

for file_path in data_folder.iterdir():
    if file_path.suffix.lower() == ".txt":
        pages = read_txt(file_path)
    elif file_path.suffix.lower() == ".pdf":
        pages = read_pdf(file_path)
    else:
        continue

    document_chunk_number = 1

    for page in pages:
        page_text = page["text"]
        page_number = page["page_number"]

        chunks = chunk_text(page_text)

        for chunk in chunks:
            chunk_id = f"{file_path.stem}_chunk_{document_chunk_number}"

            all_ids.append(chunk_id)
            all_documents.append(chunk)
            all_metadatas.append({
                "source": file_path.name,
                "chunk_number": document_chunk_number,
                "page_number": page_number if page_number is not None else 0,
                "file_type": file_path.suffix.lower()
            })

            document_chunk_number += 1

if all_documents:
    collection.add(
        ids=all_ids,
        documents=all_documents,
        metadatas=all_metadatas
    )

print(f"Stored {len(all_documents)} chunks in ChromaDB.")