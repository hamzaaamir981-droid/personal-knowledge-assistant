\# Personal Knowledge Assistant



A local RAG-based knowledge assistant that lets users upload PDF and TXT files, ask questions from selected documents, and generate detailed summaries using a local AI model.



This project was built as part of my AI Generalist learning roadmap to understand how Retrieval-Augmented Generation works in practice.



\---



\## What This Project Does



The app allows users to:



\- Upload PDF and TXT documents

\- Rebuild a local searchable knowledge base

\- Select a specific document to search

\- Ask questions from that document

\- Generate detailed summaries

\- View source chunks used for each answer

\- See PDF page numbers in sources

\- Copy answers from a copy-friendly text box

\- Delete uploaded documents from the app



\---



\## Why This Project Matters



Normal AI models can hallucinate because they answer from general training data.



This project uses RAG:



```text

User question

→ retrieve relevant document chunks

→ send chunks to local LLM

→ generate answer based on retrieved context

