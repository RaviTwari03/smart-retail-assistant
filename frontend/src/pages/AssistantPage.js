import { useEffect, useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";

function AssistantPage() {

  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {

    try {

      const res = await axios.get(
        "http://127.0.0.1:8000/chat-history"
      );

      console.log("History API:", res.data);

      setHistory(res.data.history || []);

    } catch (error) {

      console.log("History Error:", error);

    }
  };

  const askAssistant = async () => {

    if (!query.trim()) return;

    try {

      setLoading(true);

      const res = await axios.post(
        "http://127.0.0.1:8000/customer-support",
        {
          query: query
        }
      );

      console.log("Assistant API:", res.data);

      // Flexible response handling
      const aiResponse =
        res.data.response ||
        res.data.answer ||
        res.data.message ||
        "No response received";

      setResponse(aiResponse);

      setQuery("");

      fetchHistory();

    } catch (error) {

      console.log("Assistant Error:", error);

      setResponse("Something went wrong.");

    } finally {

      setLoading(false);

    }
  };

  return (

    <Layout>

      <h1>Retail AI Assistant</h1>

      {/* Input Section */}

      <div
        style={{
          display: "flex",
          gap: "10px",
          marginTop: "30px"
        }}
      >

        <input
          type="text"
          placeholder="Ask something..."
          value={query}
          onChange={(e) =>
            setQuery(e.target.value)
          }
          style={{
            padding: "12px",
            width: "400px",
            borderRadius: "8px",
            border: "none",
            fontSize: "16px"
          }}
        />

        <button
          onClick={askAssistant}
          disabled={loading}
          style={{
            padding: "12px 20px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: "#2563eb",
            color: "white",
            cursor: "pointer",
            opacity: loading ? 0.7 : 1
          }}
        >

          {loading ? "Thinking..." : "Ask AI"}

        </button>

      </div>

      {/* Current Response */}

      <div
        style={{
          background: "#1e293b",
          padding: "20px",
          borderRadius: "12px",
          marginTop: "30px",
          maxWidth: "800px"
        }}
      >

        <h3>Assistant Response</h3>

        <p
          style={{
            lineHeight: "1.8",
            whiteSpace: "pre-wrap"
          }}
        >

          {response || "No response yet..."}

        </p>

      </div>

      {/* Chat History */}

      <div
        style={{
          marginTop: "40px",
          maxWidth: "800px"
        }}
      >

        <h2>Recent Chats</h2>

        {
          history.length === 0 ? (

            <p>No chat history found.</p>

          ) : (

            history
              .slice()
              .reverse()
              .map((chat) => (

                <div
                  key={chat.id}
                  style={{
                    background: "#0f172a",
                    padding: "16px",
                    borderRadius: "10px",
                    marginTop: "15px"
                  }}
                >

                  <p>
                    <strong>Query:</strong>
                    {" "}
                    {chat.query}
                  </p>

                  <p
                    style={{
                      marginTop: "10px",
                      color: "#cbd5e1",
                      whiteSpace: "pre-wrap"
                    }}
                  >

                    <strong>Response:</strong>
                    {" "}
                    {chat.response}

                  </p>

                </div>
              ))
          )
        }

      </div>

    </Layout>
  );
}

export default AssistantPage;