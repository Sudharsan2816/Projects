/* Main app — real backend wiring */

const { useState, useEffect, useCallback } = React;

const App = () => {
  const [sessionId]   = useState(() => API.getSessionId());
  const [route, setRoute] = useState("dashboard");

  const [docs,    setDocs]    = useState([]);
  const [reports, setReports] = useState([]);
  const [report,  setReport]  = useState(null);  // normalised current report
  const [messages, setMessages] = useState([]);
  const [health,  setHealth]  = useState(false);

  const [topic,       setTopic]       = useState("");
  const [generating,  setGenerating]  = useState(false);
  const [genProgress, setGenProgress] = useState(0);
  const [genStep,     setGenStep]     = useState(0);

  const steps = [
    "Analysing topic & retrieving context",
    "Extracting competitor intelligence",
    "Mining pricing insights",
    "Identifying market trends",
    "Performing SWOT analysis",
    "Rendering report",
  ];

  // ── Initial load ─────────────────────────────────────────────────────────────
  useEffect(() => {
    API.checkHealth().then(h => setHealth(h || null));
    API.listDocuments(sessionId).then(setDocs).catch(() => {});
    API.listReports(sessionId).then(r => {
      setReports(r);
      if (r.length > 0 && r[0].status === 'done') {
        setReport(API.normalizeReport(r[0]));
        setTopic(r[0].topic || '');
      }
    }).catch(() => {});
    API.getChatHistory(sessionId).then(hist => {
      setMessages(hist.map(m => ({
        role: m.role === 'assistant' ? 'ai' : m.role,
        content: m.content,
        sources: m.sources || [],
      })));
    }).catch(() => {});
  }, [sessionId]);

  // ── Reload docs helper ────────────────────────────────────────────────────────
  const refreshDocs = useCallback(() => {
    API.listDocuments(sessionId).then(setDocs).catch(() => {});
  }, [sessionId]);

  // ── Generate report ───────────────────────────────────────────────────────────
  const onGenerate = useCallback(async () => {
    if (!topic.trim() || generating) return;
    setGenerating(true);
    setGenProgress(0);
    setGenStep(0);

    let reportId;
    try {
      const res = await API.generateReport(sessionId, topic);
      reportId = res.data?.report_id;
    } catch (e) {
      alert('Failed to start report: ' + e.message);
      setGenerating(false);
      return;
    }

    // Animate steps while polling
    const totalSteps = steps.length;
    const stepDuration = 8000 / totalSteps;  // ~8 s visual animation
    let s = 0;
    const stepTimer = setInterval(() => {
      s += 1;
      setGenStep(s);
      setGenProgress(Math.min(95, (s / totalSteps) * 100));
      if (s >= totalSteps) clearInterval(stepTimer);
    }, stepDuration);

    // Poll the actual report
    const poll = async () => {
      while (true) {
        await new Promise(r => setTimeout(r, 3000));
        try {
          const r = await API.getReport(sessionId, reportId);
          if (r.status === 'done') {
            clearInterval(stepTimer);
            setGenProgress(100);
            setGenStep(totalSteps);
            setGenerating(false);
            const norm = API.normalizeReport(r);
            setReport(norm);
            setReports(prev => {
              const others = prev.filter(x => x.id !== r.id);
              return [r, ...others];
            });
            setTimeout(() => setRoute("report"), 400);
            return;
          }
          if (r.status === 'failed') {
            clearInterval(stepTimer);
            setGenerating(false);
            alert('Report generation failed. Check backend logs.');
            return;
          }
        } catch {}
      }
    };
    poll();
  }, [topic, generating, sessionId]);

  const hasReport = report !== null || reports.some(r => r.status === 'done');

  const crumbsMap = {
    dashboard: ["Marketscope", "Dashboard"],
    upload:    ["Marketscope", "Workspace", "Upload"],
    research:  ["Marketscope", "Workspace", "Research"],
    report:    ["Marketscope", "Reports", topic.length > 40 ? topic.slice(0, 40) + "…" : (topic || "Report")],
    chat:      ["Marketscope", "Workspace", "Chat"],
  };

  // ── Theme ─────────────────────────────────────────────────────────────────────
  const [tweaks, setTweak] = useTweaks({
    "theme":       "dark",
    "accent":      "lime",
    "displayFont": "Instrument Serif",
    "uiFont":      "Geist",
  });

  useEffect(() => {
    document.body.dataset.theme = tweaks.theme;
    const accents = {
      lime:    "oklch(0.86 0.18 120)",
      amber:   "oklch(0.82 0.16 75)",
      coral:   "oklch(0.74 0.17 30)",
      sky:     "oklch(0.78 0.14 230)",
      magenta: "oklch(0.72 0.20 340)",
      mint:    "oklch(0.84 0.14 165)",
    };
    const a = accents[tweaks.accent] || accents.lime;
    document.body.style.setProperty("--accent", a);
    document.body.style.setProperty("--accent-dim", a.replace(")", " / 0.18)"));
    const fg = (tweaks.theme === "light" || ["amber","lime","mint"].includes(tweaks.accent))
      ? "#0A0B14" : "#FFFFFF";
    document.body.style.setProperty("--accent-fg", fg);
    document.body.style.setProperty("--font-sans",  `'${tweaks.uiFont}', system-ui, sans-serif`);
    document.body.style.setProperty("--font-serif", `'${tweaks.displayFont}', Georgia, serif`);
    const fontMap = {
      "Geist":             "Geist:wght@400;500;600;700",
      "Inter":             "Inter:wght@400;500;600;700",
      "IBM Plex Sans":     "IBM+Plex+Sans:wght@400;500;600;700",
      "Manrope":           "Manrope:wght@400;500;600;700",
      "Instrument Serif":  "Instrument+Serif:ital@0;1",
      "Fraunces":          "Fraunces:ital,wght@0,400;1,400",
      "EB Garamond":       "EB+Garamond:ital,wght@0,400;1,400",
      "Playfair Display":  "Playfair+Display:ital@0;1",
    };
    [tweaks.uiFont, tweaks.displayFont].forEach(f => {
      if (!fontMap[f]) return;
      const id = `gf-${f.replace(/\s/g, "-")}`;
      if (!document.getElementById(id)) {
        const link = document.createElement("link");
        link.id = id; link.rel = "stylesheet";
        link.href = `https://fonts.googleapis.com/css2?family=${fontMap[f]}&display=swap`;
        document.head.appendChild(link);
      }
    });
  }, [tweaks]);

  return (
    <div className="app">
      <Sidebar
        route={route}
        setRoute={setRoute}
        docCount={docs.length}
        hasReport={hasReport}
        msgCount={messages.length || undefined}
        reports={reports}
        sessionId={sessionId}
      />
      <div className="main">
        <TopBar crumbs={crumbsMap[route]} health={health} />
        <div className="scroll" data-screen-label={route}>
          {route === "dashboard" && (
            <Dashboard
              setRoute={setRoute}
              docs={docs}
              reports={reports}
              health={health}
            />
          )}
          {route === "upload" && (
            <PageUpload
              sessionId={sessionId}
              docs={docs}
              setDocs={setDocs}
              refreshDocs={refreshDocs}
              setRoute={setRoute}
            />
          )}
          {route === "research" && (
            <PageResearch
              topic={topic}
              setTopic={setTopic}
              onGenerate={onGenerate}
              generating={generating}
              progress={genProgress}
              currentStep={genStep}
              steps={steps}
            />
          )}
          {route === "report" && (
            <PageReport
              report={report}
              reports={reports}
              sessionId={sessionId}
              setRoute={setRoute}
            />
          )}
          {route === "chat" && (
            <PageChat
              sessionId={sessionId}
              messages={messages}
              setMessages={setMessages}
              docs={docs}
            />
          )}
        </div>
      </div>

      <TweaksPanel title="Tweaks">
        <TweakSection title="Theme">
          <TweakRadio label="Mode" value={tweaks.theme} onChange={v => setTweak("theme", v)} options={[
            { value: "dark",  label: "Dark" },
            { value: "light", label: "Light" },
          ]} />
          <TweakSelect label="Accent" value={tweaks.accent} onChange={v => setTweak("accent", v)} options={[
            { value: "lime",    label: "Chartreuse (default)" },
            { value: "amber",   label: "Amber" },
            { value: "coral",   label: "Coral" },
            { value: "sky",     label: "Sky" },
            { value: "magenta", label: "Magenta" },
            { value: "mint",    label: "Mint" },
          ]} />
        </TweakSection>
        <TweakSection title="Typography">
          <TweakSelect label="Display font" value={tweaks.displayFont} onChange={v => setTweak("displayFont", v)} options={[
            { value: "Instrument Serif", label: "Instrument Serif" },
            { value: "Fraunces",         label: "Fraunces" },
            { value: "EB Garamond",      label: "EB Garamond" },
            { value: "Playfair Display", label: "Playfair Display" },
          ]} />
          <TweakSelect label="UI font" value={tweaks.uiFont} onChange={v => setTweak("uiFont", v)} options={[
            { value: "Geist",        label: "Geist" },
            { value: "Inter",        label: "Inter" },
            { value: "IBM Plex Sans",label: "IBM Plex Sans" },
            { value: "Manrope",      label: "Manrope (legacy)" },
          ]} />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
