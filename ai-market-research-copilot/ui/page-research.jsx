/* Page: Research (generate report) */

const PageResearch = ({ topic, setTopic, onGenerate, generating, progress, currentStep, steps }) => {
  const suggestions = [
    "AI note-taking tools — Global SMB market, 2026",
    "EV charging infrastructure — EU 2026",
    "D2C skincare brands — India",
    "Voice AI agents — Enterprise",
    "Cloud security posture management",
  ];

  return (
    <div className="fade-in">
      <div className="mb-32">
        <div className="eyebrow mb-8">Step 02 — Generate</div>
        <h1 className="h-display" style={{ fontSize: 32 }}>
          What market are we <span className="italic serif">decoding today?</span>
        </h1>
        <div className="muted mt-8" style={{ maxWidth: 620 }}>
          Define a topic with geography and timeframe. We'll mine your indexed corpus for competitors,
          pricing, trends, and a SWOT — every claim cited.
        </div>
      </div>

      <div className="card mb-24" style={{ padding: 28 }}>
        <div className="eyebrow mb-12">Research Brief</div>
        <textarea
          className="input"
          style={{ fontSize: 18, fontWeight: 500, padding: 14, minHeight: 64, lineHeight: 1.4 }}
          value={topic}
          onChange={e => setTopic(e.target.value)}
          placeholder="e.g. AI note-taking tools — Global SMB market, 2026"
          disabled={generating}
        />
        <div className="row gap-8 mt-16" style={{ flexWrap: "wrap" }}>
          <span className="dim" style={{ fontSize: 11, marginRight: 8, alignSelf: "center" }}>SUGGESTED</span>
          {suggestions.map(s => (
            <span
              key={s}
              className={`chip ${topic === s ? "chip-active" : ""}`}
              onClick={() => !generating && setTopic(s)}
            >
              {s}
            </span>
          ))}
        </div>

        <div className="row mt-24 gap-16" style={{ paddingTop: 16, borderTop: "1px solid var(--border)" }}>
          <div className="col gap-4">
            <div className="dim" style={{ fontSize: 11 }}>Sections</div>
            <div style={{ fontSize: 13, fontWeight: 500 }}>Summary · Competitors · Pricing · Trends · SWOT</div>
          </div>
          <div style={{ width: 1, height: 28, background: "var(--border)" }}></div>
          <div className="col gap-4">
            <div className="dim" style={{ fontSize: 11 }}>ETA</div>
            <div style={{ fontSize: 13, fontWeight: 500 }} className="mono tnum">~ 60–120 sec</div>
          </div>
          <button
            className="btn btn-primary"
            style={{ marginLeft: "auto", padding: "12px 22px" }}
            onClick={onGenerate}
            disabled={generating || !topic.trim()}
          >
            {generating
              ? <><span className="spinner"></span> Generating</>
              : <><Icon name="sparkle" size={14} /> Generate Report</>}
          </button>
        </div>
      </div>

      {generating && (
        <div className="card fade-in" style={{ padding: 28 }}>
          <div className="row mb-16" style={{ justifyContent: "space-between" }}>
            <h2>Synthesising "{topic}"</h2>
            <span className="dim mono tnum">{Math.round(progress)}%</span>
          </div>
          <div className="progress-track mb-24">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <div>
            {steps.map((st, i) => (
              <div key={i} className={`step-row ${i === currentStep ? "active" : ""} ${i < currentStep ? "done" : ""}`}>
                <div className={`step-marker ${i === currentStep ? "active" : ""} ${i < currentStep ? "done" : ""}`}>
                  {i < currentStep ? "✓" : (i + 1).toString().padStart(2, "0")}
                </div>
                <div className="step-label">{st}</div>
                <div className="step-time">
                  {i < currentStep
                    ? `${(2 + i * 1.4).toFixed(1)}s`
                    : i === currentStep
                      ? <span className="spinner"></span>
                      : "—"}
                </div>
              </div>
            ))}
          </div>
          <div className="muted mt-16" style={{ fontSize: 12 }}>
            Running AI analysis on your corpus and web sources. This typically takes 60–120 seconds.
          </div>
        </div>
      )}
    </div>
  );
};

window.PageResearch = PageResearch;
