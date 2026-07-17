/* Client-side search over per-year SQLite shards (sql.js + FTS5).
   Shards are fetched lazily per selected year and cached for the session. */

const state = {
  manifest: null,
  dbCache: new Map(), // year -> Promise<SQL.Database>
  sqlReady: null,
};

const els = {
  query: document.getElementById("query"),
  searchBtn: document.getElementById("search-btn"),
  filters: document.getElementById("year-filters"),
  status: document.getElementById("status"),
  results: document.getElementById("results"),
  selectAll: document.getElementById("select-all"),
  selectRecent: document.getElementById("select-recent"),
};

const RECENT_YEARS = 3;
const MAX_RESULTS = 50;

function setStatus(message) {
  els.status.textContent = message || "";
}

function initSql() {
  if (!state.sqlReady) {
    state.sqlReady = initSqlJs({ locateFile: (f) => `assets-v2/sqljs/${f}` });
  }
  return state.sqlReady;
}

async function loadManifest() {
  const res = await fetch("db/manifest.json");
  state.manifest = await res.json();
  renderYearPills();
}

function years() {
  return state.manifest.entries.map((e) => e.year).sort().reverse();
}

function renderYearPills() {
  const all = years();
  const recent = new Set(all.slice(0, RECENT_YEARS));
  els.filters.innerHTML = "";
  for (const year of all) {
    const pill = document.createElement("button");
    pill.className = "year-pill";
    pill.type = "button";
    pill.textContent = year;
    pill.setAttribute("aria-pressed", recent.has(year) ? "true" : "false");
    pill.addEventListener("click", () => {
      const on = pill.getAttribute("aria-pressed") === "true";
      pill.setAttribute("aria-pressed", on ? "false" : "true");
    });
    els.filters.appendChild(pill);
  }
}

function selectedYears() {
  return [...els.filters.querySelectorAll('[aria-pressed="true"]')].map(
    (p) => p.textContent
  );
}

function setAllYears(on) {
  els.filters
    .querySelectorAll(".year-pill")
    .forEach((p) => p.setAttribute("aria-pressed", on ? "true" : "false"));
}

function setRecentYears() {
  const recent = new Set(years().slice(0, RECENT_YEARS));
  els.filters
    .querySelectorAll(".year-pill")
    .forEach((p) =>
      p.setAttribute("aria-pressed", recent.has(p.textContent) ? "true" : "false")
    );
}

async function loadShard(year) {
  if (!state.dbCache.has(year)) {
    const entry = state.manifest.entries.find((e) => e.year === year);
    const promise = (async () => {
      const SQL = await initSql();
      const res = await fetch(`db/${entry.db}`);
      const buf = await res.arrayBuffer();
      return new SQL.Database(new Uint8Array(buf));
    })();
    state.dbCache.set(year, promise);
  }
  return state.dbCache.get(year);
}

function queryAll(db, sql, params) {
  const stmt = db.prepare(sql);
  const rows = [];
  try {
    stmt.bind(params);
    while (stmt.step()) rows.push(stmt.getAsObject());
  } finally {
    stmt.free();
  }
  return rows;
}

/* Quote each token so user input can't break FTS5 MATCH syntax. */
function ftsQuery(raw) {
  const tokens = raw.match(/[\p{L}\p{N}']+/gu) || [];
  return tokens.map((t) => `"${t.replaceAll('"', "")}"`).join(" ");
}

function formatHms(totalSeconds) {
  const s = Math.floor(totalSeconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
}

function formatDate(raw) {
  return raw && raw.length === 8
    ? `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6)}`
    : raw || "";
}

const PARAGRAPH_SQL = `
  SELECT p.sermon_id AS id, p.idx AS idx, p.start_s AS start_s,
         snippet(paragraphs_fts, 0, '[[', ']]', '…', 14) AS snip,
         s.title AS title, s.upload_date AS upload_date
  FROM paragraphs_fts f
  JOIN paragraphs p ON p.id = f.rowid
  JOIN sermons s ON s.id = p.sermon_id
  WHERE paragraphs_fts MATCH :q
  ORDER BY rank
  LIMIT 20
`;

const TITLE_SQL = `
  SELECT id, title, upload_date FROM sermons
  WHERE title LIKE :like ORDER BY upload_date DESC LIMIT 10
`;

async function search() {
  const raw = els.query.value.trim();
  if (!raw) return;
  const q = ftsQuery(raw);
  if (!q) return;
  const chosen = selectedYears();
  if (!chosen.length) {
    setStatus("Pick at least one year to search.");
    return;
  }
  els.results.innerHTML = "";
  const titleHits = [];
  const paraHits = [];
  let loaded = 0;
  for (const year of chosen.sort().reverse()) {
    setStatus(`Searching ${year}… (${++loaded}/${chosen.length})`);
    try {
      const db = await loadShard(year);
      titleHits.push(...queryAll(db, TITLE_SQL, { ":like": `%${raw}%` }));
      paraHits.push(...queryAll(db, PARAGRAPH_SQL, { ":q": q }));
    } catch (err) {
      console.error(`shard ${year}:`, err);
    }
    renderResults(titleHits, paraHits); // progressive render per shard
    if (titleHits.length + paraHits.length >= MAX_RESULTS) break;
  }
  const total = titleHits.length + paraHits.length;
  setStatus(
    total
      ? `${total} result${total === 1 ? "" : "s"}`
      : "No results — try different words or more years."
  );
}

/* snippet() output is plain transcript text with [[ ]] markers; escape
   everything, then swap markers for <mark>. */
function snippetHtml(snip) {
  return escapeHtml(snip)
    .replaceAll("[[", "<mark>")
    .replaceAll("]]", "</mark>");
}

function renderResults(titleHits, paraHits) {
  els.results.innerHTML = "";
  const fragment = document.createDocumentFragment();
  for (const hit of titleHits.slice(0, 10)) {
    const card = document.createElement("a");
    card.className = "result-card";
    card.href = `sermons/${hit.id}.html`;
    card.innerHTML = `
      <div class="result-meta"><span>${formatDate(hit.upload_date)}</span><span>title match</span></div>
      <div class="result-title">${escapeHtml(hit.title)}</div>`;
    fragment.appendChild(card);
  }
  for (const hit of paraHits.slice(0, MAX_RESULTS)) {
    const card = document.createElement("a");
    card.className = "result-card";
    card.href = `sermons/${hit.id}.html#p${hit.idx}`;
    card.innerHTML = `
      <div class="result-meta"><span>${formatDate(hit.upload_date)}</span><span class="ts">→ ${formatHms(hit.start_s)}</span></div>
      <div class="result-title">${escapeHtml(hit.title)}</div>
      <div class="result-snippet">${snippetHtml(hit.snip)}</div>`;
    fragment.appendChild(card);
  }
  if (!fragment.childNodes.length) {
    els.results.innerHTML = '<div class="empty">No results yet.</div>';
    return;
  }
  els.results.appendChild(fragment);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

els.searchBtn.addEventListener("click", search);
els.query.addEventListener("keydown", (e) => {
  if (e.key === "Enter") search();
});
els.selectAll.addEventListener("click", () => setAllYears(true));
els.selectRecent.addEventListener("click", setRecentYears);

loadManifest().catch((err) => {
  console.error(err);
  setStatus("Could not load the search index.");
});
