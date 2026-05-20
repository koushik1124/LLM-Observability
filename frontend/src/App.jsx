import { useState, useEffect } from "react";
import axios from "axios";
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, BarChart, Bar
} from "recharts";

const API = "http://localhost:8000";

const gradeColor = (grade) => {
  if (grade === "good") return "#00ff88";
  if (grade === "acceptable") return "#f59e0b";
  return "#ef4444";
};

const GradeTag = ({ grade }) => (
  <span style={{
    color: gradeColor(grade),
    border: `1px solid ${gradeColor(grade)}`,
    padding: "2px 10px",
    borderRadius: "4px",
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    textTransform: "uppercase",
    letterSpacing: "1px"
  }}>
    {grade}
  </span>
);

const MetricCard = ({ label, value, accent }) => (
  <div style={{
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "12px",
    padding: "24px",
    flex: 1,
    minWidth: "160px"
  }}>
    <div style={{
      fontSize: "28px",
      fontFamily: "var(--font-mono)",
      fontWeight: "700",
      color: accent || "var(--accent)",
      marginBottom: "6px"
    }}>{value}</div>
    <div style={{
      fontSize: "12px",
      color: "var(--text-muted)",
      textTransform: "uppercase",
      letterSpacing: "1px"
    }}>{label}</div>
  </div>
);

const ScoreBar = ({ label, score }) => (
  <div style={{ marginBottom: "12px" }}>
    <div style={{
      display: "flex",
      justifyContent: "space-between",
      marginBottom: "4px",
      fontSize: "12px"
    }}>
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span style={{
        fontFamily: "var(--font-mono)",
        color: score >= 0.75 ? "var(--accent)" : score >= 0.55 ? "var(--warn)" : "var(--danger)"
      }}>{score.toFixed(3)}</span>
    </div>
    <div style={{
      height: "4px",
      background: "var(--border)",
      borderRadius: "2px",
      overflow: "hidden"
    }}>
      <div style={{
        height: "100%",
        width: `${score * 100}%`,
        background: score >= 0.75 ? "var(--accent)" : score >= 0.55 ? "var(--warn)" : "var(--danger)",
        borderRadius: "2px",
        transition: "width 0.6s ease"
      }} />
    </div>
  </div>
);

export default function App() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [statsRes, historyRes] = await Promise.all([
          axios.get(`${API}/stats`),
          axios.get(`${API}/history`)
        ]);
        setStats(statsRes.data);
        setHistory(historyRes.data);
      } catch {
        console.error("Initial data fetch failed");
      }
    };
    loadInitialData();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/stats`);
      setStats(res.data);
    } catch {
      console.error("Stats fetch failed");
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API}/history`);
      setHistory(res.data);
    } catch {
      console.error("History fetch failed");
    }
  };

  const handleQuery = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError("");
    setResponse(null);

    try {
      const res = await axios.post(`${API}/query`, {
        question,
        context: ""
      });
      setResponse(res.data);
      await fetchStats();
      await fetchHistory();
    } catch (e) {
      setError(e.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const chartData = history.slice(0, 20).reverse().map((r, i) => ({
    index: i + 1,
    relevance: r.relevance_score || 0,
    faithfulness: r.faithfulness_score || 0,
    overall: r.overall_score || 0,
    cost: r.estimated_cost_usd || 0
  }));

  return (
    <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "40px 24px" }}>

      {/* Header */}
      <div style={{ marginBottom: "48px" }}>
        <div style={{
          fontFamily: "var(--font-mono)",
          fontSize: "11px",
          color: "var(--accent)",
          letterSpacing: "3px",
          textTransform: "uppercase",
          marginBottom: "8px"
        }}>
          ◆ LLM Observability Platform
        </div>
        <h1 style={{
          fontSize: "42px",
          fontWeight: "300",
          letterSpacing: "-1px",
          lineHeight: 1.1
        }}>
          Monitor. Evaluate.<br />
          <span style={{ color: "var(--accent)", fontWeight: "600" }}>Optimize.</span>
        </h1>
      </div>

      {/* Metrics Row */}
      {stats && (
        <div style={{
          display: "flex",
          gap: "16px",
          marginBottom: "40px",
          flexWrap: "wrap"
        }}>
          <MetricCard
            label="Total Requests"
            value={stats.total_requests}
            accent="var(--accent)"
          />
          <MetricCard
            label="Total Cost"
            value={`$${stats.total_cost_usd.toFixed(6)}`}
            accent="var(--warn)"
          />
          <MetricCard
            label="Cache Hit Rate"
            value={`${stats.cache_hit_rate}%`}
            accent="#7c3aed"
          />
          <MetricCard
            label="Cost Saved"
            value={`${stats.cache_hit_rate}%`}
            accent="var(--accent)"
          />
        </div>
      )}

      {/* Query Box */}
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "16px",
        padding: "24px",
        marginBottom: "32px"
      }}>
        <div style={{
          fontSize: "11px",
          fontFamily: "var(--font-mono)",
          color: "var(--text-muted)",
          letterSpacing: "2px",
          textTransform: "uppercase",
          marginBottom: "16px"
        }}>Query Interface</div>

        <div style={{ display: "flex", gap: "12px" }}>
          <input
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleQuery()}
            placeholder="Ask anything about AI/ML..."
            style={{
              flex: 1,
              background: "var(--surface2)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "14px 16px",
              color: "var(--text)",
              fontSize: "15px",
              fontFamily: "var(--font-body)",
              outline: "none",
            }}
          />
          <button
            onClick={handleQuery}
            disabled={loading}
            style={{
              background: loading ? "var(--border)" : "var(--accent)",
              color: loading ? "var(--text-muted)" : "#000",
              border: "none",
              borderRadius: "8px",
              padding: "14px 28px",
              fontSize: "14px",
              fontWeight: "600",
              fontFamily: "var(--font-mono)",
              cursor: loading ? "not-allowed" : "pointer",
              transition: "all 0.2s",
              whiteSpace: "nowrap"
            }}
          >
            {loading ? "..." : "RUN →"}
          </button>
        </div>

        {error && (
          <div style={{
            marginTop: "12px",
            color: "var(--danger)",
            fontSize: "13px",
            fontFamily: "var(--font-mono)"
          }}>⚠ {error}</div>
        )}
      </div>

      {/* Response Card */}
      {response && (
        <div style={{
          background: "var(--surface)",
          border: `1px solid ${gradeColor(response.grade)}40`,
          borderRadius: "16px",
          padding: "24px",
          marginBottom: "32px"
        }}>
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "20px",
            flexWrap: "wrap",
            gap: "12px"
          }}>
            <div style={{
              fontSize: "11px",
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
              letterSpacing: "2px",
              textTransform: "uppercase"
            }}>Response</div>
            <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
              <GradeTag grade={response.grade} />
              <span style={{
                fontSize: "11px",
                fontFamily: "var(--font-mono)",
                color: "var(--text-muted)",
                background: "var(--surface2)",
                padding: "2px 10px",
                borderRadius: "4px"
              }}>
                {response.cache_hit ? "⚡ CACHE" : `⚙ ${response.model_used.split("-").slice(0, 3).join("-")}`}
              </span>
              <span style={{
                fontSize: "11px",
                fontFamily: "var(--font-mono)",
                color: "var(--text-muted)"
              }}>
                {response.latency_ms}ms · ${response.estimated_cost_usd.toFixed(6)}
              </span>
            </div>
          </div>

          <p style={{
            lineHeight: "1.7",
            color: "var(--text)",
            fontSize: "15px",
            marginBottom: "20px",
            whiteSpace: "pre-wrap"
          }}>{response.answer}</p>

          {/* Scores */}
          <div style={{
            background: "var(--surface2)",
            borderRadius: "10px",
            padding: "16px",
            marginBottom: "16px"
          }}>
            <div style={{
              fontSize: "11px",
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
              letterSpacing: "2px",
              textTransform: "uppercase",
              marginBottom: "14px"
            }}>Eval Scores</div>
            <ScoreBar label="Relevance" score={response.relevance_score} />
            <ScoreBar label="Faithfulness" score={response.faithfulness_score} />
            <ScoreBar label="Overall" score={response.overall_score} />
          </div>

          {/* Sources or Warning */}
          {response.sources?.length > 0 ? (
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "16px" }}>
              <span style={{
                fontSize: "11px",
                color: "var(--text-muted)",
                fontFamily: "var(--font-mono)"
              }}>SOURCES:</span>
              {response.sources.map(s => (
                <span key={s} style={{
                  fontSize: "11px",
                  fontFamily: "var(--font-mono)",
                  color: "var(--accent)",
                  background: "#00ff8815",
                  padding: "2px 8px",
                  borderRadius: "4px"
                }}>{s}</span>
              ))}
            </div>
          ) : (
            !response.cache_hit && (
              <div style={{
                marginTop: "16px",
                padding: "10px 14px",
                background: "#f59e0b15",
                border: "1px solid #f59e0b40",
                borderRadius: "8px",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}>
                <span style={{ fontSize: "14px" }}>⚠</span>
                <span style={{
                  fontSize: "12px",
                  fontFamily: "var(--font-mono)",
                  color: "#f59e0b"
                }}>
                  Answer not grounded in documents — verify independently
                </span>
              </div>
            )
          )}
        </div>
      )}

      {/* Charts */}
      {chartData.length > 1 && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "16px",
          marginBottom: "32px"
        }}>
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "16px",
            padding: "24px"
          }}>
            <div style={{
              fontSize: "11px",
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
              letterSpacing: "2px",
              textTransform: "uppercase",
              marginBottom: "20px"
            }}>Quality Over Time</div>
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={chartData}>
                <XAxis dataKey="index" hide />
                <YAxis domain={[0, 1]} hide />
                <Tooltip
                  contentStyle={{
                    background: "var(--surface2)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    fontFamily: "var(--font-mono)"
                  }}
                />
                <Line type="monotone" dataKey="relevance" stroke="#00ff88" strokeWidth={2} dot={false} name="Relevance" />
                <Line type="monotone" dataKey="faithfulness" stroke="#7c3aed" strokeWidth={2} dot={false} name="Faithfulness" />
                <Line type="monotone" dataKey="overall" stroke="#f59e0b" strokeWidth={2} dot={false} name="Overall" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "16px",
            padding: "24px"
          }}>
            <div style={{
              fontSize: "11px",
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
              letterSpacing: "2px",
              textTransform: "uppercase",
              marginBottom: "20px"
            }}>Cost Per Request</div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={chartData}>
                <XAxis dataKey="index" hide />
                <YAxis hide />
                <Tooltip
                  contentStyle={{
                    background: "var(--surface2)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    fontFamily: "var(--font-mono)"
                  }}
                  formatter={(v) => [`$${v.toFixed(6)}`, "Cost"]}
                />
                <Bar dataKey="cost" fill="#f59e0b" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* History Table */}
      {history.length > 0 && (
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "16px",
          padding: "24px"
        }}>
          <div style={{
            fontSize: "11px",
            fontFamily: "var(--font-mono)",
            color: "var(--text-muted)",
            letterSpacing: "2px",
            textTransform: "uppercase",
            marginBottom: "20px"
          }}>Recent Requests</div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["Question", "Model", "Grade", "Latency", "Cost", "Cache"].map(h => (
                    <th key={h} style={{
                      textAlign: "left",
                      padding: "8px 12px",
                      fontSize: "10px",
                      fontFamily: "var(--font-mono)",
                      color: "var(--text-muted)",
                      letterSpacing: "1px",
                      textTransform: "uppercase",
                      fontWeight: "400"
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.slice(0, 10).map((row, i) => (
                  <tr key={i}
                    style={{
                      borderBottom: "1px solid var(--border)",
                      transition: "background 0.15s"
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = "var(--surface2)"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                  >
                    <td style={{
                      padding: "12px",
                      fontSize: "13px",
                      maxWidth: "300px",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap"
                    }}>{row.question}</td>
                    <td style={{
                      padding: "12px",
                      fontSize: "11px",
                      fontFamily: "var(--font-mono)",
                      color: "var(--text-muted)"
                    }}>{row.model_used === "cache" ? "⚡ cache" : row.model_used?.split("-").slice(0, 3).join("-")}</td>
                    <td style={{ padding: "12px" }}>
                      {row.grade && <GradeTag grade={row.grade} />}
                    </td>
                    <td style={{
                      padding: "12px",
                      fontSize: "12px",
                      fontFamily: "var(--font-mono)",
                      color: "var(--text-muted)"
                    }}>{row.latency_ms}ms</td>
                    <td style={{
                      padding: "12px",
                      fontSize: "12px",
                      fontFamily: "var(--font-mono)",
                      color: row.estimated_cost_usd === 0 ? "var(--accent)" : "var(--text-muted)"
                    }}>${row.estimated_cost_usd?.toFixed(6)}</td>
                    <td style={{
                      padding: "12px",
                      fontSize: "12px",
                      fontFamily: "var(--font-mono)",
                      color: row.cache_hit ? "var(--accent)" : "var(--text-muted)"
                    }}>{row.cache_hit ? "HIT" : "MISS"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}