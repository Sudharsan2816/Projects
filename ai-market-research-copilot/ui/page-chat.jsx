/* Page: Chat */

const PageChat = ({ sessionId, messages, setMessages, docs }) => {
  const [input, setInput] = React.useState("");
  const [streaming, setStreaming] = React.useState(false);
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
    let finalAnswerMode = "documents";

    try {
      for await (const event of API.chatStream(sessionId, question)) {
        if (event.token) {
          fullText += event.token;
          setStreamText(fullText);
        }
        if (event.done) {
          finalSources = event.sources || [];
          finalAnswerMode = event.answer_mode || "documents";
        }
        if (event.error) throw new Error(event.error);
      }
      setMessages(prev => [...prev, {
        role: "ai",
        content: fullText,
        sources: finalSources,
        answerMode: finalAnswerMode,
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: "ai",
        content: `Error: ${error.message}`,
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
    return parts.map((part, index) => {
      const citation = part.match(/^\[(\d+)\]$/);
      if (citation) return <span key={index} className="citation">{citation[1]}</span>;
      const bold = part.match(/^\*\*(.+)\*\*$/);
      if (bold) return <strong key={index} style={{ fontWeight: 600 }}>{bold[1]}</strong>;
      return <span key={index}>{part}</span>;
    });
  };

  const modeLabel = (mode) => ({
    documents: "Uploaded documents",
    general_market_knowledge: "General market knowledge",
    report_irrelevant: "Not in report",
    out_of_scope: "Scope guard",
  }[mode] || "");

  const modeClass = (mode) => ({
    documents: "badge-info",
    report_irrelevant: "badge-warn",
  }[mode] || "");

  const suggestedQuestions = [
    "How do I calculate TAM, SAM, and SOM for a new market?",
    "Who are the top competitors and how do they differ?",
    "What's the pricing benchmark for the core segment?",
    "Which trends will hit hardest in the next 12 months?",
    "What's the white space we should target?",
  ];

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", height: "100%", maxHeight: "calc(100vh - 52px - 64px)" }}>
      <div className="row mb-16" style={{ justifyContent: "space-between" }}>
        <div>
          <div className="eyebrow mb-8">Step 04 — Interrogate</div>
          <h1 className="h-display" style={{ fontSize: 28 }}>
            Chat with your <span className="italic serif">research copilot.</span>
          </h1>
        </div>
        <div className="row gap-8">
          <span className="status-pill">
            <span className="status-dot"></span>
            {docs.length} docs · hybrid answers
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
                  Ask about your sources or market research.
                </div>
                <div className="muted mb-24" style={{ fontSize: 13 }}>
                  Document answers are cited. General market guidance is clearly labeled.
                </div>
                <div className="row gap-8" style={{ flexWrap: "wrap", justifyContent: "center", maxWidth: 640 }}>
                  {suggestedQuestions.map(question => (
                    <button type="button" key={question} className="chip" onClick={() => send(question)}>{question}</button>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="chat-feed">
            {messages.map((message, index) => (
              <div key={index} className="msg fade-in">
                <div className={`msg-avatar ${message.role}`}>
                  {message.role === "user" ? "U" : "AI"}
                </div>
                <div className="msg-body">
                  <div className="msg-author">{message.role === "user" ? "You" : "Marketscope"}</div>
                  {message.role !== "user" && modeLabel(message.answerMode) && (
                    <div className="mb-8">
                      <span className={`badge ${modeClass(message.answerMode)}`}>
                        {modeLabel(message.answerMode)}
                      </span>
                    </div>
                  )}
                  <div className="msg-text">{renderText(message.content)}</div>
                  {message.sources && message.sources.length > 0 && (
                    <div className="sources">
                      {message.sources.map((source, sourceIndex) => (
                        <span key={sourceIndex} className="source-chip">
                          <span className="source-chip-num">{source.idx || sourceIndex + 1}</span>
                          {source.doc || source.source || source.filename || "source"}{source.page ? ` · p.${source.page}` : ""}
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
              onChange={event => setInput(event.target.value)}
              onKeyDown={event => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  send();
                }
              }}
              placeholder="Ask about your documents or a market-research topic…"
              disabled={streaming}
            />
            <div className="composer-actions">
              <span className="composer-hint">
                Enter to send · Shift+Enter for newline · {docs.length} indexed doc{docs.length !== 1 ? "s" : ""}
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
