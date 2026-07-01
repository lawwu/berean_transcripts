const state = {
  manifest: null,
  dbCache: new Map(),
  sqlReady: null,
};

const els = {
  query: document.getElementById("query"),
  searchBtn: document.getElementById("search"),
  latestBtn: document.getElementById("latest"),
  filters: document.getElementById("filters"),
  status: document.getElementById("status"),
  results: document.getElementById("results"),
  selectAll: document.getElementById("select-all"),
  selectNone: document.getElementById("select-none"),
  viewer: document.getElementById("viewer"),
  viewerTitle: document.getElementById("viewer-title"),
  viewerMeta: document.getElementById("viewer-meta"),
  viewerBody: document.getElementById("viewer-body"),
};

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

function setStatus(message) {
  els.status.textContent = message;
}

function clearResults() {
  els.results.innerHTML = "";
}

function renderResults(items) {
  clearResults();
  if (!items.length) {
    els.results.innerHTML =
      '<div class="empty">No results yet. Try a different keyword or load a different year.</div>';
    return;
  }
  const fragment = document.createDocumentFragment();
  for (const item of items) {
    const card = document.createElement("article");
    card.className = "result";
    card.innerHTML = `
      <h3>${item.title}</h3>
      <div class="meta">
        <span>${formatDate(item.upload_date)}</span>
        <span>${formatDuration(item.duration)}</span>
        <span>${item.year}</span>
      </div>
      <p class="snippet">${item.snippet || ""}</p>
      <div class="result-actions">
        <button class="btn secondary view-transcript" data-id="${item.id}" data-year="${item.year}">
          Read transcript
        </button>
        <a class="link-pill" href="./viewer.html#id=${item.id}&year=${item.year}">Open viewer</a>
        <a class="link-pill" href="${item.url}" target="_blank" rel="noopener">Watch video</a>
      </div>
    `;
    fragment.appendChild(card);
  }
  els.results.appendChild(fragment);
}

function selectedYears() {
  const inputs = [...els.filters.querySelectorAll("input[type=checkbox]")];
  return inputs.filter((i) => i.checked).map((i) => i.value);
}

async function loadManifest() {
  const response = await fetch("./db/manifest.json");
  state.manifest = await response.json();
}

function renderFilters() {
  const years = state.manifest.entries.map((e) => e.year).sort().reverse();
  els.filters.innerHTML = "";
  for (const year of years) {
    const entry = state.manifest.entries.find((e) => e.year === year);
    const label = document.createElement("label");
    label.innerHTML = `
      <input type="checkbox" value="${year}" checked>
      <span>${year} (${entry.count})</span>
    `;
    els.filters.appendChild(label);
  }
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

function showViewer(data, year) {
  if (!data) return;
  els.viewer.hidden = false;
  els.viewerTitle.textContent = data.title || data.id;
  els.viewerMeta.innerHTML = `
    <span>${formatDate(data.upload_date)}</span>
    <span>${formatDuration(data.duration)}</span>
    <span>${year}</span>
    <a class="link-pill" href="${data.url}" target="_blank" rel="noopener">Watch video</a>
  `;
  const paragraphs = toParagraphs(data.text || "");
  els.viewerBody.innerHTML = paragraphs.map((p) => `<p>${p}</p>`).join("");
  els.viewer.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function runSearch() {
  const query = els.query.value.trim();
  if (!query) {
    setStatus("Enter a keyword or phrase to search.");
    renderResults([]);
    return;
  }
  const years = selectedYears();
  if (!years.length) {
    setStatus("Select at least one year.");
    return;
  }
  setStatus(`Searching ${years.length} shard(s)...`);
  const perShardLimit = 60;
  const results = [];
  for (const year of years) {
    const db = await loadDb(year);
    if (!db) continue;
    const rows = dbQuery(
      db,
      `
      SELECT t.id, t.title, t.upload_date, t.duration, t.url,
             snippet(transcripts_fts, 1, '<mark>', '</mark>', '…', 12) as snippet,
             bm25(transcripts_fts) as score
      FROM transcripts_fts
      JOIN transcripts t ON t.rowid = transcripts_fts.rowid
      WHERE transcripts_fts MATCH ?
      ORDER BY bm25(transcripts_fts)
      LIMIT ?;
      `,
      [query, perShardLimit]
    ).map((row) => ({ ...row, year }));
    results.push(...rows);
  }
  results.sort((a, b) => {
    if (a.score !== b.score) return a.score - b.score;
    return (b.upload_date || "").localeCompare(a.upload_date || "");
  });
  setStatus(`Found ${results.length} results across ${years.length} shard(s).`);
  renderResults(results.slice(0, 150));
}

async function loadLatest() {
  const years = selectedYears();
  if (!years.length) {
    setStatus("Select at least one year.");
    return;
  }
  setStatus(`Loading latest messages from ${years.length} shard(s)...`);
  const perShardLimit = 30;
  const results = [];
  for (const year of years) {
    const db = await loadDb(year);
    if (!db) continue;
    const rows = dbQuery(
      db,
      `
      SELECT id, title, upload_date, duration, url,
             '' as snippet
      FROM transcripts
      ORDER BY upload_date DESC
      LIMIT ?;
      `,
      [perShardLimit]
    ).map((row) => ({ ...row, year }));
    results.push(...rows);
  }
  results.sort((a, b) => (b.upload_date || "").localeCompare(a.upload_date || ""));
  setStatus(`Showing ${Math.min(120, results.length)} recent messages.`);
  renderResults(results.slice(0, 120));
}

function wireControls() {
  els.searchBtn.addEventListener("click", runSearch);
  els.latestBtn.addEventListener("click", loadLatest);
  els.query.addEventListener("keydown", (event) => {
    if (event.key === "Enter") runSearch();
  });
  els.results.addEventListener("click", async (event) => {
    const button = event.target.closest(".view-transcript");
    if (!button) return;
    const id = button.dataset.id;
    const year = button.dataset.year;
    setStatus(`Loading transcript ${id}...`);
    const data = await loadTranscript(id, year);
    if (!data) {
      setStatus("Transcript not found in selected shard.");
      return;
    }
    setStatus("Transcript loaded.");
    showViewer(data, year);
  });
  els.selectAll.addEventListener("click", () => {
    els.filters
      .querySelectorAll("input[type=checkbox]")
      .forEach((input) => (input.checked = true));
  });
  els.selectNone.addEventListener("click", () => {
    els.filters
      .querySelectorAll("input[type=checkbox]")
      .forEach((input) => (input.checked = false));
  });
}

async function init() {
  await loadManifest();
  renderFilters();
  wireControls();
  setStatus("Ready. Search the archive or load the latest messages.");
}

init();
