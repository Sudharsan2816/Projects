/* Page: Report */

const PageReport = ({ report, reports, sessionId, setRoute, onSelectReport }) => {
  const [tab, setTab] = React.useState("summary");

  if (!report) {
    // Show a picker if we have reports but none selected, or empty state
    const doneReports = (reports || []).filter(r => r.status === 'done');
    if (doneReports.length === 0) {
      return (
        <div className="fade-in" style={{ display: "grid", placeItems: "center", height: "60vh" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 22, fontFamily: "var(--font-serif)", marginBottom: 8 }}>No report yet.</div>
            <div className="muted mb-24" style={{ fontSize: 13 }}>Head to Research to generate your first report.</div>
            <button className="btn btn-primary" onClick={() => setRoute("research")}>
              <Icon name="sparkle" size={14} /> Generate a report
            </button>
          </div>
        </div>
      );
    }
    return (
      <div className="fade-in">
        <div className="eyebrow mb-16">Available Reports</div>
        <div className="col gap-12">
          {doneReports.map(r => (
            <button key={r.id} type="button" className="card report-picker" onClick={() => onSelectReport(r)}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>{r.topic}</div>
                  <div className="dim mono" style={{ fontSize: 12 }}>#{r.id} · {API.relativeTime(r.created_at)}</div>
                </div>
                <span className="badge badge-pos">DONE</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  }

  const m = report;
  const swotSignals = Object.values(m.swot || {}).reduce((s, v) => s + (v || []).length, 0);

  return (
    <div className="fade-in">
      <div className="row mb-24" style={{ justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <div className="eyebrow mb-8">
            Report · <span className="mono">#{m.id}</span> · {API.relativeTime(m.createdAt)}
          </div>
          <h1 className="h-display" style={{ fontSize: 30, lineHeight: 1.1 }}>{m.topic}</h1>
        </div>
        <div className="row gap-8">
          <button className="btn" onClick={() => setRoute("research")}>
            <Icon name="refresh" size={13} /> New report
          </button>
          {m.downloadReady && (
            <a
              className="btn btn-primary"
              href={API.reportDownloadUrl(sessionId, m.id)}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Icon name="download" size={13} /> Export PDF
            </a>
          )}
        </div>
      </div>

      <div className="grid-4 mb-24">
        <ReportStat label="Competitors"  value={m.competitors.length}  icon="target" />
        <ReportStat label="Pricing tiers" value={m.pricing.length}     icon="dollar" />
        <ReportStat label="Trends"        value={m.trends.length}      icon="trend" />
        <ReportStat label="SWOT signals"  value={swotSignals}           icon="shield" />
      </div>

      <div className="tabs">
        {[
          ["summary",     "Executive Summary"],
          ["competitors", "Competitors",  m.competitors.length],
          ["pricing",     "Pricing",      m.pricing.length],
          ["trends",      "Trends",       m.trends.length],
          ["swot",        "SWOT"],
        ].map(([k, l, c]) => (
          <button type="button" key={k} className={`tab ${tab === k ? "tab-active" : ""}`} onClick={() => setTab(k)}>
            {l}{c != null && <span className="tab-count tnum">{c}</span>}
          </button>
        ))}
      </div>

      {tab === "summary" && <SummaryTab summary={m.executiveSummary} setRoute={setRoute} reportId={m.id} sessionId={sessionId} downloadReady={m.downloadReady} />}
      {tab === "competitors" && <CompetitorsTab data={m.competitors} />}
      {tab === "pricing"     && <PricingTab     data={m.pricing} />}
      {tab === "trends"      && <TrendsTab      data={m.trends} />}
      {tab === "swot"        && <SwotTab        data={m.swot} />}
    </div>
  );
};

const ReportStat = ({ label, value, icon }) => (
  <div className="kpi">
    <div className="row" style={{ justifyContent: "space-between" }}>
      <div className="kpi-label">{label}</div>
      <div style={{ color: "var(--fg-dim)" }}><Icon name={icon} size={14} /></div>
    </div>
    <div className="kpi-value tnum">{value}</div>
  </div>
);

const SummaryTab = ({ summary, setRoute, reportId, sessionId, downloadReady }) => (
  <div className="grid-2 fade-in" style={{ gridTemplateColumns: "1.7fr 1fr", gap: 24 }}>
    <div className="card" style={{ padding: 28 }}>
      <div className="eyebrow mb-16">Executive synthesis</div>
      {summary ? (
        <div style={{ fontFamily: "var(--font-serif)", fontSize: 18, lineHeight: 1.55, color: "var(--fg)", whiteSpace: "pre-wrap" }}>
          {summary}
        </div>
      ) : (
        <div className="muted" style={{ fontSize: 14 }}>Summary not available.</div>
      )}
      <div className="row mt-24 gap-8" style={{ paddingTop: 20, borderTop: "1px solid var(--border)" }}>
        <button className="btn btn-primary btn-sm" onClick={() => setRoute("chat")}>
          <Icon name="chat" size={13} /> Ask follow-ups
        </button>
        {reportId && downloadReady && (
          <a className="btn btn-sm" href={API.reportDownloadUrl(sessionId, reportId)} target="_blank" rel="noopener noreferrer">
            <Icon name="download" size={13} /> Export PDF
          </a>
        )}
      </div>
    </div>
    <div className="col gap-16">
      <div className="card">
        <div className="eyebrow mb-12">Review status</div>
        <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 8 }}>AI generated</div>
        <div className="muted" style={{ fontSize: 12 }}>
          Verify material claims and figures against source documents before making decisions.
        </div>
      </div>
      <div className="card">
        <div className="eyebrow mb-12">Next steps</div>
        <div className="col gap-8">
          <button className="btn btn-sm" style={{ justifyContent: "flex-start" }} onClick={() => setRoute("chat")}>
            <Icon name="chat" size={13} /> Deep-dive with Chat
          </button>
          <button className="btn btn-sm" style={{ justifyContent: "flex-start" }} onClick={() => setRoute("research")}>
            <Icon name="sparkle" size={13} /> Generate new report
          </button>
        </div>
      </div>
    </div>
  </div>
);

const CompetitorsTab = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="muted fade-in" style={{ fontSize: 14, padding: "24px 0" }}>No competitor data available.</div>;
  }
  const colors = ["#C8E25C", "#7BB7E8", "#E89A7B", "#B89AE5", "#E8C97B"];
  return (
    <div className="fade-in">
      <div className="col gap-16">
        {data.map((c, i) => (
          <div key={c.name || i} className="card card-hover">
            <div className="row mb-12" style={{ justifyContent: "space-between" }}>
              <div className="row gap-12">
                <div style={{ fontSize: 17, fontWeight: 600 }}>{c.name}</div>
                <span className={`badge ${
                  c.position === "Leader"     ? "badge-pos"  :
                  c.position === "Challenger" ? "badge-warn" :
                  c.position === "Niche"      ? "badge-info" : "badge-accent"
                }`}>{c.position}</span>
              </div>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span className="legend-swatch" style={{ background: colors[i % colors.length], width: 10, height: 10, borderRadius: 3 }}></span>
                {c.pricing && (
                  <div className="mono tnum" style={{ fontSize: 12 }}>{c.pricing}</div>
                )}
              </div>
            </div>
            {c.desc && <div className="muted" style={{ fontSize: 13, marginBottom: 16 }}>{c.desc}</div>}
            <div className="grid-2 gap-16">
              {c.strengths.length > 0 && (
                <div>
                  <div className="eyebrow mb-8" style={{ color: "var(--pos)" }}>Strengths</div>
                  <ul className="col gap-6">
                    {c.strengths.map((s, j) => (
                      <li key={j} className="muted" style={{ fontSize: 13, paddingLeft: 14, position: "relative" }}>
                        <span style={{ position: "absolute", left: 0, color: "var(--pos)" }}>+</span>{s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {c.weaknesses.length > 0 && (
                <div>
                  <div className="eyebrow mb-8" style={{ color: "var(--neg)" }}>Weaknesses</div>
                  <ul className="col gap-6">
                    {c.weaknesses.map((s, j) => (
                      <li key={j} className="muted" style={{ fontSize: 13, paddingLeft: 14, position: "relative" }}>
                        <span style={{ position: "absolute", left: 0, color: "var(--neg)" }}>−</span>{s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const PricingTab = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="muted fade-in" style={{ fontSize: 14, padding: "24px 0" }}>No pricing data available.</div>;
  }
  const max = Math.max(...data.map(d => d.mid || 0), 1);
  return (
    <div className="fade-in">
      {data.some(p => p.mid > 0) && (
        <div className="card mb-24">
          <div className="row mb-16" style={{ justifyContent: "space-between" }}>
            <h2>Pricing intelligence</h2>
            <span className="dim mono" style={{ fontSize: 12 }}>Price range by segment</span>
          </div>
          <div className="col gap-12">
            {data.map(p => (
              <div key={p.segment} className="bar-row" style={{ gridTemplateColumns: "180px 1fr 100px" }}>
                <div className="bar-label" style={{ color: "var(--fg)", fontWeight: 500 }}>{p.segment}</div>
                <div className="bar-track" style={{ height: 10 }}>
                  <div className="bar-fill" style={{
                    width: `${p.mid ? (p.mid / max) * 100 : 30}%`,
                    background: "var(--accent)"
                  }}></div>
                </div>
                <div className="bar-value">{p.range}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="grid-2 gap-16">
        {data.map(p => (
          <div key={p.segment} className="card card-hover">
            <div className="row mb-8" style={{ justifyContent: "space-between" }}>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{p.segment}</div>
              <div className="mono" style={{ color: "var(--accent)", fontSize: 14 }}>{p.range}</div>
            </div>
            {p.notes && <div className="muted" style={{ fontSize: 13, marginBottom: 12 }}>{p.notes}</div>}
            {p.players.length > 0 && (
              <div className="row gap-6" style={{ flexWrap: "wrap" }}>
                {p.players.map(pl => <span key={pl} className="chip">{pl}</span>)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const TrendsTab = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="muted fade-in" style={{ fontSize: 14, padding: "24px 0" }}>No trend data available.</div>;
  }
  return (
    <div className="fade-in col gap-12">
      {data.map((t, i) => (
        <div key={i} className="card card-hover">
          <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
            <div className="grow">
              <div className="row gap-8 mb-8">
                <span className={`badge ${
                  t.impact === "High"   ? "badge-neg"  :
                  t.impact === "Medium" ? "badge-warn" : "badge-info"
                }`}>{t.impact} impact</span>
                <span className="dim mono" style={{ fontSize: 11 }}>{t.timeframe}</span>
              </div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>{t.trend}</div>
              <div className="muted" style={{ fontSize: 13, maxWidth: 720 }}>{t.description}</div>
            </div>
            <div className="mono tnum dim" style={{ fontSize: 11 }}>0{i + 1}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

const SwotTab = ({ data }) => {
  if (!data) return null;
  return (
    <div className="fade-in">
      <div className="swot">
        <SwotCell title="Strengths"     items={data.strengths     || []} cls="swot-s" color="var(--pos)"  />
        <SwotCell title="Weaknesses"    items={data.weaknesses    || []} cls="swot-w" color="var(--neg)"  />
        <SwotCell title="Opportunities" items={data.opportunities || []} cls="swot-o" color="var(--info)" />
        <SwotCell title="Threats"       items={data.threats       || []} cls="swot-t" color="var(--warn)" />
      </div>
    </div>
  );
};

const SwotCell = ({ title, items, cls, color }) => (
  <div className={`swot-cell ${cls}`}>
    <div className="swot-title" style={{ color }}>{title}</div>
    <ul className="swot-list">
      {items.map((it, i) => <li key={i} className="swot-item">{it}</li>)}
    </ul>
  </div>
);

window.PageReport = PageReport;
