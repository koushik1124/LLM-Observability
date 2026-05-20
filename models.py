from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    context: str = ""  # optional, used later in RAG phase

class QueryResponse(BaseModel):
    answer: str
    model_used: str
    latency_ms: float
    estimated_cost_usd: float
    cache_hit: bool
    sources: list[str] = []
    relevance_score: float = 0.0
    faithfulness_score: float = 0.0
    overall_score: float = 0.0
    grade: str = ""