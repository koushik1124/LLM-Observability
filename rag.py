import os
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Reuse same embedding model as cache — no double loading
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Separate ChromaDB collection from cache — don't mix them
chroma_client = chromadb.PersistentClient(path="./rag_store")
rag_collection = chroma_client.get_or_create_collection(name="documents")

DOCUMENTS_PATH = "./documents"

# Chunk size in characters — 500 chars is roughly 100 words
# Small enough to be specific, large enough to have context
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100


def chunk_text(text: str, source: str) -> list[dict]:
    """
    Split document into overlapping chunks.
    Overlap prevents answers from being cut off at chunk boundaries.
    """
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_text = text[start:end]

        # Don't create tiny leftover chunks
        if len(chunk_text) < 100:
            break

        chunks.append({
            "text": chunk_text,
            "source": source,
            "chunk_index": chunk_index
        })

        chunk_index += 1
        # Move forward by CHUNK_SIZE minus overlap
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def load_documents():
    """
    Load all .txt files from documents folder,
    chunk them, embed them, store in ChromaDB.
    """
    # Skip if already loaded
    if rag_collection.count() > 0:
        print(f"RAG store already has {rag_collection.count()} chunks — skipping ingestion")
        return

    print("Loading documents into RAG store...")
    all_chunks = []

    for filepath in Path(DOCUMENTS_PATH).glob("*.txt"):
        text = filepath.read_text(encoding="utf-8")
        chunks = chunk_text(text, source=filepath.name)
        all_chunks.extend(chunks)
        print(f"  {filepath.name} — {len(chunks)} chunks")

    if not all_chunks:
        print("No documents found in ./documents folder")
        return

    # Embed all chunks
    texts = [c["text"] for c in all_chunks]
    embeddings = embedding_model.encode(texts).tolist()

    # Store in ChromaDB
    rag_collection.upsert(
        ids=[f"{c['source']}_{c['chunk_index']}" for c in all_chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[{"source": c["source"], "chunk_index": c["chunk_index"]} for c in all_chunks]
    )

    print(f"RAG store ready — {len(all_chunks)} total chunks from {len(list(Path(DOCUMENTS_PATH).glob('*.txt')))} files")


def retrieve_context(question: str, top_k: int = 3) -> dict:
    """
    Find the most relevant chunks for a given question.
    Returns context text and source citations.
    """
    question_embedding = embedding_model.encode(question).tolist()

    results = rag_collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    if not results["ids"][0]:
        return {"context": "", "sources": []}

    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # Convert distances to similarity scores
    similarities = [round(1 - (d / 2), 3) for d in distances]

    # Only use chunks above relevance threshold
    relevant_chunks = [
        {"text": chunk, "source": meta["source"], "similarity": sim}
        for chunk, meta, sim in zip(chunks, metadatas, similarities)
        if sim >= 0.5
    ]

    if not relevant_chunks:
        return {"context": "", "sources": []}

    # Combine chunks into one context block
    context = "\n\n".join([c["text"] for c in relevant_chunks])
    sources = list(set([c["source"] for c in relevant_chunks]))

    return {
        "context": context,
        "sources": sources,
        "relevance_scores": similarities
    }