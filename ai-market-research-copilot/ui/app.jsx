/* Main application state and server-owned report job polling. */

const { useCallback, useEffect, useState } = React;

const REPORT_STEPS = [
  "Preparing sources",
  "Executive summary",
  "Competitor analysis",
  "Pricing analysis",
  "Trend analysis",
  "SWOT analysis",
  "Rendering PDF",
];

const App = () => {
  const [sessionId] = useState(() => API.getSessionId());
  const [route, setRoute] = useState("dashboard");

  const [docs, setDocs] = useState([]);
  const [reports, setReports] = useState([]);
  const [report, setReport] = useState(null);
  const [messages, setMessages] = useState([]);
  const [health, setHealth] = useState(false);
  const [topic, setTopic] = useState("");
  const [activeReportId, setActiveReportId] = useState(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobStage, setJobStage] = useState("");
  const [generationError, setGenerationError] = useState("");

  const mergeReport = useCallback((raw) => {
    setReports((current) => {
      const others = current.filter((item) => item.id !== raw.id);
      return [raw, ...others];
    });
  }, []);

  const selectReport = useCallback((raw) => {
    setReport(API.normalizeReport(raw));
    setTopic(raw.topic || "");
    setRoute("report");
  }, []);

  useEffect(() => {
    let cancelled = false;
    const bootstrap = async () => {
      const [healthData, documentData, reportData, history] = await Promise.all([
        API.checkHealth(),
        API.listDocuments(sessionId).catch(() => []),
        API.listReports(sessionId).catch(() => []),
        API.getChatHistory(sessionId).catch(() => []),
      ]);
      if (cancelled) return;
      setHealth(healthData || null);
      setDocs(documentData);
      setReports(reportData);
      setMessages(history.map((message) => ({
        role: message.role === "assistant" ? "ai" : message.role,
        content: message.content,
        sources: message.sources || [],
      })));

      const active = reportData.find((item) => ["pending", "generating"].includes(item.status));
      if (active) {
        setActiveReportId(active.id);
        setTopic(active.topic || "");
        setJobProgress(active.progress || 0);
        setJobStage(active.current_stage || "Queued");
      }
      const latestDone = reportData.find((item) => item.status === "done");
      if (latestDone) {
        setReport(API.normalizeReport(latestDone));
        if (!active) setTopic(latestDone.topic || "");
      }
    };
    bootstrap();
    return () => { cancelled = true; };
  }, [sessionId]);

  useEffect(() => {
    if (!activeReportId) return undefined;
    let cancelled = false;
    let timer;

    const poll = async () => {
      try {
        const raw = await API.getReport(sessionId, activeReportId);
        if (cancelled) return;
        mergeReport(raw);
        setJobProgress(raw.progress || 0);
        setJobStage(raw.current_stage || "Generating report");
        if (raw.status === "done") {
          setReport(API.normalizeReport(raw));
          setTopic(raw.topic || "");
          setActiveReportId(null);
          setGenerationError("");
          return;
        }
        if (raw.status === "failed") {
          setGenerationError(raw.error_message || "Report generation failed.");
          setActiveReportId(null);
          return;
        }
      } catch (error) {
        if (!cancelled) setJobStage("Reconnecting to report job");
      }
      if (!cancelled) timer = window.setTimeout(poll, 3000);
    };

    const onVisibility = () => {
      if (document.visibilityState === "visible") poll();
    };
    document.addEventListener("visibilitychange", onVisibility);
    poll();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [activeReportId, mergeReport, sessionId]);

  const refreshDocs = useCallback(() => {
    API.listDocuments(sessionId).then(setDocs).catch(() => {});
  }, [sessionId]);

  const onGenerate = useCallback(async () => {
    if (!topic.trim() || activeReportId) return;
    setGenerationError("");
    setJobProgress(0);
    setJobStage("Submitting report job");
    try {
      const response = await API.generateReport(sessionId, topic.trim());
      const reportId = response.data && response.data.report_id;
      if (!reportId) throw new Error("Backend did not return a report id");
      setActiveReportId(reportId);
    } catch (error) {
      setGenerationError(error.message || "Unable to start report generation");
    }
  }, [activeReportId, sessionId, topic]);

  const openLatestReport = useCallback(() => {
    if (report) setRoute("report");
  }, [report]);

  const generating = activeReportId !== null;
  const hasReport = report !== null || reports.some((item) => item.status === "done");
  const currentStep = Math.min(
    REPORT_STEPS.length - 1,
    Math.max(0, Math.floor((jobProgress / 100) * REPORT_STEPS.length)),
  );

  const crumbsMap = {
    dashboard: ["Marketscope", "Overview"],
    upload: ["Marketscope", "Sources"],
    research: ["Marketscope", "Research"],
    report: ["Marketscope", "Reports", topic || "Report"],
    chat: ["Marketscope", "Ask"],
  };

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
        health={health}
        onSelectReport={selectReport}
      />
      <div className="main">
        <TopBar crumbs={crumbsMap[route]} health={health} />
        {generating && (
          <div className="job-bar" role="status" aria-live="polite">
            <span className="spinner" aria-hidden="true"></span>
            <div className="job-copy">
              <strong>{jobStage || "Generating report"}</strong>
              <span>{jobProgress}% complete. You can use any workspace view while this runs.</span>
            </div>
            <div className="job-progress" aria-hidden="true">
              <span style={{ width: `${jobProgress}%` }}></span>
            </div>
            <button className="btn btn-sm" onClick={() => setRoute("research")}>View job</button>
          </div>
        )}
        <main className="scroll" data-screen-label={route}>
          {route === "dashboard" && (
            <Dashboard setRoute={setRoute} setTopic={setTopic} docs={docs} reports={reports} health={health} />
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
              progress={jobProgress}
              currentStep={currentStep}
              currentStage={jobStage}
              steps={REPORT_STEPS}
              error={generationError}
              reportReady={Boolean(report)}
              onOpenReport={openLatestReport}
            />
          )}
          {route === "report" && (
            <PageReport
              report={report}
              reports={reports}
              sessionId={sessionId}
              setRoute={setRoute}
              onSelectReport={selectReport}
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
        </main>
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
