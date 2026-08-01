/* Page: Research */

const PageResearch = ({
  topic,
  setTopic,
  onGenerate,
  generating,
  progress,
  currentStep,
  currentStage,
  steps,
  error,
  reportReady,
  onOpenReport,
}) => {
  const suggestions = [
    "AI note-taking tools, global SMB market, 2026",
    "EV charging infrastructure, EU, 2026",
    "D2C skincare brands in India",
    "Voice AI agents for enterprises",
  ];

  return (
    <div className="fade-in page-stack">
      <header className="page-header">
        <div>
          <div className="eyebrow mb-8">Research workspace</div>
          <h1>Generate market intelligence</h1>
          <p className="muted page-lead">
            Define the market, geography, audience, and timeframe. The report job runs on the server
            and continues while you move through the workspace.
          </p>
        </div>
        {reportReady && !generating && (
          <button type="button" className="btn" onClick={onOpenReport}>
            <Icon name="chart" size={14} /> Open latest report
          </button>
        )}
      </header>

      <section className="workspace-panel" aria-labelledby="research-brief-title">
        <div className="panel-heading">
          <div>
            <div className="eyebrow">Research brief</div>
            <h2 id="research-brief-title">What should the copilot investigate?</h2>
          </div>
          <span className="badge badge-info">AI generated</span>
        </div>

        <label className="field-label" htmlFor="market-topic">Market topic</label>
        <textarea
          id="market-topic"
          className="input research-input"
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          placeholder="Example: AI note-taking tools for global SMB teams, 2026"
          disabled={generating}
          maxLength={255}
        />
        <div className="field-meta">
          <span>Include geography, customer segment, and timeframe for stronger output.</span>
          <span className="mono tnum">{topic.length}/255</span>
        </div>

        <div className="suggestion-row" aria-label="Suggested market topics">
          {suggestions.map((suggestion) => (
            <button
              type="button"
              key={suggestion}
              className={`chip ${topic === suggestion ? "chip-active" : ""}`}
              onClick={() => setTopic(suggestion)}
              disabled={generating}
            >
              {suggestion}
            </button>
          ))}
        </div>

        <div className="research-actions">
          <div className="research-output-list">
            <span>Executive summary</span>
            <span>Competitors</span>
            <span>Pricing</span>
            <span>Trends</span>
            <span>SWOT</span>
          </div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={onGenerate}
            disabled={generating || topic.trim().length < 3}
          >
            {generating
              ? <><span className="spinner" aria-hidden="true"></span> Report running</>
              : <><Icon name="sparkle" size={14} /> Generate report</>}
          </button>
        </div>
      </section>

      {error && (
        <section className="alert alert-error" role="alert">
          <Icon name="flag" size={18} />
          <div className="grow">
            <strong>Report generation failed</strong>
            <p>{error}</p>
          </div>
          <button type="button" className="btn btn-sm" onClick={onGenerate}>Retry</button>
        </section>
      )}

      {generating && (
        <section className="workspace-panel" aria-labelledby="job-title">
          <div className="panel-heading">
            <div>
              <div className="eyebrow">Active job</div>
              <h2 id="job-title">{currentStage || "Generating report"}</h2>
            </div>
            <span className="mono tnum job-percent">{progress}%</span>
          </div>
          <div className="progress-track" aria-label={`Report generation ${progress}% complete`}>
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <div className="job-steps">
            {steps.map((step, index) => (
              <div key={step} className={`job-step ${index === currentStep ? "active" : ""} ${index < currentStep ? "done" : ""}`}>
                <span className="job-step-marker">{index < currentStep ? "✓" : String(index + 1).padStart(2, "0")}</span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

window.PageResearch = PageResearch;
