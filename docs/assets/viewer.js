const els = {
  title: document.getElementById("viewer-title"),
  meta: document.getElementById("viewer-meta"),
  body: document.getElementById("viewer-body"),
  status: document.getElementById("status"),
};

const state = {
  manifest: null,
  idIndex: null,
  dbCache: new Map(),
  sqlReady: null,
};

function setStatus(message) {
  els.status.textContent = message;
}

function formatDate(raw) {
  if (!raw || raw.length !== 8) return raw || "";
  return `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6)}`;
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) return "";
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  const rem = mins % 60;
  return hrs ? `${hrs}h ${rem}m` : `${mins}m`;
}

function parseHash() {
  const hash = window.location.hash.replace(/^#/, "");
  const params = new URLSearchParams(hash);
  return {
    id: params.get("id"),
    year: params.get("year"),
  };
}

async function loadManifest() {
  const response = await fetch("./db/manifest.json");
  state.manifest = await response.json();
}

async function loadIdIndex() {
  const response = await fetch("./db/id_index.json");
  state.idIndex = await response.json();
}

async function initSql() {
  if (!state.sqlReady) {
    state.sqlReady = initSqlJs({
      locateFile: (file) =>
        `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.2/${file}`,
    });
  }
  return state.sqlReady;
}

async function loadDb(year) {
  if (state.dbCache.has(year)) {
    return state.dbCache.get(year);
  }
  const entry = state.manifest.entries.find((e) => e.year === year);
  if (!entry) return null;
  const response = await fetch(`./db/${entry.db}`);
  const buffer = await response.arrayBuffer();
  const SQL = await initSql();
  const db = new SQL.Database(new Uint8Array(buffer));
  state.dbCache.set(year, db);
  return db;
}

function dbQuery(db, sql, params = []) {
  const stmt = db.prepare(sql);
  stmt.bind(params);
  const rows = [];
  while (stmt.step()) {
    rows.push(stmt.getAsObject());
  }
  stmt.free();
  return rows;
}

function toParagraphs(text) {
  if (!text) return [];
  const sentences = text.split(/(?<=[.!?])\s+/);
  const paragraphs = [];
  let buffer = [];
  let wordCount = 0;
  for (const sentence of sentences) {
    const words = sentence.trim().split(/\s+/).filter(Boolean);
    if (!words.length) continue;
    buffer.push(sentence.trim());
    wordCount += words.length;
    if (wordCount >= 50) {
      paragraphs.push(buffer.join(" "));
      buffer = [];
      wordCount = 0;
    }
  }
  if (buffer.length) paragraphs.push(buffer.join(" "));
  return paragraphs;
}

async function loadTranscript(id, year) {
  const db = await loadDb(year);
  if (!db) return null;
  const rows = dbQuery(
    db,
    `
    SELECT id, title, upload_date, duration, url, text
    FROM transcripts
    WHERE id = ?
    LIMIT 1;
    `,
    [id]
  );
  return rows[0] || null;
}

function renderTranscript(data, year) {
  els.title.textContent = data.title || data.id;
  els.meta.innerHTML = `
    <span>${formatDate(data.upload_date)}</span>
    <span>${formatDuration(data.duration)}</span>
    <span>${year}</span>
    <a class="link-pill" href="${data.url}" target="_blank" rel="noopener">Watch video</a>
  `;
  const paragraphs = toParagraphs(data.text || "");
  els.body.innerHTML = paragraphs.map((p) => `<p>${p}</p>`).join("");
}

async function init() {
  setStatus("Loading transcript...");
  await loadManifest();
  await loadIdIndex();
  const { id, year } = parseHash();
  if (!id) {
    setStatus("Missing transcript id in URL.");
    return;
  }
  const resolvedYear = year || state.idIndex[id];
  if (!resolvedYear) {
    setStatus("Could not resolve year for this transcript.");
    return;
  }
  const data = await loadTranscript(id, resolvedYear);
  if (!data) {
    setStatus("Transcript not found.");
    return;
  }
  renderTranscript(data, resolvedYear);
  setStatus("Loaded.");
}

init();
