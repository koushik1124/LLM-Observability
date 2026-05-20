from groq import Groq
from config import GROQ_API_KEY, FAST_MODEL, SMART_MODEL

client = Groq(api_key=GROQ_API_KEY)

# Questions shorter than this word count go to fast model directly
SHORT_QUESTION_THRESHOLD = 10

# Keywords that signal a complex question needing the smart model
COMPLEX_KEYWORDS = [
    "explain", "compare", "difference between", "tradeoff", "architecture",
    "design", "implement", "analyze", "evaluate", "why does", "how does",
    "what are the implications", "pros and cons", "in detail", "step by step"
]


def measure_complexity(question: str) -> dict:
    """
    Decide how complex a question is.
    Returns complexity level and which model to use.
    """
    question_lower = question.lower()
    word_count = len(question.split())
    print(f"Word count: {word_count}")

    # Rule 1: Very short questions are simple
    if word_count <= SHORT_QUESTION_THRESHOLD:
        has_complex_keyword = any(keyword in question_lower for keyword in COMPLEX_KEYWORDS)
        if not has_complex_keyword:
            return {
                "complexity": "simple",
                "model": FAST_MODEL,
                "reason": f"Short question ({word_count} words), no complex keywords"
            }

    # Rule 2: Check for complexity keywords
    found_keywords = [kw for kw in COMPLEX_KEYWORDS if kw in question_lower]
    print(f"Found keywords: {found_keywords}")
    if found_keywords:
        return {
            "complexity": "complex",
            "model": SMART_MODEL,
            "reason": f"Complex keywords detected: {found_keywords}"
        }

    # Rule 3: Long questions without keywords — use smart model to be safe
    if word_count > SHORT_QUESTION_THRESHOLD:
        return {
            "complexity": "moderate",
            "model": SMART_MODEL,
            "reason": f"Long question ({word_count} words)"
        }

    return {
        "complexity": "simple",
        "model": FAST_MODEL,
        "reason": "Default: simple question"
    }


def route_request(question: str, context: str = "") -> dict:
    """
    Route question to the right model based on complexity.
    Returns the answer plus routing metadata.
    """
    routing_decision = measure_complexity(question)
    chosen_model = routing_decision["model"]

    # Build messages — include context if provided (used later in RAG phase)
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Answer clearly and accurately. If you don't know something, say so explicitly instead of guessing."
        }
    ]

    if context.strip():
        messages.append({
            "role": "system",
            "content": f"Use this context to answer the question:\n\n{context}"
        })

    messages.append({"role": "user", "content": question})

    completion = client.chat.completions.create(
        model=chosen_model,
        messages=messages,
        max_tokens=512,
        temperature=0
    )

    answer = completion.choices[0].message.content
    tokens_used = completion.usage.total_tokens

    return {
        "answer": answer,
        "model_used": chosen_model,
        "tokens_used": tokens_used,
        "complexity": routing_decision["complexity"],
        "routing_reason": routing_decision["reason"]
    }