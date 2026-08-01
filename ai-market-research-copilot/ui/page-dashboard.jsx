/* Page: Dashboard */

const Dashboard = ({ setRoute, setTopic, docs, reports, health }) => {
  const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
  const totalChunks = docs.reduce((s, d) => s + (d.chunks || 0), 0);
  const doneReports = reports.filter(r => r.status === 'done');
  const llm = health ? (health.llm_provider || 'LLM').toUpperCase() : '—';

  return (
    <div className="fade-in">
      <div className="row mb-32" style={{ alignItems: "flex-end", justifyContent: "space-between" }}>
        <div>
          <div className="eyebrow mb-8">{today} — Live session</div>
          <div className="h-display">
            Discover markets <span className="italic serif">like an analyst,</span><br/>
            ship reports like a copilot.
          </div>
        </div>
        <div className="row gap-8">
          <button className="btn btn-ghost" onClick={() => setRoute("upload")}>
            <Icon name="upload" /> Add documents
          </button>
          <button className="btn btn-primary" onClick={() => setRoute("research")}>
            <Icon name="sparkle" /> New report
          </button>
        </div>
      </div>

      <div className="grid-4 mb-32">
        <div className="kpi">
          <div className="kpi-label">Documents</div>
          <div className="kpi-value tnum">{docs.length}</div>
          <div className="kpi-delta dim">{docs.length ? `${totalChunks} chunks indexed` : "none yet"}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Vector chunks</div>
          <div className="kpi-value tnum">{totalChunks}</div>
          <div className="kpi-delta dim">{docs.length ? `avg ${Math.round(totalChunks / docs.length)} / doc` : "—"}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Reports</div>
          <div className="kpi-value tnum">{doneReports.length}</div>
          <div className="kpi-delta dim">{doneReports.length ? `last: ${API.relativeTime(doneReports[0].created_at)}` : "none yet"}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">LLM Provider</div>
          <div className="kpi-value" style={{ fontSize: 18, fontWeight: 600, color: health ? "var(--accent)" : "var(--fg-muted)" }}>
            {llm}
          </div>
          <div className="kpi-delta">
            <span className="status-dot" style={{ width: 6, height: 6, borderRadius: 999, background: health ? "var(--pos)" : "var(--neg)" }}></span>
            {health ? `configured · ${health.llm_provider || 'selected'}` : "offline"}
          </div>
        </div>
      </div>

      <div className="grid-2 gap-24" style={{ alignItems: "stretch" }}>
        <div className="card" style={{ padding: 24 }}>
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 16 }}>
            <h2>Continue research</h2>
            <span className="dim mono" style={{ fontSize: 11 }}>{doneReports.length} done</span>
          </div>
          {doneReports.length === 0 ? (
            <div className="dim" style={{ fontSize: 13, padding: "12px 0" }}>No reports yet — run your first one.</div>
          ) : (
            <div className="col gap-12">
              {doneReports.slice(0, 3).map(r => (
                <div key={r.id} className="row card-tight card-hover"
                     style={{ background: "var(--bg-elev)", border: "1px solid var(--border)", borderRadius: "var(--r)", cursor: "pointer" }}
                     onClick={() => setRoute("report")}>
                  <div className="col gap-4 grow" style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 500, fontSize: 13 }}>{r.topic}</div>
                    <div className="dim" style={{ fontSize: 11 }}>
                      <span className="mono">#{r.id}</span> · {API.relativeTime(r.created_at)}
                    </div>
                  </div>
                  <span className="badge badge-pos">DONE</span>
                  <Icon name="arrow" size={14} />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card" style={{ padding: 24, display: "flex", flexDirection: "column" }}>
          <h2 className="mb-16">Quickstart</h2>
          <div className="col gap-12 grow">
            <QuickStep n="01" label="Curate"     desc="Drop in PDFs, CSVs, notes."             done={docs.length > 0}  onClick={() => setRoute("upload")} />
            <QuickStep n="02" label="Generate"   desc="Run AI synthesis on a topic."            active={docs.length > 0 && doneReports.length === 0} onClick={() => setRoute("research")} />
            <QuickStep n="03" label="Inspect"    desc="Competitors, pricing, SWOT."             onClick={() => setRoute("report")} />
            <QuickStep n="04" label="Interrogate" desc="Chat with cite-backed answers."          onClick={() => setRoute("chat")} />
          </div>
        </div>
      </div>

      <div className="mt-32 card" style={{ padding: 24 }}>
        <div className="row mb-16" style={{ justifyContent: "space-between" }}>
          <h2>Start a new insight session</h2>
          <span className="dim" style={{ fontSize: 12 }}>Define a market topic and generate a full report</span>
        </div>
        <TopicLauncher setRoute={setRoute} setTopic={setTopic} />
      </div>
    </div>
  );
};

const TopicLauncher = ({ setRoute, setTopic }) => {
  const [val, setVal] = React.useState('');
  const suggestions = [
    "AI note-taking tools, SMB",
    "EV charging EU 2026",
    "D2C skincare India",
    "SaaS CRM landscape",
    "Voice AI — Enterprise",
  ];
  return (
    <>
      <div className="row gap-12">
        <input
          className="input input-lg grow"
          placeholder="e.g. AI note-taking tools — Global SMB market, 2026"
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && val.trim()) {
              setTopic(val.trim());
              setRoute('research');
            }
          }}
        />
        <button
          className="btn btn-primary"
          style={{ padding: "12px 18px" }}
          onClick={() => {
            if (val.trim()) setTopic(val.trim());
            setRoute("research");
          }}
        >
          Generate <Icon name="arrow" size={14} />
        </button>
      </div>
      <div className="row gap-8 mt-16" style={{ flexWrap: "wrap" }}>
        {suggestions.map(s => (
          <button key={s} type="button" className="chip" onClick={() => { setTopic(s); setRoute("research"); }}>{s}</button>
        ))}
      </div>
    </>
  );
};

const QuickStep = ({ n, label, desc, active, done, onClick }) => (
  <div
    className={`step-row ${active ? "active" : ""} ${done ? "done" : ""}`}
    style={{ borderBottom: "none", padding: "10px 0", cursor: "pointer" }}
    onClick={onClick}
  >
    <div className={`step-marker ${active ? "active" : ""} ${done ? "done" : ""}`}>
      {done ? "✓" : n}
    </div>
    <div className="col gap-4 grow">
      <div className="step-label" style={{ fontWeight: 500, fontSize: 13 }}>{label}</div>
      <div className="dim" style={{ fontSize: 12 }}>{desc}</div>
    </div>
    <Icon name="arrow" size={14} />
  </div>
);

window.Dashboard = Dashboard;
