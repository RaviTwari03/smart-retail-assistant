import { useEffect, useState, useRef } from "react";
import axios from "axios";
import Layout from "../components/Layout";
import API_BASE from "../api";

function AssistantPage() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    fetchHistory();
    inputRef.current?.focus();
  }, []);

  const fetchHistory = async () => {
    try {
      setHistoryLoading(true);
      const res = await axios.get(`${API_BASE}/chat-history`);
      setHistory(res.data.history || []);
    } catch (err) {
      console.error("History fetch error:", err);
      // Non-fatal — just show empty history
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const askAssistant = async () => {
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setResponse("");

      const res = await axios.post(`${API_BASE}/customer-support`, { query });

      const aiResponse =
        res.data.response ||
        res.data.answer ||
        res.data.message ||
        "No response received.";

      setResponse(aiResponse);
      setQuery("");
      fetchHistory();
    } catch (err) {
      console.error("Assistant error:", err);
      setError("Could not reach the assistant. Make sure the API is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !loading) askAssistant();
  };

  return (
    <Layout>
      <h1 style={{ fontSize: "32px", marginBottom: "8px" }}>Retail AI Assistant</h1>
      <p style={{ color: "#64748b", marginBottom: "28px" }}>Ask anything about store policies, inventory, or discounts</p>

      {/* Input row */}
      <div style={{ display: "flex", gap: "10px", maxWidth: "700px" }}>
        <input
          ref={inputRef}
          type="text"
          placeholder="e.g. What is the return policy?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          style={{
            flex: 1,
            padding: "13px 16px",
            borderRadius: "10px",
            border: "1px solid #334155",
            background: "#0f172a",
            color: "white",
            fontSize: "15px",
            outline: "none"
          }}
        />
        <button
          onClick={askAssistant}
          disabled={loading || !query.trim()}
          style={{
            padding: "13px 24px",
            borderRadius: "10px",
            border: "none",
            background: loading ? "#1e3a5f" : "#2563eb",
            color: "white",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "15px",
            fontWeight: "600",
            transition: "background 0.2s"
          }}
        >
          {loading ? "Thinking…" : "Ask AI"}
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div style={{ background: "#450a0a", border: "1px solid #dc2626", borderRadius: "10px", padding: "14px 16px", marginTop: "20px", maxWidth: "700px", color: "#fca5a5" }}>
          ⚠️ {error}
        </div>
      )}

      {/* Response box */}
      <div style={{
        background: "#1e293b",
        padding: "24px",
        borderRadius: "14px",
        marginTop: "24px",
        maxWidth: "700px",
        minHeight: "100px",
        boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
        borderLeft: response ? "4px solid #38bdf8" : "4px solid #334155"
      }}>
        <p style={{ color: "#64748b", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "12px" }}>
          Assistant Response
        </p>
        {loading ? (
          <p style={{ color: "#475569", fontStyle: "italic" }}>Searching knowledge base…</p>
        ) : (
          <p style={{ color: "#e2e8f0", lineHeight: "1.8", whiteSpace: "pre-wrap", margin: 0 }}>
            {response || <span style={{ color: "#475569" }}>No response yet. Ask a question above.</span>}
          </p>
        )}
      </div>

      {/* Chat history */}
      <div style={{ marginTop: "40px", maxWidth: "700px" }}>
        <h2 style={{ fontSize: "20px", marginBottom: "16px", color: "#94a3b8" }}>Recent Chats</h2>

        {historyLoading && <p style={{ color: "#475569" }}>Loading history…</p>}

        {!historyLoading && history.length === 0 && (
          <p style={{ color: "#475569" }}>No chat history yet. Ask your first question!</p>
        )}

        {!historyLoading && history.slice().reverse().map((chat) => (
          <div key={chat.id} style={{
            background: "#0f172a",
            padding: "18px",
            borderRadius: "12px",
            marginBottom: "12px",
            borderLeft: "3px solid #1e3a5f"
          }}>
            <p style={{ color: "#38bdf8", fontSize: "13px", marginBottom: "8px" }}>
              <strong>Q:</strong> {chat.query}
            </p>
            <p style={{ color: "#94a3b8", fontSize: "13px", lineHeight: "1.7", margin: 0, whiteSpace: "pre-wrap" }}>
              <strong>A:</strong> {chat.response}
            </p>
          </div>
        ))}
      </div>
    </Layout>
  );
}

export default AssistantPage;
