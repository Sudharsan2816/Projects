/* Sidebar + topbar shell components */

const Icon = ({ name, size = 16 }) => {
  const paths = {
    home:     "M3 11l9-8 9 8v9a2 2 0 0 1-2 2h-4v-7h-6v7H5a2 2 0 0 1-2-2v-9z",
    upload:   "M12 3v12m0-12l-4 4m4-4l4 4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2",
    sparkle:  "M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3zM18 14l.8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14z",
    chart:    "M3 3v18h18M7 14l4-4 4 4 5-6",
    chat:     "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z",
    search:   "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3",
    plus:     "M12 5v14M5 12h14",
    download: "M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2",
    arrow:    "M5 12h14M13 5l7 7-7 7",
    file:     "M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6zM14 3v6h6",
    check:    "M5 12l5 5L20 7",
    close:    "M18 6L6 18M6 6l12 12",
    send:     "M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z",
    settings: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z",
    chevron:  "M9 6l6 6-6 6",
    refresh:  "M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5",
    pdf:      "M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6zM14 3v6h6M9 13h6M9 17h4",
    csv:      "M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6zM14 3v6h6M8 13v4M12 13v4M16 13v4",
    text:     "M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6zM14 3v6h6M9 13h6M9 17h6M9 9h2",
    bolt:     "M13 2L3 14h7v8l10-12h-7V2z",
    target:   "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12zM12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
    trend:    "M3 17l6-6 4 4 8-8M14 7h7v7",
    dollar:   "M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",
    shield:   "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
    flag:     "M4 22V4m0 0h11l-2 4 2 4H4",
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d={paths[name] || ""} />
    </svg>
  );
};

const Sidebar = ({ route, setRoute, docCount, hasReport, msgCount, reports, sessionId }) => {
  const items = [
    { id: "dashboard", label: "Dashboard",  icon: "home" },
    { id: "upload",    label: "Upload",      icon: "upload",  count: docCount },
    { id: "research",  label: "Research",    icon: "sparkle" },
    { id: "report",    label: "Report",      icon: "chart",   badge: hasReport ? "•" : null },
    { id: "chat",      label: "Chat",        icon: "chat",    count: msgCount || undefined },
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">M</div>
        <div className="col">
          <div className="brand-name">Marketscope</div>
          <div className="brand-sub">Research Copilot</div>
        </div>
      </div>

      <div className="nav-section-label">Workspace</div>
      {items.map(it => (
        <div
          key={it.id}
          className={`nav-item ${route === it.id ? "active" : ""}`}
          onClick={() => setRoute(it.id)}
        >
          <Icon name={it.icon} />
          <span>{it.label}</span>
          {it.count != null && it.count > 0 && <span className="nav-count tnum">{it.count}</span>}
          {it.badge && <span className="nav-count" style={{ color: "var(--accent)" }}>{it.badge}</span>}
        </div>
      ))}

      {reports && reports.length > 0 && (
        <>
          <div className="nav-section-label">Recent Reports</div>
          {reports.slice(0, 3).map(r => (
            <div key={r.id} className="nav-item" onClick={() => setRoute("report")}
                 style={{ paddingTop: 6, paddingBottom: 6 }}>
              <div className="col gap-4" style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12.5, color: "var(--fg-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {r.topic}
                </div>
                <div className="dim" style={{ fontSize: 10.5 }}>
                  {API.relativeTime(r.created_at)}
                </div>
              </div>
            </div>
          ))}
        </>
      )}

      <div className="session-card">
        <div className="session-label">Session</div>
        <div className="session-id">{sessionId || "…"}</div>
        <div className="session-pulse">
          <span className="pulse-dot"></span>
          Backend connected
        </div>
      </div>
    </aside>
  );
};

const TopBar = ({ crumbs, health }) => (
  <div className="topbar">
    <div className="crumb">
      {(crumbs || []).map((c, i) => (
        <React.Fragment key={i}>
          {i > 0 && <span className="crumb-sep">/</span>}
          <span className={i === crumbs.length - 1 ? "crumb-current" : ""}>{c}</span>
        </React.Fragment>
      ))}
    </div>
    <div className="topbar-actions">
      <div className="status-pill">
        <span className={`status-dot ${health === null ? "neg" : health === false ? "warn" : ""}`}></span>
        {health === null ? "Backend offline" : health ? `${health.llm_provider || "LLM"} ready` : "Connecting…"}
      </div>
    </div>
  </div>
);

Object.assign(window, { Icon, Sidebar, TopBar });
