import time
from fastapi import FastAPI, HTTPException
from cache import check_cache, store_in_cache
from rag import load_documents, retrieve_context
from router import route_request
from groq import Groq
from models import QueryRequest, QueryResponse
from database import init_db, log_request, update_quality_score, get_last_request_id
from config import GROQ_API_KEY, FAST_MODEL, SMART_MODEL
from evaluator import score_response
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="LLM Observability Platform")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
client = Groq(api_key=GROQ_API_KEY)

COST_PER_1K_TOKENS = {
    "llama-3.1-8b-instant": 0.00005,
    "llama-3.3-70b-versatile": 0.00059,
}

@app.on_event("startup")
def startup():
    init_db()
    load_documents()

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Step 1: Check cache
    cached_answer = check_cache(request.question)
    if cached_answer:
        from database import get_scores_by_question
        original_scores = get_scores_by_question(request.question)

        overall = original_scores[0] if original_scores else 0.0
        relevance = original_scores[1] if original_scores else 0.0
        faithfulness = original_scores[2] if original_scores else 0.0
        grade = original_scores[3] if original_scores else "good"

        log_request(
            question=request.question,
            answer=cached_answer,
            model_used="cache",
            latency_ms=0.0,
            cost=0.0,
            cache_hit=True
        )
        last_id = get_last_request_id()
        update_quality_score(
            request_id=last_id,
            relevance=relevance,
            faithfulness=faithfulness,
            overall=overall,
            grade=grade
        )
        return QueryResponse(
            answer=cached_answer,
            model_used="cache",
            latency_ms=0.0,
            estimated_cost_usd=0.0,
            cache_hit=True,
            sources=[],
            relevance_score=relevance,
            faithfulness_score=faithfulness,
            overall_score=overall,
            grade=grade
        )

    # Step 2: Retrieve context from RAG
    rag_result = retrieve_context(request.question)
    context = rag_result["context"]
    sources = rag_result["sources"]

    # Step 3: Route to correct model
    start = time.time()
    try:
        result = route_request(request.question, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    latency_ms = (time.time() - start) * 1000
    answer = result["answer"]
    model_used = result["model_used"]
    tokens_used = result["tokens_used"]
    cost = (tokens_used / 1000) * COST_PER_1K_TOKENS.get(model_used, 0.0001)

    # Step 4: Store in cache
    store_in_cache(request.question, answer)

    # Step 5: Log to database
    log_request(
        question=request.question,
        answer=answer,
        model_used=model_used,
        latency_ms=round(latency_ms, 2),
        cost=round(cost, 6),
        cache_hit=False
    )

    # Step 6: Score response quality
    eval_scores = score_response(request.question, answer, context)
    last_id = get_last_request_id()
    update_quality_score(
        request_id=last_id,
        relevance=eval_scores["relevance_score"],
        faithfulness=eval_scores["faithfulness_score"],
        overall=eval_scores["overall_score"],
        grade=eval_scores["grade"]
    )

    return QueryResponse(
        answer=answer,
        model_used=model_used,
        latency_ms=round(latency_ms, 2),
        estimated_cost_usd=round(cost, 6),
        cache_hit=False,
        sources=sources,
        relevance_score=eval_scores["relevance_score"],
        faithfulness_score=eval_scores["faithfulness_score"],
        overall_score=eval_scores["overall_score"],
        grade=eval_scores["grade"]
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def stats():
    from database import get_all_requests
    rows = get_all_requests()
    total_cost = sum(row[6] for row in rows)
    total_requests = len(rows)
    cache_hits = sum(1 for row in rows if row[7] == 1)
    return {
        "total_requests": total_requests,
        "total_cost_usd": round(total_cost, 6),
        "cache_hit_rate": round(cache_hits / total_requests * 100, 2) if total_requests > 0 else 0
    }

@app.delete("/cache/clear")
def clear_cache():
    from cache import collection
    collection.delete(where={"timestamp": {"$gt": "0"}})
    return {"status": "cache cleared"}

@app.get("/history")
def history():
    from database import get_all_requests
    rows = get_all_requests()
    return [
        {
            "question": row[2],
            "answer": row[3],
            "model_used": row[4],
            "latency_ms": row[5],
            "estimated_cost_usd": row[6],
            "cache_hit": bool(row[7]),
            "overall_score": row[8],
            "relevance_score": row[9],
            "faithfulness_score": row[10],
            "grade": row[11]
        }
        for row in rows
    ]