from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def score_relevance(question: str, answer: str) -> float:
    """
    Measures how well the answer addresses the question.
    Score 0.0 to 1.0 — higher is better.
    """
    question_embedding = embedding_model.encode([question])
    answer_embedding = embedding_model.encode([answer])
    score = cosine_similarity(question_embedding, answer_embedding)[0][0]
    return round(float(score), 3)


def score_faithfulness(answer: str, context: str) -> float:
    """
    Measures how grounded the answer is in the retrieved context.
    Score 0.0 to 1.0 — higher means answer stays true to documents.
    Returns 1.0 if no context was used (LLM answered from memory).
    """
    if not context.strip():
        return 1.0

    # Split context into sentences for granular comparison
    context_sentences = [s.strip() for s in context.split(".") if len(s.strip()) > 20]

    if not context_sentences:
        return 1.0

    answer_embedding = embedding_model.encode([answer])
    context_embeddings = embedding_model.encode(context_sentences)

    # Score = how similar the answer is to the most relevant context sentence
    similarities = cosine_similarity(answer_embedding, context_embeddings)[0]
    score = float(np.max(similarities))
    return round(score, 3)


def score_response(question: str, answer: str, context: str = "") -> dict:
    relevance = score_relevance(question, answer)
    faithfulness = score_faithfulness(answer, context)

    # If no context was used, faithfulness is neutral (0.5) not perfect
    # Prevents off-topic questions from scoring artificially high
    if not context.strip():
        faithfulness = 0.5

    overall = round((relevance * 0.6) + (faithfulness * 0.4), 3)

    if overall >= 0.75:
        grade = "good"
    elif overall >= 0.55:
        grade = "acceptable"
    else:
        grade = "poor"

    return {
        "relevance_score": relevance,
        "faithfulness_score": faithfulness,
        "overall_score": overall,
        "grade": grade
    }