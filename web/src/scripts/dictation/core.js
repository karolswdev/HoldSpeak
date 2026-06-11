// ── Core: shared state, HTTP, utilities, and the section switcher ────
// The kernel every dictation behavior module imports from. Holds the one
// shared mutable `state` object, the `api` fetch wrapper, the escape/format
// helpers, and `activateSection` with its section-loader registry (feature
// modules register their tab loader here, so cross-module "reload that
// section" calls never need a direct import — keeping the module graph
// acyclic).

function loadRecentProjectRoots() {
  try {
    const raw = JSON.parse(localStorage.getItem("holdspeak.recentProjectRoots") || "[]");
    return Array.isArray(raw) ? raw.filter((x) => typeof x === "string" && x.trim()).slice(0, 6) : [];
  } catch (_e) {
    return [];
  }
}

export const state = {
  scope: "global",
  document: null,
  path: null,
  project: null,
  exists: false,
  selectedId: null,
  editorMode: "idle", // idle | new | edit
  draft: null,
  templates: [],
  projectRootOverride: localStorage.getItem("holdspeak.projectRootOverride") || "",
  recentProjectRoots: loadRecentProjectRoots(),
  activeSection: "blocks",
  agentSession: null,
  hooks: null,
};

// ── HTTP ─────────────────────────────────────────────────────────────
export async function api(method, url, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  let data = null;
  try { data = await r.json(); } catch (_e) { /* empty */ }
  if (!r.ok) {
    const err = new Error((data && data.error) || `HTTP ${r.status}`);
    err.status = r.status;
    err.data = data;
    throw err;
  }
  return data;
}

// ── Helpers ──────────────────────────────────────────────────────────
export function deepClone(o) { return JSON.parse(JSON.stringify(o)); }
export function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
}

export function escapeAttr(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export function relativeTime(iso) {
  const then = new Date(iso).getTime();
  if (!Number.isFinite(then)) return "";
  const secs = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (secs < 60) return "just now";
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

export function basename(path) {
  const text = String(path || "").replace(/\/+$/, "");
  if (!text) return "";
  const parts = text.split("/");
  return parts[parts.length - 1] || text;
}

export function plural(n, word) {
  return Number(n) === 1 ? word : `${word}s`;
}

// HS-48-02: the inline "learned from N similar" trust chip. One renderer for the
// dry-run result, journal entries, and the Memory list. Quiet at N=0 — never a
// claim of learning that did not happen.
export function learnSigChip(similar) {
  const n = Number(similar) || 0;
  if (n <= 0) return "";
  return `<span class="learn-sig" title="How many journal utterances this nudge reaches — counted by the same matcher that routes">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m12 3 2.2 5.4L20 9.6l-4 4 1 5.8L12 16.8 7 19.4l1-5.8-4-4 5.8-1.2z"/></svg>
    learned from ${n} similar</span>`;
}

export function projectRootParam(prefix) {
  const value = state.projectRootOverride.trim();
  return value ? `${prefix}project_root=${encodeURIComponent(value)}` : "";
}

// ── Section switching ────────────────────────────────────────────────
// Feature modules register their tab loader at module-eval time; switching
// to a section invokes its registered loader. `loadSection` is also how a
// module reloads *another* module's section (e.g. knowledge saving → refresh
// readiness) without importing it directly.
const sectionLoaders = {};

export function registerSection(name, loader) {
  sectionLoaders[name] = loader;
}

export function loadSection(name) {
  const loader = sectionLoaders[name];
  if (loader) loader();
}

export function activateSection(name) {
  state.activeSection = name;
  // HS-40-03: each `.view` carries the `hidden` attribute in markup, and
  // `.view[hidden] { display: none }` outranks the base `.view { display: flex }`
  // rule — so clearing the inline display alone leaves a switched-to tab blank
  // (a pre-existing bug: every non-default tab rendered empty). Drive `hidden`
  // itself: clear it on the active view (base rule shows it), set it on the
  // rest. This is what makes runtime / readiness / KB / … actually render.
  const views = {
    readiness: "view-readiness",
    blocks: "view-blocks",
    kb: "view-kb",
    hs: "view-hs",
    hooks: "view-hooks",
    runtime: "view-runtime",
    memory: "view-memory",
    journal: "view-journal",
    "dry-run": "view-dry-run",
  };
  for (const [key, id] of Object.entries(views)) {
    const el = document.getElementById(id);
    if (!el) continue;
    const active = key === name;
    el.hidden = !active;
    el.style.display = active ? "" : "none";
  }
  document.querySelectorAll('.scope-row button[data-section]').forEach((b) =>
    b.classList.toggle("active", b.dataset.section === name)
  );
  loadSection(name);
}

// ── Shared render helpers ────────────────────────────────────────────
// Runtime guidance + telemetry are rendered from more than one tab
// (readiness, runtime, knowledge, dry-run), so they live here.
export function renderRuntimeGuidance(guidance) {
  if (!guidance) return "";
  const commands = (guidance.commands || []).map((item) => `
    <div class="command-snippet">
      <code>${escapeHtml(item.command || "")}</code>
      <button class="btn" data-copy-command="${escapeAttr(item.command || "")}">Copy</button>
    </div>
  `).join("");
  const modelPath = guidance.model_path
    ? `<p>missing path: <code>${escapeHtml(guidance.model_path)}</code></p>`
    : "";
  const links = (guidance.links || []).map((link) =>
    `<a href="${escapeAttr(link.target || "#")}">${escapeHtml(link.label || "Docs")}</a>`
  ).join(" · ");
  const bundle = guidance.command_bundle && (guidance.commands || []).length > 1
    ? `<button class="btn primary" data-copy-command="${escapeAttr(guidance.command_bundle)}" style="margin-top:10px;">Copy all setup commands</button>`
    : "";
  return `
    <div class="guidance-block">
      <strong>${escapeHtml(guidance.title || "Runtime guidance")}</strong>
      <p>${escapeHtml(guidance.summary || "")}</p>
      ${modelPath}
      <p>${escapeHtml(guidance.next_step || "")}</p>
      ${commands}
      ${bundle}
      ${links ? `<p>${links}</p>` : ""}
    </div>
  `;
}

export function wireCopyCommandButtons(root) {
  root.querySelectorAll("button[data-copy-command]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await navigator.clipboard.writeText(btn.dataset.copyCommand || "");
      btn.textContent = "Copied";
      setTimeout(() => { btn.textContent = "Copy"; }, 1200);
    });
  });
}

export function renderDryTelemetry(telemetry) {
  if (!telemetry || !telemetry.status) return "";
  const latency = telemetry.latency || {};
  const fallbacks = telemetry.fallbacks || [];
  const fallbackText = fallbacks.length
    ? fallbacks.map((f) => `${f.stage_id || "runtime"}: ${f.category || f.reason}`).join(" · ")
    : "none";
  return `
    <div class="meta-banner ${telemetry.status === "ok" ? "" : "warn"}">
      <strong>Telemetry:</strong>
      ${escapeHtml(telemetry.summary || telemetry.status)}
      · total ${Number(latency.total_elapsed_ms || 0).toFixed(2)} ms
      ${latency.max_total_latency_ms ? ` / budget ${Number(latency.max_total_latency_ms).toFixed(0)} ms` : ""}
      · fallback ${escapeHtml(fallbackText)}
    </div>
  `;
}
