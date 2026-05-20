import chromadb
from sentence_transformers import SentenceTransformer
import hashlib
import time

# Load embedding model once at startup — this stays in memory
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ChromaDB client — stores vectors locally on disk
chroma_client = chromadb.PersistentClient(path="./cache_store")
collection = chroma_client.get_or_create_collection(name="query_cache")

# How similar two questions must be to count as a cache hit
# 0.0 = completely different, 1.0 = identical
# 0.85 is the sweet spot — catches rephrased duplicates, ignores different questions
SIMILARITY_THRESHOLD = 0.85


def get_embedding(text: str):
    """Convert text into a vector of numbers that represents its meaning."""
    return embedding_model.encode(text).tolist()


def generate_id(text: str) -> str:
    """Create a unique ID for each question using a hash."""
    return hashlib.md5(text.encode()).hexdigest()


def check_cache(question: str):
    """
    Look for a semantically similar question in cache.
    Returns cached answer if found, None if not found.
    """
    question_embedding = get_embedding(question)

    # Need at least 1 item in collection before querying
    if collection.count() == 0:
        return None

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=1,
        include=["documents", "metadatas", "distances"]
    )

    if not results["ids"][0]:
        return None

    # ChromaDB returns distance not similarity
    # Distance 0 = identical, Distance 2 = completely opposite
    # Convert to similarity: similarity = 1 - (distance / 2)
    distance = results["distances"][0][0]
    similarity = 1 - (distance / 2)

    if similarity >= SIMILARITY_THRESHOLD:
        cached_answer = results["metadatas"][0][0]["answer"]
        return cached_answer

    return None


def store_in_cache(question: str, answer: str):
    """Save a question-answer pair to cache for future reuse."""
    question_embedding = get_embedding(question)
    question_id = generate_id(question)

    collection.upsert(
        ids=[question_id],
        embeddings=[question_embedding],
        documents=[question],
        metadatas=[{"answer": answer, "timestamp": str(time.time())}]
    )