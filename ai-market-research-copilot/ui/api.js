// Marketscope API — wires the React UI to the FastAPI backend.

// ── Session management ────────────────────────────────────────────────────────

function createSessionId() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16));
}

function startSession() {
  const id = createSessionId();
  localStorage.setItem('marketscope_session', id);
  return id;
}

function getSessionId() {
  return localStorage.getItem('marketscope_session') || startSession();
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

const API_TOKEN_STORAGE_KEY = 'marketscope_api_token';
let apiTokenPromptPromise = null;

function getApiToken() {
  return sessionStorage.getItem(API_TOKEN_STORAGE_KEY) || '';
}

function authHeaders(headers = {}) {
  const token = getApiToken();
  return token ? { ...headers, 'X-API-Key': token } : headers;
}

function requestApiToken() {
  // Several protected requests run together during startup. Share one prompt so
  // their simultaneous 401 responses do not ask for the same token repeatedly.
  if (!apiTokenPromptPromise) {
    apiTokenPromptPromise = Promise.resolve()
      .then(() => window.prompt('This deployment is private. Enter its access token:'))
      .then((token) => {
        const normalized = (token || '').trim();
        if (normalized) sessionStorage.setItem(API_TOKEN_STORAGE_KEY, normalized);
        return normalized;
      })
      .finally(() => {
        apiTokenPromptPromise = null;
      });
  }
  return apiTokenPromptPromise;
}

async function apiFetch(path, options = {}, retried = false) {
  const tokenAtRequestStart = getApiToken();
  const response = await fetch(window.API_BASE + path, {
    ...options,
    headers: authHeaders(options.headers || {}),
  });
  if (response.status === 401 && !retried) {
    // Another concurrent request may already have collected the token while this
    // request was in flight. Retry with it instead of displaying another prompt.
    const currentToken = getApiToken();
    if (currentToken && currentToken !== tokenAtRequestStart) {
      return apiFetch(path, options, true);
    }
    if (await requestApiToken()) {
      return apiFetch(path, options, true);
    }
  }
  return response;
}

async function apiGet(path) {
  const res = await apiFetch(path);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

async function apiPost(path, body) {
  const res = await apiFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

async function apiDelete(path) {
  const res = await apiFetch(path, { method: 'DELETE' });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

// ── Data normalisers ──────────────────────────────────────────────────────────

function normalizeDoc(d) {
  const kb = d.file_size_kb || 0;
  const size = kb >= 1024 ? (kb / 1024).toFixed(1) + ' MB' : kb.toFixed(0) + ' KB';
  const ago = d.created_at ? relativeTime(d.created_at) : 'indexed';
  return {
    id: d.id,
    name: d.filename,
    type: d.file_type || 'doc',
    size,
    chunks: d.chunk_count || 0,
    indexed: ago,
    brief: d.brief || '',
    briefStatus: d.brief_status || (d.brief ? 'ready' : 'pending'),
  };
}

function normalizeReport(r) {
  const competitors = (r.competitors || []).map(c => ({
    name: c.name || c.company_name || 'Unknown',
    position: c.market_position || c.position || 'Niche',
    desc: c.description || '',
    share: c.market_share || null,
    growth: c.yoy_growth || null,
    pricing: c.pricing || c.price_range || null,
    strengths: c.strengths || [],
    weaknesses: c.weaknesses || [],
    scores: null,
  }));

  const pricing = (r.pricing_insights || []).map(p => ({
    segment: p.segment || p.tier || '',
    range: p.price_range || p.range || '',
    mid: parseMidPrice(p.price_range || p.range || ''),
    notes: p.notes || p.insight || '',
    players: p.key_players || p.players || [],
  }));

  const trends = (r.market_trends || []).map(t => ({
    trend: t.trend || t.name || '',
    description: t.description || t.desc || '',
    impact: t.impact || 'Medium',
    timeframe: t.timeframe || '',
  }));

  const swot = r.swot_analysis || { strengths: [], weaknesses: [], opportunities: [], threats: [] };

  return {
    id: r.id,
    topic: r.topic || '',
    status: r.status || 'pending',
    progress: r.progress || 0,
    currentStage: r.current_stage || '',
    errorMessage: r.error_message || '',
    executiveSummary: r.executive_summary || '',
    competitors,
    pricing,
    trends,
    swot,
    citations: [],
    createdAt: r.created_at,
    downloadReady: Boolean(r.download_ready),
    sourceDocumentIds: r.source_document_ids || [],
    sourceDocumentNames: r.source_document_names || [],
  };
}

function parseMidPrice(range) {
  const nums = (range || '').match(/[\d.]+/g);
  if (!nums) return 0;
  if (nums.length >= 2) return (parseFloat(nums[0]) + parseFloat(nums[1])) / 2;
  return parseFloat(nums[0]) || 0;
}

function relativeTime(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return Math.floor(diff / 60) + ' min ago';
  if (diff < 86400) return Math.floor(diff / 3600) + ' hr ago';
  return Math.floor(diff / 86400) + ' days ago';
}

// ── API calls ─────────────────────────────────────────────────────────────────

async function checkHealth() {
  try {
    const data = await apiGet('/health');
    return data;
  } catch {
    return null;
  }
}

async function listDocuments(sessionId) {
  const data = await apiGet(`/api/v1/upload/${sessionId}/documents`);
  return data.map(normalizeDoc);
}

async function uploadDocument(sessionId, file, onProgress, resetSession = false) {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('session_id', sessionId);
  fd.append('reset_session', resetSession ? 'true' : 'false');

  const send = (retried = false) => new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', window.API_BASE + '/api/v1/upload/');
    const token = getApiToken();
    if (token) xhr.setRequestHeader('X-API-Key', token);
    if (onProgress) xhr.upload.onprogress = (e) => onProgress(e.loaded / e.total);
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else if (xhr.status === 401 && !retried) {
        requestApiToken().then((token) => {
          if (token) send(true).then(resolve, reject);
          else reject(new Error('Valid API credentials are required'));
        }, reject);
      } else {
        let msg = `Upload error ${xhr.status}`;
        try { msg = JSON.parse(xhr.responseText).detail || msg; } catch {}
        reject(new Error(msg));
      }
    };
    xhr.onerror = () => reject(new Error('Network error during upload'));
    xhr.send(fd);
  });
  return send();
}

async function deleteDocument(sessionId, docId) {
  return apiDelete(`/api/v1/upload/${sessionId}/documents/${docId}`);
}

async function generateDocumentBrief(sessionId, docId) {
  return apiPost(`/api/v1/upload/${sessionId}/documents/${docId}/brief`, {});
}

async function generateReport(sessionId, topic, documentIds = []) {
  return apiPost('/api/v1/research/generate', {
    session_id: sessionId,
    topic,
    document_ids: documentIds,
  });
}

async function getReport(sessionId, reportId) {
  return apiGet(`/api/v1/research/${sessionId}/reports/${reportId}`);
}

async function listReports(sessionId) {
  return apiGet(`/api/v1/research/${sessionId}/reports`);
}

async function downloadReport(sessionId, reportId) {
  const path = `/api/v1/report/${encodeURIComponent(sessionId)}/${reportId}/download`;
  const response = await apiFetch(path);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Download error ${response.status}`);
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const disposition = response.headers.get('Content-Disposition') || '';
  const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = filenameMatch ? filenameMatch[1] : `market-research-${reportId}.pdf`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

async function* chatStream(sessionId, message) {
  const res = await apiFetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) throw new Error(`Chat error ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try { yield JSON.parse(line.slice(6)); } catch {}
      }
    }
  }
}

async function getChatHistory(sessionId) {
  return apiGet(`/api/v1/chat/${sessionId}/history`);
}

async function clearChatHistory(sessionId) {
  return apiDelete(`/api/v1/chat/${sessionId}/history`);
}

window.API = {
  getSessionId,
  startSession,
  checkHealth,
  listDocuments,
  uploadDocument,
  deleteDocument,
  generateDocumentBrief,
  generateReport,
  getReport,
  listReports,
  downloadReport,
  chatStream,
  getChatHistory,
  clearChatHistory,
  normalizeReport,
  normalizeDoc,
  relativeTime,
};
