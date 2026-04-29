/* Page: Upload */

const PageUpload = ({ sessionId, docs, setDocs, refreshDocs, setRoute }) => {
  const [drag,      setDrag]      = React.useState(false);
  const [pending,   setPending]   = React.useState([]);   // File objects
  const [uploading, setUploading] = React.useState(false);
  const [progress,  setProgress]  = React.useState(0);
  const [errors,    setErrors]    = React.useState([]);

  const totalChunks = docs.reduce((s, d) => s + (d.chunks || 0), 0);
  const fileTypeLabel = t => ({ pdf: "PDF", csv: "CSV", md: "MD", txt: "TXT" }[t] || "DOC");

  const addFiles = (fileList) => {
    const allowed = ['.pdf', '.csv', '.txt', '.md'];
    const ok = Array.from(fileList).filter(f => allowed.some(ext => f.name.toLowerCase().endsWith(ext)));
    if (ok.length) setPending(prev => [...prev, ...ok]);
  };

  const startUpload = async () => {
    if (pending.length === 0 || uploading) return;
    setUploading(true);
    setProgress(0);
    setErrors([]);

    const total = pending.length;
    let done = 0;

    for (const file of pending) {
      try {
        await API.uploadDocument(sessionId, file, p => {
          setProgress(((done + p) / total) * 100);
        });
        done += 1;
        setProgress((done / total) * 100);
      } catch (e) {
        setErrors(prev => [...prev, `${file.name}: ${e.message}`]);
        done += 1;
      }
    }

    setPending([]);
    setUploading(false);
    setProgress(0);
    refreshDocs();
  };

  return (
    <div className="fade-in">
      <div className="row mb-32" style={{ justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <div className="eyebrow mb-8">Step 01 — Curate</div>
          <h1 className="h-display" style={{ fontSize: 32 }}>
            Bring your <span className="italic serif">market data.</span>
          </h1>
          <div className="muted mt-8" style={{ maxWidth: 560 }}>
            Upload PDFs, CSVs, notes, or transcripts. We chunk, embed, and index them locally — your reports cite back to the exact passage.
          </div>
        </div>
        <button className="btn btn-ghost" onClick={() => setRoute("research")}>
          Skip to research <Icon name="arrow" size={14} />
        </button>
      </div>

      <div className="grid-3 mb-24">
        <div className="kpi">
          <div className="kpi-label">Indexed files</div>
          <div className="kpi-value tnum">{docs.length}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Knowledge chunks</div>
          <div className="kpi-value tnum">{totalChunks}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">State</div>
          <div className="kpi-value" style={{ fontSize: 18, color: docs.length ? "var(--accent)" : "var(--fg-muted)" }}>
            {docs.length ? "READY" : "EMPTY"}
          </div>
        </div>
      </div>

      {/* Drop zone */}
      <div
        className={`dropzone mb-24 ${drag ? "drag" : ""}`}
        onDragOver={e => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); addFiles(e.dataTransfer.files); }}
        onClick={() => {
          const inp = document.createElement('input');
          inp.type = 'file';
          inp.multiple = true;
          inp.accept = '.pdf,.csv,.txt,.md';
          inp.onchange = e => addFiles(e.target.files);
          inp.click();
        }}
      >
        <div className="dropzone-icon"><Icon name="upload" size={20} /></div>
        <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 4 }}>Drop files here, or click to browse</div>
        <div className="dim" style={{ fontSize: 12 }}>PDF · CSV · TXT · Markdown · up to {50} MB each</div>
      </div>

      {/* Pending queue */}
      {pending.length > 0 && (
        <div className="card mb-24 fade-in">
          <div className="row mb-16" style={{ justifyContent: "space-between" }}>
            <h2>{pending.length} file{pending.length > 1 ? "s" : ""} ready to index</h2>
            <button className="btn btn-primary btn-sm" onClick={startUpload} disabled={uploading}>
              {uploading
                ? <><span className="spinner"></span> Indexing…</>
                : <><Icon name="bolt" size={13} /> Index all</>}
            </button>
          </div>
          <div className="col gap-8">
            {pending.map((f, i) => (
              <div key={i} className="file-row">
                <div className="file-icon">{fileTypeLabel(f.name.split('.').pop())}</div>
                <div>
                  <div className="file-name">{f.name}</div>
                  <div className="file-meta">{(f.size / 1024).toFixed(0)} KB</div>
                </div>
                <span className="dim mono" style={{ fontSize: 11 }}>queued</span>
                <span className="dim" style={{ fontSize: 11 }}>—</span>
                <button className="btn btn-ghost btn-sm"
                        onClick={() => setPending(pending.filter((_, j) => j !== i))}>
                  <Icon name="close" size={12} />
                </button>
              </div>
            ))}
          </div>
          {uploading && (
            <div className="mt-16">
              <div className="row mb-8" style={{ justifyContent: "space-between", fontSize: 12 }}>
                <span className="muted">Parsing → chunking → embedding</span>
                <span className="mono dim tnum">{Math.round(progress)}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${progress}%` }}></div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <div className="card mb-24 fade-in" style={{ borderColor: "var(--neg)" }}>
          <div className="eyebrow mb-8" style={{ color: "var(--neg)" }}>Upload errors</div>
          {errors.map((e, i) => <div key={i} className="muted" style={{ fontSize: 13 }}>{e}</div>)}
        </div>
      )}

      {/* Indexed files table */}
      {docs.length > 0 && (
        <div className="card">
          <div className="row mb-16" style={{ justifyContent: "space-between" }}>
            <h2>Indexed in this session</h2>
            <span className="dim mono" style={{ fontSize: 11 }}>{docs.length} files · {totalChunks} chunks</span>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>File</th><th>Type</th><th>Size</th><th>Chunks</th><th>Indexed</th><th></th>
              </tr>
            </thead>
            <tbody>
              {docs.map(d => (
                <tr key={d.id}>
                  <td>
                    <div className="row gap-12">
                      <div className="file-icon" style={{ width: 28, height: 28 }}>{fileTypeLabel(d.type)}</div>
                      <span style={{ fontWeight: 500 }}>{d.name}</span>
                    </div>
                  </td>
                  <td className="muted">{d.type.toUpperCase()}</td>
                  <td className="muted mono tnum">{d.size}</td>
                  <td className="mono tnum">{d.chunks}</td>
                  <td className="dim">{d.indexed}</td>
                  <td>
                    <button className="btn btn-ghost btn-sm"
                            onClick={async () => {
                              try {
                                await API.deleteDocument(sessionId, d.id);
                                setDocs(docs.filter(x => x.id !== d.id));
                              } catch (e) {
                                alert('Delete failed: ' + e.message);
                              }
                            }}>
                      <Icon name="close" size={12} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {docs.length > 0 && (
        <div className="row mt-24" style={{ justifyContent: "flex-end" }}>
          <button className="btn btn-primary" onClick={() => setRoute("research")}>
            Continue to research <Icon name="arrow" size={14} />
          </button>
        </div>
      )}
    </div>
  );
};

window.PageUpload = PageUpload;
