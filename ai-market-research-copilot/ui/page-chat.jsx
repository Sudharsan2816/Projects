/* Page: Chat */

const PageChat = ({ sessionId, messages, setMessages, docs }) => {
  const [input,      setInput]      = React.useState("");
  const [streaming,  setStreaming]  = React.useState(false);
  const [streamText, setStreamText] = React.useState("");
  const feedRef = React.useRef(null);

  React.useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [messages, streamText]);

  const send = async (q) => {
    const question = (q || input).trim();
    if (!question || streaming) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: question }]);
    setStreaming(true);
    setStreamText("");

    let fullText = "";
    let finalSources = [];

    try {
      for await (const event of API.chatStream(sessionId, question)) {
        if (event.token) {
          fullText += event.token;
          setStreamText(fullText);
        }
        if (event.done) {
          finalSources = event.sources || [];
        }
        if (event.error) {
          throw new Error(event.error);
        }
      }
      setMessages(prev => [...prev, {
        role: "ai",
        content: fullText,
        sources: finalSources,
      }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: "ai",
        content: `Error: ${e.message}`,
        sources: [],
      }]);
    } finally {
      setStreaming(false);
      setStreamText("");
    }
  };

  const clearChat = async () => {
    try {
      await API.clearChatHistory(sessionId);
      setMessages([]);
    } catch {}
  };

  const renderText = (text) => {
    const parts = text.split(/(\[\d+\]|\*\*[^*]+\*\*)/g);
    return parts.map((p, i) => {
      const cite = p.match(/^\[(\d+)\]$/);
      if (cite) return <span key={i} className="citation">{cite[1]}</span>;
      const bold = p.match(/^\*\*(.+)\*\*$/);
      if (bold) return <strong key={i} style={{ fontWeight: 600 }}>{bold[1]}</strong>;
      return <span key={i}>{p}</span>;
    });
  };

  const suggestedQuestions = [
    "Who are the top competitors and how do they differ?",
    "What's the pricing benchmark for the core segment?",
    "Which trends will hit hardest in the next 12 months?",
    "What's the white space we should target?",
    "What are the biggest market threats?",
  ];

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", height: "100%", maxHeight: "calc(100vh - 52px - 64px)" }}>
      <div className="row mb-16" style={{ justifyContent: "space-between" }}>
        <div>
          <div className="eyebrow mb-8">Step 04 — Interrogate</div>
          <h1 className="h-display" style={{ fontSize: 28 }}>
            Chat with your <span className="italic serif">corpus.</span>
          </h1>
        </div>
        <div className="row gap-8">
          <span className="status-pill">
            <span className="status-dot"></span>
            {docs.length} docs · streaming
          </span>
          <button className="btn btn-ghost btn-sm" onClick={clearChat}>
            <Icon name="refresh" size={12} /> Clear
          </button>
        </div>
      </div>

      <div className="card grow" style={{ display: "flex", flexDirection: "column", padding: 0, overflow: "hidden", minHeight: 0 }}>
        <div ref={feedRef} className="grow" style={{ overflowY: "auto", padding: "24px 28px" }}>
          {messages.length === 0 && !streaming && (
            <div style={{ display: "grid", placeItems: "center", height: "100%", textAlign: "center" }}>
              <div>
                <div style={{ fontSize: 22, fontFamily: "var(--font-serif)", marginBottom: 8 }}>
                  Ask anything about your corpus.
                </div>
                <div className="muted mb-24" style={{ fontSize: 13 }}>
                  Every answer cites the exact passage. Try one of these:
                </div>
                <div className="row gap-8" style={{ flexWrap: "wrap", justifyContent: "center", maxWidth: 640 }}>
                  {suggestedQuestions.map(q => (
                    <span key={q} className="chip" onClick={() => send(q)}>{q}</span>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="chat-feed">
            {messages.map((msg, i) => (
              <div key={i} className="msg fade-in">
                <div className={`msg-avatar ${msg.role}`}>
                  {msg.role === "user" ? "U" : "AI"}
                </div>
                <div className="msg-body">
                  <div className="msg-author">{msg.role === "user" ? "You" : "Marketscope"}</div>
                  <div className="msg-text">{renderText(msg.content)}</div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="sources">
                      {msg.sources.map((s, si) => (
                        <span key={si} className="source-chip">
                          <span className="source-chip-num">{s.idx || si + 1}</span>
                          {s.doc || s.source || s.filename || "source"}{s.page ? ` · p.${s.page}` : ""}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {streaming && (
              <div className="msg fade-in">
                <div className="msg-avatar ai">AI</div>
                <div className="msg-body">
                  <div className="msg-author">Marketscope</div>
                  <div className="msg-text">
                    {renderText(streamText)}
                    <span className="caret"></span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div style={{ padding: "16px 20px", borderTop: "1px solid var(--border)", background: "var(--bg)" }}>
          <div className="composer">
            <textarea
              rows={1}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
              }}
              placeholder="Ask a question about your corpus…"
              disabled={streaming}
            />
            <div className="composer-actions">
              <span className="composer-hint">
                ⏎ to send · ⇧⏎ for newline · cited from {docs.length} doc{docs.length !== 1 ? "s" : ""}
              </span>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => send()}
                disabled={streaming || !input.trim()}
              >
                {streaming ? <span className="spinner"></span> : <>Send <Icon name="arrow" size={12} /></>}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

window.PageChat = PageChat;
