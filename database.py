import sqlite3
from datetime import datetime

DB_PATH = "observability.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            question TEXT,
            answer TEXT,
            model_used TEXT,
            latency_ms REAL,
            estimated_cost_usd REAL,
            cache_hit INTEGER,
            quality_score REAL DEFAULT NULL,
            relevance_score REAL DEFAULT NULL,
            faithfulness_score REAL DEFAULT NULL,
            grade TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()

def log_request(question, answer, model_used, latency_ms, cost, cache_hit):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO requests 
        (timestamp, question, answer, model_used, latency_ms, estimated_cost_usd, cache_hit)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        question, answer, model_used,
        latency_ms, cost, int(cache_hit)
    ))
    conn.commit()
    conn.close()

def get_all_requests():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
def update_quality_score(request_id: int, relevance: float, faithfulness: float, overall: float, grade: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE requests 
        SET quality_score = ?,
            relevance_score = ?,
            faithfulness_score = ?,
            grade = ?
        WHERE id = ?
    """, (overall, relevance, faithfulness, grade, request_id))
    conn.commit()
    conn.close()

def get_last_request_id() -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM requests")
    result = cursor.fetchone()[0]
    conn.close()
    return result or 0
def get_scores_by_question(question: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT quality_score, relevance_score, faithfulness_score, grade 
        FROM requests 
        WHERE question = ? AND cache_hit = 0
        ORDER BY id DESC LIMIT 1
    """, (question,))
    row = cursor.fetchone()
    conn.close()
    return row