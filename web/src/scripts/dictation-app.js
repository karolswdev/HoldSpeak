const state = {
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

const PLACEHOLDER_RE = /\{([^{}]*)\}/g;
const VALID_NAME_RE = /^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$/;

// ── HTTP ─────────────────────────────────────────────────────────────
async function api(method, url, body) {
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

// ── Loading ──────────────────────────────────────────────────────────
async function loadScope(scope) {
  state.scope = scope;
  document.querySelectorAll('.scope-row button[data-scope]').forEach((b) =>
    b.classList.toggle("active", b.dataset.scope === scope)
  );
  const banner = document.getElementById("meta-banner");
  banner.classList.remove("warn", "error");
  banner.textContent = "Loading…";
  try {
    const data = await api("GET", `/api/dictation/blocks?scope=${scope}${scope === "project" ? projectRootParam("&") : ""}`);
    state.document = data.document;
    state.path = data.path;
    state.project = data.project;
    state.exists = data.exists;
    renderMeta();
    renderBlockList();
    state.selectedId = null;
    state.editorMode = "idle";
    renderEditor();
  } catch (e) {
    state.document = null;
    banner.classList.add(e.status === 404 ? "warn" : "error");
    banner.textContent = e.message;
    document.getElementById("block-list").innerHTML = "";
    state.editorMode = "idle";
    renderEditor();
  }
}

function renderMeta() {
  const banner = document.getElementById("meta-banner");
  const parts = [`scope: <strong>${state.scope}</strong>`, `path: ${escapeHtml(state.path || "—")}`];
  if (state.project) parts.push(`project: <strong>${escapeHtml(state.project.name)}</strong> (${escapeHtml(state.project.anchor)})`);
  if (!state.exists) parts.push(`<em style="color:var(--warn);">file does not exist yet — first write will create it</em>`);
  banner.innerHTML = parts.join("  ·  ");
}

function renderBlockList() {
  const list = document.getElementById("block-list");
  const blocks = (state.document && state.document.blocks) || [];
  if (!blocks.length) {
    list.innerHTML = `<div style="color:var(--muted);font-size:13px;">No blocks yet. Use "+ New block" to add one.</div>`;
    return;
  }
  list.innerHTML = blocks.map((b) => `
    <div class="block-card${b.id === state.selectedId ? " selected" : ""}" data-id="${escapeHtml(b.id)}">
      <div><span class="block-id">${escapeHtml(b.id)}</span><span class="pill">${escapeHtml(b.inject?.mode || "?")}</span></div>
      <div class="block-desc">${escapeHtml(b.description || "(no description)")}</div>
    </div>
  `).join("");
  list.querySelectorAll(".block-card").forEach((el) =>
    el.addEventListener("click", () => selectBlock(el.dataset.id))
  );
}

async function loadStarterTemplates() {
  try {
    const data = await api("GET", "/api/dictation/block-templates");
    state.templates = data.templates || [];
    renderStarterTemplates();
  } catch (e) {
    document.getElementById("template-list").innerHTML =
      `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

function renderStarterTemplates() {
  const host = document.getElementById("template-list");
  if (!state.templates.length) {
    host.innerHTML = `<div style="color:var(--muted);font-size:13px;">No starter templates available.</div>`;
    return;
  }
  host.innerHTML = state.templates.map((t) => `
    <div class="template-card">
      <div class="template-title">${escapeHtml(t.title)}</div>
      <div class="template-desc">${escapeHtml(t.description)}</div>
      <div style="font-family:var(--font-mono);font-size:12px;color:var(--muted);">${escapeHtml(t.sample_utterance || "")}</div>
      <div class="actions" style="margin-top:8px;">
        <button class="btn" data-template-id="${escapeAttr(t.id)}">Create</button>
        <button class="btn primary" data-template-dry-run-id="${escapeAttr(t.id)}">Create + dry-run</button>
      </div>
    </div>
  `).join("");
  host.querySelectorAll("button[data-template-id]").forEach((btn) => {
    btn.addEventListener("click", () => createFromTemplate(btn.dataset.templateId));
  });
  host.querySelectorAll("button[data-template-dry-run-id]").forEach((btn) => {
    btn.addEventListener("click", () => createFromTemplate(btn.dataset.templateDryRunId, { dryRun: true }));
  });
}

async function createFromTemplate(templateId, options = {}) {
  const msg = document.getElementById("template-msg");
  msg.innerHTML = "";
  const dryRun = !!options.dryRun;
  const targetScope = options.scope || state.scope;
  try {
    const data = await api(
      "POST",
      `/api/dictation/blocks/from-template?scope=${targetScope}${projectRootParam("&")}`,
      { template_id: templateId, dry_run: dryRun }
    );
    msg.innerHTML = `<div class="ok-box">Created ${escapeHtml(data.block.id)} from ${escapeHtml(data.template.title)}.</div>`;
    await loadScope(targetScope);
    if (data.block && data.block.id) selectBlock(data.block.id);
    if (dryRun && data.dry_run) {
      document.getElementById("dry-utterance").value =
        data.dry_run.sample_utterance || data.template.sample_utterance || "";
      activateSection("dry-run");
      renderDryRun(data.dry_run);
      document.getElementById("dry-msg").innerHTML =
        `<div class="ok-box">Created ${escapeHtml(data.block.id)} and ran the starter sample.</div>`;
    }
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

// ── Editor ───────────────────────────────────────────────────────────
function selectBlock(id) {
  state.selectedId = id;
  const blocks = (state.document && state.document.blocks) || [];
  const b = blocks.find((x) => x.id === id);
  if (!b) return;
  state.draft = deepClone(b);
  state.editorMode = "edit";
  renderBlockList();
  renderEditor();
}

function newBlock() {
  state.selectedId = null;
  state.draft = {
    id: "",
    description: "",
    match: { examples: [""], negative_examples: [], threshold: 0.7 },
    inject: { mode: "append", template: "{raw_text}\n" },
  };
  state.editorMode = "new";
  renderBlockList();
  renderEditor();
}

function renderEditor() {
  const titleEl = document.getElementById("editor-title");
  const editor = document.getElementById("editor");
  if (state.editorMode === "idle" || !state.draft) {
    titleEl.textContent = "Select a block to edit";
    editor.innerHTML = `<p style="color:var(--muted);font-size:13px;">Pick a block from the list, or click <strong>+ New block</strong>.</p>`;
    return;
  }
  const d = state.draft;
  titleEl.textContent = state.editorMode === "new" ? "New block" : `Edit: ${d.id}`;
  const extrasJson = d.match.extras_schema ? JSON.stringify(d.match.extras_schema, null, 2) : "";

  editor.innerHTML = `
    <label>id <input type="text" id="f-id" value="${escapeAttr(d.id)}" /></label>
    <label>description <input type="text" id="f-desc" value="${escapeAttr(d.description || "")}" /></label>

    <label>examples (one per line, at least one)
      <textarea id="f-examples">${escapeHtml((d.match.examples || []).join("\n"))}</textarea>
    </label>
    <label>negative examples (one per line, optional)
      <textarea id="f-neg">${escapeHtml((d.match.negative_examples || []).join("\n"))}</textarea>
    </label>

    <div class="row">
      <label>threshold (0.0–1.0)
        <input type="number" id="f-threshold" step="0.05" min="0" max="1" value="${d.match.threshold ?? ""}" />
      </label>
      <label>inject mode
        <select id="f-mode">
          ${["append", "prepend", "replace"].map((m) => `<option value="${m}"${m === d.inject.mode ? " selected" : ""}>${m}</option>`).join("")}
        </select>
      </label>
    </div>

    <label>template (placeholders: <code>{raw_text}</code> · <code>{project.name}</code> · <code>{project.kb.*}</code> · <code>{intent.extras.*}</code>)
      <textarea id="f-template">${escapeHtml(d.inject.template || "")}</textarea>
    </label>

    <label>extras_schema (JSON, optional — e.g. <code>{"stage": {"type": "enum", "values": ["draft","final"]}}</code>)
      <textarea id="f-extras" placeholder="leave blank for none">${escapeHtml(extrasJson)}</textarea>
    </label>

    <label>template preview against sample utterance
      <input type="text" id="f-sample" value="hello world" />
    </label>
    <div class="preview" id="preview"></div>

    <div id="msg"></div>

    <div class="actions">
      <button class="btn primary" id="btn-save">${state.editorMode === "new" ? "Create" : "Save"}</button>
      ${state.editorMode === "edit" ? `<button class="btn danger" id="btn-delete">Delete</button>` : ""}
      <button class="btn" id="btn-cancel">Cancel</button>
    </div>
  `;

  // Live preview wiring
  const previewInputs = ["f-template", "f-sample", "f-id"];
  previewInputs.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("input", refreshPreview);
  });
  document.getElementById("btn-save").addEventListener("click", saveDraft);
  document.getElementById("btn-cancel").addEventListener("click", () => {
    state.editorMode = "idle"; state.draft = null; state.selectedId = null;
    renderBlockList(); renderEditor();
  });
  const delBtn = document.getElementById("btn-delete");
  if (delBtn) delBtn.addEventListener("click", deleteDraft);

  refreshPreview();
}

function refreshPreview() {
  const tmplEl = document.getElementById("f-template");
  const sampleEl = document.getElementById("f-sample");
  const previewEl = document.getElementById("preview");
  if (!tmplEl || !previewEl) return;
  const tmpl = tmplEl.value;
  const sample = (sampleEl && sampleEl.value) || "";
  const ctx = {
    raw_text: sample,
    project: state.project ? { name: state.project.name, kb: state.project.kb || {} } : { name: "(no project)", kb: {} },
    intent: { extras: {} },
  };
  previewEl.innerHTML = renderTemplate(tmpl, ctx);
}

function renderTemplate(tmpl, ctx) {
  return escapeHtml(tmpl).replace(/\{([^{}]*)\}/g, (_m, raw) => {
    const inner = raw.trim();
    if (!inner) return `<span class="missing">{}</span>`;
    if (!VALID_NAME_RE.test(inner)) return `<span class="missing">{${escapeHtml(inner)}!}</span>`;
    const value = resolveDotted(ctx, inner);
    if (value === undefined) return `<span class="missing">{${escapeHtml(inner)}?}</span>`;
    return escapeHtml(String(value));
  });
}

function resolveDotted(obj, path) {
  const parts = path.split(".");
  let cur = obj;
  for (const p of parts) {
    if (cur && typeof cur === "object" && p in cur) cur = cur[p];
    else return undefined;
  }
  return cur;
}

// ── Save / delete ────────────────────────────────────────────────────
function collectDraft() {
  const get = (id) => document.getElementById(id);
  const examples = get("f-examples").value.split("\n").map((s) => s.trim()).filter(Boolean);
  const neg = get("f-neg").value.split("\n").map((s) => s.trim()).filter(Boolean);
  const thresholdRaw = get("f-threshold").value.trim();
  const threshold = thresholdRaw === "" ? null : Number(thresholdRaw);
  let extras = null;
  const extrasRaw = get("f-extras").value.trim();
  if (extrasRaw) {
    try { extras = JSON.parse(extrasRaw); }
    catch (e) { throw new Error(`extras_schema is not valid JSON: ${e.message}`); }
  }
  const block = {
    id: get("f-id").value.trim(),
    description: get("f-desc").value,
    match: { examples, negative_examples: neg },
    inject: { mode: get("f-mode").value, template: get("f-template").value },
  };
  if (threshold !== null && !Number.isNaN(threshold)) block.match.threshold = threshold;
  if (extras !== null) block.match.extras_schema = extras;
  return block;
}

async function saveDraft() {
  const msg = document.getElementById("msg");
  msg.innerHTML = "";
  let block;
  try { block = collectDraft(); }
  catch (e) { msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`; return; }
  try {
    if (state.editorMode === "new") {
      await api("POST", `/api/dictation/blocks?scope=${state.scope}${state.scope === "project" ? projectRootParam("&") : ""}`, { block });
    } else {
      await api("PUT", `/api/dictation/blocks/${encodeURIComponent(state.selectedId)}?scope=${state.scope}${state.scope === "project" ? projectRootParam("&") : ""}`, { block });
    }
    await loadScope(state.scope);
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

async function deleteDraft() {
  if (!state.selectedId) return;
  const ok = await window.holdspeakConfirm({
    title: `Delete block "${state.selectedId}"?`,
    body: "The block's match examples and injection template are removed from the local dictation taxonomy. Utterances that previously routed to this block will fall through to the next match.",
    scopeNote: "Only the local HoldSpeak block library is affected.",
    confirmLabel: "Delete block",
  });
  if (!ok) return;
  const msg = document.getElementById("msg");
  msg.innerHTML = "";
  try {
    await api("DELETE", `/api/dictation/blocks/${encodeURIComponent(state.selectedId)}?scope=${state.scope}${state.scope === "project" ? projectRootParam("&") : ""}`);
    await loadScope(state.scope);
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

// ── Helpers ──────────────────────────────────────────────────────────
function deepClone(o) { return JSON.parse(JSON.stringify(o)); }
function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
}
function escapeAttr(s) { return escapeHtml(s); }

// ── Project KB editor ───────────────────────────────────────────────
const kbState = { detected: null, kbPath: null, lastLoaded: null, rows: [] };
const HS_FILE_META = [
  ["instructions.md", "How HoldSpeak rewrites/injects prompts for this repo."],
  ["context.md", "Architecture, important paths, setup notes, and constraints."],
  ["memory.md", "Durable user-approved facts HoldSpeak may reuse."],
  ["workflows.md", "Common test, build, review, and deploy workflows."],
  ["issues.md", "Active scratchpad for current problems and decisions."],
  ["terms.md", "Project vocabulary, acronyms, and preferred spellings."],
  ["targets.md", "Per-target style notes for Codex, Claude, terminal, browser, editor, and chat."],
  ["ignore", "Paths, topics, or data HoldSpeak should not inject."],
];
const hsState = {
  detected: null,
  contextDir: null,
  contextDirExists: false,
  files: {},
  flatFiles: {},
  skipped: [],
  warnings: [],
  writePolicy: {},
  suggestion: null,
  selected: "instructions.md",
};

function activateSection(name) {
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
  if (name === "readiness") loadReadiness();
  if (name === "kb") loadKB();
  if (name === "hs") loadHSContext();
  if (name === "hooks") loadAgentHooks();
  if (name === "runtime") loadRuntime();
  if (name === "memory") loadMemory();
  if (name === "journal") loadJournal();
}

// ── Readiness snapshot ──────────────────────────────────────────────
async function loadReadiness() {
  const meta = document.getElementById("ready-meta");
  const cards = document.getElementById("ready-cards");
  const actions = document.getElementById("ready-actions");
  meta.classList.remove("warn", "error");
  meta.textContent = "Loading…";
  cards.innerHTML = "";
  actions.innerHTML = "";
  try {
    const data = await api("GET", `/api/dictation/readiness${projectRootParam("?")}`);
    renderReadiness(data);
  } catch (e) {
    meta.classList.add("error");
    meta.textContent = e.message;
  }
}

function renderReadiness(data) {
  const meta = document.getElementById("ready-meta");
  meta.classList.remove("warn", "error");
  if (!data.ready) meta.classList.add("warn");
  const project = data.project
    ? `${escapeHtml(data.project.name)} (${escapeHtml(data.project.anchor)} @ ${escapeHtml(data.project.root)})`
    : "(none selected)";
  meta.innerHTML =
    `status: <strong>${data.ready ? "ready" : "needs attention"}</strong>` +
    `  ·  project: <strong>${project}</strong>`;

  const blocks = data.blocks || {};
  const kb = data.project_kb || {};
  const runtime = data.runtime || {};
  const telemetry = data.telemetry || runtime.telemetry || {};
  const telemetryCounters = telemetry.counters || runtime.counters || {};
  const telemetryLatency = telemetry.latency || {};
  const telemetryFallbacks = telemetry.fallbacks || [];
  const target = data.target || {};
  const agentHooks = data.agent_hooks || {};
  const freshHooks = Object.entries(agentHooks)
    .filter(([_agent, entry]) => entry && entry.fresh)
    .map(([agent]) => agent);
  const config = data.config || {};
  document.getElementById("ready-cards").innerHTML = [
    readinessCard(
      "Pipeline",
      config.pipeline_enabled ? "enabled" : "disabled",
      config.pipeline_enabled ? "ok" : "warn",
      `${config.max_total_latency_ms || "?"} ms target`
    ),
    readinessCard(
      "Target",
      target.label || "Unknown",
      target.id && target.id !== "unknown" ? "ok" : "warn",
      `${target.source || "none"} · ${Math.round(Number(target.confidence || 0) * 100)}% confidence`
    ),
    readinessCard(
      "Blocks",
      `${blocks.resolved?.count ?? 0} loaded`,
      (blocks.resolved?.valid && (blocks.resolved?.count || 0) > 0) ? "ok" : "warn",
      `${blocks.resolved_scope || "global"} · ${blocks.resolved?.path || "no file"}`
    ),
    readinessCard(
      "Project KB",
      kb.exists ? `${(kb.keys || []).length} keys` : "missing",
      kb.valid && kb.exists ? "ok" : "warn",
      kb.path || "no project"
    ),
    readinessCard(
      "Runtime",
      runtime.status || "unknown",
      runtime.status === "available" ? "ok" : (runtime.status === "disabled" ? "warn" : "error"),
      runtime.resolved_backend || runtime.requested_backend || "not resolved"
    ),
    readinessCard(
      "Telemetry",
      telemetryFallbacks.length ? `${telemetryFallbacks.length} fallback` : `${telemetryCounters.classify_calls ?? 0} classify calls`,
      telemetryFallbacks.length ? "warn" : "ok",
      `budget ${telemetryLatency.max_total_latency_ms || config.max_total_latency_ms || "?"} ms · successes ${telemetryCounters.classify_successes ?? 0}`
    ),
    readinessCard(
      "Agent hooks",
      freshHooks.length ? `${freshHooks.join(" + ")} fresh` : "no recent hooks",
      freshHooks.length ? "ok" : "warn",
      "Claude/Codex hook context freshness"
    ),
  ].join("");

  const warnings = data.warnings || [];
  const actions = document.getElementById("ready-actions");
  if (!warnings.length) {
    actions.innerHTML = `<div class="ok-box">Ready for dry-run and live dictation.</div>`;
    return;
  }
  actions.innerHTML = warnings.map((w) => `
    <div class="${w.section === "runtime" && w.code !== "pipeline_disabled" ? "error-box" : "meta-banner warn"}">
      <strong>${escapeHtml(w.message)}</strong><br />
      <span>${escapeHtml(w.action || "")}</span>
      ${w.section && w.section !== "readiness" ? `<button class="btn" data-ready-section="${escapeAttr(w.section)}" style="float:right;">Open</button>` : ""}
      ${w.template_id ? `<button class="btn primary" data-ready-template-id="${escapeAttr(w.template_id)}" data-ready-template-scope="${escapeAttr(w.template_scope || "global")}" style="float:right;margin-right:8px;">Create + dry-run</button>` : ""}
      ${w.kb_action === "create_starter" ? `<button class="btn primary" data-ready-kb-starter="1" style="float:right;margin-right:8px;">Create starter KB</button>` : ""}
      ${w.runtime_action === "enable_pipeline" ? `<button class="btn primary" data-ready-runtime-action="enable_pipeline" style="float:right;margin-right:8px;">Enable pipeline</button>` : ""}
      ${renderRuntimeGuidance(w.guidance)}
    </div>
  `).join("");
  actions.querySelectorAll("button[data-ready-section]").forEach((btn) => {
    btn.addEventListener("click", () => activateSection(btn.dataset.readySection));
  });
  actions.querySelectorAll("button[data-ready-template-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      activateSection("blocks");
      createFromTemplate(btn.dataset.readyTemplateId, {
        dryRun: true,
        scope: btn.dataset.readyTemplateScope || "global",
      });
    });
  });
  actions.querySelectorAll("button[data-ready-kb-starter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      createStarterKB({ switchToKB: true });
    });
  });
  actions.querySelectorAll("button[data-ready-runtime-action]").forEach((btn) => {
    btn.addEventListener("click", () => enablePipelineFromReadiness());
  });
  wireCopyCommandButtons(actions);
}

function readinessCard(title, value, status, detail) {
  return `
    <div class="readiness-card ${status}">
      <strong>${escapeHtml(title)}</strong>
      <div class="value">${escapeHtml(value)}</div>
      <div style="color:var(--muted);font-size:12px;margin-top:8px;word-break:break-word;">${escapeHtml(detail || "")}</div>
    </div>
  `;
}

function renderRuntimeGuidance(guidance) {
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

function wireCopyCommandButtons(root) {
  root.querySelectorAll("button[data-copy-command]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await navigator.clipboard.writeText(btn.dataset.copyCommand || "");
      btn.textContent = "Copied";
      setTimeout(() => { btn.textContent = "Copy"; }, 1200);
    });
  });
}

async function loadKB() {
  const banner = document.getElementById("kb-meta-banner");
  banner.classList.remove("warn", "error");
  banner.textContent = "Loading…";
  try {
    const data = await api("GET", `/api/dictation/project-kb${projectRootParam("?")}`);
    kbState.detected = data.detected;
    kbState.kbPath = data.kb_path;
    kbState.lastLoaded = data.kb;
    kbState.rows = Object.entries(data.kb || {}).map(([k, v]) => ({ key: k, value: v ?? "" }));
    renderKBMeta(data);
    renderKBRows();
  } catch (e) {
    banner.classList.add("error");
    banner.textContent = e.message;
  }
}

function renderKBMeta(data) {
  const banner = document.getElementById("kb-meta-banner");
  if (!data.detected) {
    banner.classList.add("warn");
    banner.innerHTML = data.message || "no project root detected from cwd";
    return;
  }
  const d = data.detected;
  const parts = [
    `project: <strong>${escapeHtml(d.name)}</strong> (${escapeHtml(d.anchor)})`,
    `root: ${escapeHtml(d.root)}`,
    `path: ${escapeHtml(data.kb_path)}`,
  ];
  if (data.kb === null) parts.push(`<em style="color:var(--warn);">file does not exist yet — first save will create it</em>`);
  banner.innerHTML = parts.join("  ·  ");
}

function renderKBRows() {
  const host = document.getElementById("kb-rows");
  if (!kbState.detected) {
    host.innerHTML = `<p style="color:var(--muted);font-size:13px;">No project detected. Navigate <code>holdspeak</code> from inside a project directory.</p>`;
    return;
  }
  if (!kbState.rows.length) {
    host.innerHTML = `<p style="color:var(--muted);font-size:13px;">No entries yet. Click <strong>+ New entry</strong> to add one.</p>`;
    return;
  }
  host.innerHTML = kbState.rows.map((row, idx) => `
    <div class="row" style="margin-bottom: 8px; align-items: stretch;">
      <input type="text" data-kb-idx="${idx}" data-kb-field="key" placeholder="key" value="${escapeAttr(row.key)}" style="flex: 0 0 30%; font-family: var(--font-mono);" />
      <input type="text" data-kb-idx="${idx}" data-kb-field="value" placeholder="value (string or empty for null)" value="${escapeAttr(row.value ?? "")}" />
      <button class="btn danger" data-kb-remove="${idx}" style="flex: 0 0 auto;">remove</button>
    </div>
  `).join("");
  host.querySelectorAll("input[data-kb-idx]").forEach((el) => {
    el.addEventListener("input", (ev) => {
      const idx = Number(ev.target.dataset.kbIdx);
      const field = ev.target.dataset.kbField;
      kbState.rows[idx][field] = ev.target.value;
    });
  });
  host.querySelectorAll("button[data-kb-remove]").forEach((el) => {
    el.addEventListener("click", () => {
      kbState.rows.splice(Number(el.dataset.kbRemove), 1);
      renderKBRows();
    });
  });
}

function kbAdd() {
  if (!kbState.detected) return;
  kbState.rows.push({ key: "", value: "" });
  renderKBRows();
}

function kbReset() {
  kbState.rows = Object.entries(kbState.lastLoaded || {}).map(([k, v]) => ({ key: k, value: v ?? "" }));
  document.getElementById("kb-msg").innerHTML = "";
  renderKBRows();
}

async function kbSave() {
  const msg = document.getElementById("kb-msg");
  msg.innerHTML = "";
  const kb = {};
  const seen = new Set();
  for (const row of kbState.rows) {
    const key = row.key.trim();
    if (!key) continue;
    if (seen.has(key)) {
      msg.innerHTML = `<div class="error-box">duplicate key ${escapeHtml(key)}</div>`;
      return;
    }
    seen.add(key);
    kb[key] = row.value === "" ? null : row.value;
  }
  try {
    const data = await api("PUT", `/api/dictation/project-kb${projectRootParam("?")}`, { kb });
    kbState.lastLoaded = data.kb;
    kbState.detected = data.detected;
    kbState.kbPath = data.kb_path;
    msg.innerHTML = `<div class="ok-box">Saved.</div>`;
    renderKBMeta(data);
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

async function createStarterKB(options = {}) {
  const msg = document.getElementById("kb-msg");
  msg.innerHTML = "";
  try {
    const data = await api("POST", `/api/dictation/project-kb/starter${projectRootParam("?")}`);
    if (options.switchToKB) activateSection("kb");
    kbState.lastLoaded = data.kb;
    kbState.detected = data.detected;
    kbState.kbPath = data.kb_path;
    kbState.rows = Object.entries(data.kb || {}).map(([k, v]) => ({ key: k, value: v ?? "" }));
    msg.innerHTML = `<div class="ok-box">Created starter Project KB.</div>`;
    renderKBMeta(data);
    renderKBRows();
    if (state.activeSection === "readiness") loadReadiness();
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

async function kbDelete() {
  if (!kbState.detected) return;
  const ok = await window.holdspeakConfirm({
    title: `Delete ${kbState.kbPath}?`,
    body: "The project knowledge base file is removed from disk. The enclosing .holdspeak/ directory is preserved so other project state (blocks, runtime config) stays intact.",
    scopeNote: "Only the local knowledge-base file is affected. Source files referenced from inside the KB are not touched.",
    confirmLabel: "Delete file",
  });
  if (!ok) return;
  const msg = document.getElementById("kb-msg");
  msg.innerHTML = "";
  try {
    await api("DELETE", `/api/dictation/project-kb${projectRootParam("?")}`);
    await loadKB();
    msg.innerHTML = `<div class="ok-box">Deleted.</div>`;
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

// ── Project .hs context editor ───────────────────────────────────────
async function loadHSContext() {
  const banner = document.getElementById("hs-meta-banner");
  banner.classList.remove("warn", "error");
  banner.textContent = "Loading…";
  try {
    const data = await api("GET", `/api/dictation/project-hs${projectRootParam("?")}`);
    hsState.detected = data.detected;
    hsState.contextDir = data.context_dir;
    hsState.contextDirExists = !!data.context_dir_exists;
    hsState.files = data.files || {};
    hsState.flatFiles = data.flat_files || {};
    hsState.skipped = data.skipped || [];
    hsState.warnings = data.warnings || [];
    hsState.writePolicy = data.write_policy || {};
    if (!hsState.files[hsState.selected]) hsState.selected = "instructions.md";
    renderHSMeta(data);
    renderHSFileList();
    renderHSEditor();
    await loadProjectDocSuggestion();
  } catch (e) {
    banner.classList.add(e.status === 404 ? "warn" : "error");
    banner.textContent = e.message;
    document.getElementById("hs-file-list").innerHTML = "";
    document.getElementById("hs-editor").value = "";
    hsState.suggestion = null;
    renderProjectDocSuggestion();
  }
}

function renderHSMeta(data) {
  const banner = document.getElementById("hs-meta-banner");
  const d = data.detected;
  if (!d) {
    banner.classList.add("warn");
    banner.textContent = "No project detected.";
    return;
  }
  const parts = [
    `project: <strong>${escapeHtml(d.name)}</strong> (${escapeHtml(d.anchor)})`,
    `root: ${escapeHtml(d.root)}`,
    `path: ${escapeHtml(data.context_dir)}`,
  ];
  const flatCount = Object.keys(data.flat_files || {}).length;
  if (flatCount) parts.push(`flat compatibility files: <strong>${flatCount}</strong>`);
  if (!data.context_dir_exists) {
    parts.push(`<em style="color:var(--warn);">.hs/ does not exist yet — first save creates the editable directory</em>`);
  }
  const policy = data.write_policy || {};
  const warnings = (data.warnings || []).length
    ? `<div class="error-box">${(data.warnings || []).map(escapeHtml).join("<br>")}</div>`
    : "";
  const telemetry = data.telemetry || {};
  const telemetryHtml = renderDryTelemetry(telemetry);
  const policyText = policy.flat
    ? `<div class="rt-counter-note">${escapeHtml(policy.canonical || "")} ${escapeHtml(policy.flat || "")}</div>`
    : "";
  banner.innerHTML = `${parts.join("  ·  ")}${policyText}${warnings}`;
}

function renderHSFileList() {
  const host = document.getElementById("hs-file-list");
  host.innerHTML = HS_FILE_META.map(([name, help]) => {
    const file = hsState.files[name] || {};
    const source = file.source === "flat"
      ? '<span class="pill">flat read-only</span>'
      : file.exists
        ? '<span class="pill">saved</span>'
        : '<span class="pill">new</span>';
    const truncation = file.truncated ? '<span class="pill">truncated</span>' : "";
    return `
      <div class="block-card${name === hsState.selected ? " selected" : ""}" data-hs-file="${escapeAttr(name)}">
        <div><span class="block-id">.hs/${escapeHtml(name)}</span>${source}${truncation}</div>
        <div class="block-desc">${escapeHtml(help)}</div>
      </div>
    `;
  }).join("");
  host.querySelectorAll("[data-hs-file]").forEach((el) => {
    el.addEventListener("click", () => {
      hsState.selected = el.dataset.hsFile;
      renderHSFileList();
      renderHSEditor();
    });
  });
}

function renderHSEditor() {
  const selected = hsState.selected || "instructions.md";
  const meta = HS_FILE_META.find(([name]) => name === selected) || [selected, ""];
  const file = hsState.files[selected] || { content: "" };
  const save = document.getElementById("hs-btn-save");
  const sourceNote = file.source === "flat"
    ? ` Loaded from read-only ${file.actual_path || file.path || "flat .hs_* file"}. Saving creates editable .hs/${selected}; it does not modify the flat file.`
    : file.exists
      ? ` Editing ${file.path || `.hs/${selected}`}.`
      : " New canonical file; first save creates it.";
  const truncationNote = file.truncated
    ? " This file was truncated for safety, so saving is disabled to avoid losing content."
    : "";
  document.getElementById("hs-editor-title").textContent = `.hs/${selected}`;
  document.getElementById("hs-editor-help").textContent = `${meta[1] || ""}${sourceNote}${truncationNote}`;
  document.getElementById("hs-editor").value = file.content || "";
  if (save) {
    save.disabled = !!file.truncated;
    save.textContent = file.source === "flat" ? "Create editable .hs copy" : "Save";
  }
  document.getElementById("hs-msg").innerHTML = "";
}

async function saveHSContext() {
  const msg = document.getElementById("hs-msg");
  msg.innerHTML = "";
  const selected = hsState.selected || "instructions.md";
  const content = document.getElementById("hs-editor").value;
  try {
    const data = await api("PUT", `/api/dictation/project-hs${projectRootParam("?")}`, {
      files: { [selected]: content },
    });
    hsState.detected = data.detected;
    hsState.contextDir = data.context_dir;
    hsState.contextDirExists = !!data.context_dir_exists;
    hsState.files = data.files || {};
    hsState.flatFiles = data.flat_files || {};
    hsState.skipped = data.skipped || [];
    hsState.warnings = data.warnings || [];
    hsState.writePolicy = data.write_policy || {};
    msg.innerHTML = `<div class="ok-box">Saved .hs/${escapeHtml(selected)}. Flat compatibility files were not modified.</div>`;
    renderHSMeta(data);
    renderHSFileList();
    renderHSEditor();
    if (state.activeSection === "readiness") loadReadiness();
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

function resetHSContext() {
  renderHSEditor();
}

async function loadProjectDocSuggestion() {
  try {
    const data = await api("GET", `/api/dictation/project-doc-suggestion${projectRootParam("?")}`);
    hsState.suggestion = data.suggestion || null;
  } catch (_e) {
    hsState.suggestion = null;
  }
  renderProjectDocSuggestion();
}

function renderProjectDocSuggestion() {
  const panel = document.getElementById("hs-suggestion-panel");
  if (!panel) return;
  const suggestion = hsState.suggestion;
  panel.hidden = !suggestion;
  const msg = document.getElementById("hs-suggestion-msg");
  if (msg) msg.innerHTML = "";
  if (!suggestion) return;
  document.getElementById("hs-suggestion-path").value = suggestion.target_path || "";
  document.getElementById("hs-suggestion-rationale").textContent =
    suggestion.rationale ? `Rationale: ${suggestion.rationale}` : "Rationale unavailable.";
  document.getElementById("hs-suggestion-content").value = suggestion.content || "";
}

function extractProjectDocSuggestion(data) {
  const stages = data && Array.isArray(data.stages) ? data.stages : [];
  for (const stage of stages) {
    const suggestion = stage && stage.metadata && stage.metadata.project_doc_suggestion;
    if (suggestion && typeof suggestion === "object") return suggestion;
  }
  return null;
}

async function applyProjectDocSuggestion() {
  const msg = document.getElementById("hs-suggestion-msg");
  msg.innerHTML = "";
  const suggestion = {
    target_path: document.getElementById("hs-suggestion-path").value.trim(),
    rationale: (hsState.suggestion && hsState.suggestion.rationale) || "Accepted from HoldSpeak suggestion review.",
    content: document.getElementById("hs-suggestion-content").value,
  };
  try {
    const data = await api("POST", `/api/dictation/project-doc-suggestion/apply${projectRootParam("?")}`, {
      suggestion,
    });
    hsState.suggestion = null;
    renderProjectDocSuggestion();
    await loadHSContext();
    document.getElementById("hs-msg").innerHTML =
      `<div class="ok-box">Applied ${escapeHtml(data.suggestion.target_path)}.</div>`;
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

async function dismissProjectDocSuggestion() {
  const msg = document.getElementById("hs-suggestion-msg");
  msg.innerHTML = "";
  try {
    await api("POST", `/api/dictation/project-doc-suggestion/dismiss${projectRootParam("?")}`);
    hsState.suggestion = null;
    renderProjectDocSuggestion();
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

// ── Runtime config editor ───────────────────────────────────────────
const rtState = { last: null };

async function loadRuntime() {
  const banner = document.getElementById("rt-meta-banner");
  banner.classList.remove("warn", "error");
  banner.textContent = "Loading…";
  try {
    const data = await api("GET", "/api/settings");
    let readiness = null;
    try {
      readiness = await api("GET", `/api/dictation/readiness${projectRootParam("?")}`);
    } catch (_) {
      readiness = null;
    }
    rtState.last = data;
    renderRuntime(data, readiness);
  } catch (e) {
    banner.classList.add("error");
    banner.textContent = e.message;
  }
}

function renderRuntime(data, readiness = null) {
  const dictation = data.dictation || {};
  const pipeline = dictation.pipeline || {};
  const runtime = dictation.runtime || {};
  const status = data._runtime_status || { counters: {}, session: {} };

  const passes = Number(pipeline.rewrite_passes ?? 1);
  document.getElementById("rt-meta-banner").innerHTML =
    `pipeline: <strong>${pipeline.enabled ? "enabled" : "disabled"}</strong>  ·  ` +
    `target: <strong>${escapeHtml(pipeline.target_profile_override || "auto")}</strong>  ·  ` +
    `backend: <strong>${escapeHtml(runtime.backend || "auto")}</strong>  ·  ` +
    `cold-start cap: <strong>${(pipeline.max_total_latency_ms || 0) * 5} ms</strong>  ·  ` +
    `depth: <strong>${passes}× pass${passes === 1 ? "" : "es"}</strong>` +
    `${pipeline.corrections_enabled ? " · <strong>learns</strong>" : ""}` +
    `${pipeline.target_detect_llm_enabled ? " · <strong>infers target</strong>" : ""}`;

  document.getElementById("rt-enabled").checked = !!pipeline.enabled;
  document.getElementById("rt-stage-rewriter").checked =
    Array.isArray(pipeline.stages) && pipeline.stages.includes("project-rewriter");
  document.getElementById("rt-target-profile").value = pipeline.target_profile_override || "auto";
  document.getElementById("rt-backend").value = runtime.backend || "auto";
  document.getElementById("rt-mlx-model").value = runtime.mlx_model || "";
  document.getElementById("rt-llama-path").value = runtime.llama_cpp_model_path || "";
  document.getElementById("rt-openai-model").value = runtime.openai_compatible_model || "";
  document.getElementById("rt-openai-base-url").value = runtime.openai_compatible_base_url || "";
  document.getElementById("rt-openai-api-key-env").value = runtime.openai_compatible_api_key_env || "";
  document.getElementById("rt-openai-timeout").value = runtime.openai_compatible_timeout_seconds || 8;
  document.getElementById("rt-warm").checked = !!runtime.warm_on_start;
  const slider = document.getElementById("rt-latency");
  slider.value = pipeline.max_total_latency_ms || 600;
  slider.oninput = updateLatencyVis;
  updateLatencyVis();

  // ── Copilot depth (HS-40-03) ──
  setRewritePasses(passes);
  document.getElementById("rt-corrections-enabled").checked = !!pipeline.corrections_enabled;
  document.getElementById("rt-target-detect-llm-enabled").checked = !!pipeline.target_detect_llm_enabled;
  const below = document.getElementById("rt-target-detect-llm-below");
  below.value = pipeline.target_detect_llm_below ?? 0.8;
  below.oninput = updateTargetBelowVis;
  updateTargetBelowVis();
  updateTargetDetectReveal();

  // Counters
  const counters = status.counters || {};
  document.getElementById("rt-counters").innerHTML = `
    <div>model_loads:        <strong>${counters.model_loads ?? 0}</strong></div>
    <div>classify_calls:     <strong>${counters.classify_calls ?? 0}</strong></div>
    <div>classify_failures:  <strong>${counters.classify_failures ?? 0}</strong></div>
    <div>constrained_retries: <strong>${counters.constrained_retries ?? 0}</strong></div>
  `;

  // Session-disabled banner
  const sessionBanner = document.getElementById("rt-session-banner");
  const session = status.session || {};
  if (session.llm_disabled_for_session) {
    sessionBanner.innerHTML = `<div class="error-box">LLM disabled for this session: ${escapeHtml(session.disabled_reason || "(no reason)")}</div>`;
  } else {
    sessionBanner.innerHTML = `<div class="ok-box">LLM stage active for this session.</div>`;
  }

  const guidance = readiness?.runtime?.guidance ||
    (readiness?.warnings || []).find((w) => w.guidance)?.guidance;
  const guidanceHost = document.getElementById("rt-guidance");
  guidanceHost.innerHTML = renderRuntimeGuidance(guidance);
  wireCopyCommandButtons(guidanceHost);
}

function updateLatencyVis() {
  const v = Number(document.getElementById("rt-latency").value);
  document.getElementById("rt-latency-vis").textContent =
    `${v} ms  ·  cold-start cap: ${v * 5} ms (DIR-R-003)`;
}

// ── Copilot depth controls (HS-40-03) ──
const REWRITE_PASS_DESC = {
  1: "Single pass — fastest; byte-identical to a plain rewrite.",
  2: "Two passes — one critique-and-refine after the draft.",
  3: "Three passes — balanced refinement (recommended for project work).",
  4: "Four passes — deeper polish; watch the latency budget.",
  5: "Five passes — maximum refinement; most latency-budget gating.",
};

function setRewritePasses(n) {
  const passes = Math.min(5, Math.max(1, Math.round(Number(n) || 1)));
  document.getElementById("rt-rewrite-passes").value = String(passes);
  document.getElementById("rt-rewrite-badge").textContent = `${passes}×`;
  document.getElementById("rt-rewrite-desc").textContent =
    REWRITE_PASS_DESC[passes] || "";
  document.querySelectorAll("#rt-rewrite-seg .seg-btn").forEach((btn) =>
    btn.setAttribute(
      "aria-pressed",
      btn.dataset.value === String(passes) ? "true" : "false"
    )
  );
}

function updateTargetBelowVis() {
  const v = Number(document.getElementById("rt-target-detect-llm-below").value);
  document.getElementById("rt-target-below-val").textContent = v.toFixed(2);
}

function updateTargetDetectReveal() {
  const on = document.getElementById("rt-target-detect-llm-enabled").checked;
  document.getElementById("rt-target-below-wrap").hidden = !on;
}

async function saveRuntime(options = {}) {
  const msg = document.getElementById("rt-msg");
  msg.innerHTML = "";

  // Inline validation mirroring the API bounds (HS-40-01) so out-of-range is
  // caught before submit. The segmented control + 0–1 slider already constrain
  // input, but guard anyway for keyboard/programmatic edits.
  const rewritePasses = Number(document.getElementById("rt-rewrite-passes").value);
  const targetBelow = Number(document.getElementById("rt-target-detect-llm-below").value);
  if (!Number.isInteger(rewritePasses) || rewritePasses < 1 || rewritePasses > 5) {
    msg.innerHTML = `<div class="error-box">Rewrite passes must be a whole number between 1 and 5.</div>`;
    return;
  }
  if (!(targetBelow >= 0 && targetBelow <= 1)) {
    msg.innerHTML = `<div class="error-box">Infer-target threshold must be between 0.00 and 1.00.</div>`;
    return;
  }

  const payload = {
    dictation: {
      pipeline: {
        enabled: document.getElementById("rt-enabled").checked,
        stages: [
          "intent-router",
          ...(document.getElementById("rt-stage-rewriter").checked ? ["project-rewriter"] : []),
          "kb-enricher",
        ],
        max_total_latency_ms: Number(document.getElementById("rt-latency").value),
        target_profile_override: document.getElementById("rt-target-profile").value,
        rewrite_passes: rewritePasses,
        corrections_enabled: document.getElementById("rt-corrections-enabled").checked,
        target_detect_llm_enabled: document.getElementById("rt-target-detect-llm-enabled").checked,
        target_detect_llm_below: targetBelow,
      },
      runtime: {
        backend: document.getElementById("rt-backend").value,
        mlx_model: document.getElementById("rt-mlx-model").value.trim(),
        llama_cpp_model_path: document.getElementById("rt-llama-path").value.trim(),
        openai_compatible_model: document.getElementById("rt-openai-model").value.trim(),
        openai_compatible_base_url: document.getElementById("rt-openai-base-url").value.trim(),
        openai_compatible_api_key_env: document.getElementById("rt-openai-api-key-env").value.trim(),
        openai_compatible_timeout_seconds: Number(document.getElementById("rt-openai-timeout").value),
        warm_on_start: document.getElementById("rt-warm").checked,
      },
    },
  };
  try {
    await api("PUT", "/api/settings", payload);
    msg.innerHTML = `<div class="ok-box">${escapeHtml(options.message || "Saved. New utterances pick up the config on next pipeline rebuild.")}</div>`;
    await loadRuntime();
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

async function saveRuntimeAndTest() {
  // Save the cockpit config, then jump to the dry-run so the user can try the
  // exact config they just set (HS-40-03 "test this config" affordance).
  await saveRuntime({ message: "Saved — opening dry-run so you can test this config." });
  const errored = document.querySelector("#rt-msg .error-box");
  if (!errored) activateSection("dry-run");
}

async function enablePipelineFromReadiness() {
  activateSection("runtime");
  await loadRuntime();
  document.getElementById("rt-enabled").checked = true;
  await saveRuntime({ message: "Enabled. New utterances pick up the config on next pipeline rebuild." });
}

// ── Memory + telemetry (HS-40-04) ───────────────────────────────────
async function loadMemory() {
  const banner = document.getElementById("mem-meta-banner");
  banner.classList.remove("warn", "error");
  banner.textContent = "Loading…";
  try {
    const corrections = await api("GET", "/api/dictation/corrections");
    renderMemoryCorrections(corrections);
    let readiness = null;
    try {
      readiness = await api("GET", `/api/dictation/readiness${projectRootParam("?")}`);
    } catch (_) {
      readiness = null;
    }
    renderMemoryDepth(readiness?.depth || null);
    const learned = corrections.size || 0;
    banner.innerHTML =
      `learning: <strong>${corrections.enabled ? "on" : "off"}</strong>  ·  ` +
      `remembered: <strong>${learned}</strong>  ·  ` +
      `depth runs this session: <strong>${(readiness?.depth?.runs) ?? 0}</strong>`;
  } catch (e) {
    banner.classList.add("error");
    banner.textContent = e.message;
  }
}

function renderMemoryCorrections(data) {
  const toggle = document.getElementById("mem-corrections-enabled");
  toggle.checked = !!data.enabled;
  document.getElementById("mem-enabled-hint").textContent = data.enabled
    ? "On — similar utterances are nudged toward what you corrected."
    : "Off — corrections are remembered but not used while routing.";

  const list = document.getElementById("mem-list");
  const items = Array.isArray(data.items) ? data.items : [];
  if (!items.length) {
    list.innerHTML =
      `<div class="mem-empty">Nothing learned yet. Correct a route from the live runtime, or add one above — it persists across restarts.</div>`;
    return;
  }
  list.innerHTML = items
    .map((it) => {
      const target = it.kind === "target";
      const when = it.created_at ? `<span class="mem-when">${escapeHtml(relativeTime(it.created_at))}</span>` : "";
      const del = it.id != null
        ? `<button class="mem-del" type="button" data-id="${escapeAttr(String(it.id))}" title="Forget this" aria-label="Forget this correction">×</button>`
        : "";
      return `<div class="mem-item ${target ? "kind-target" : "kind-intent"}">
        <div class="mem-item-body">
          <span class="mem-kind">${target ? "target → profile" : "intent → block"}</span>
          <span class="mem-gist" title="${escapeAttr(it.key || "")}">${escapeHtml(it.key || "")}</span>
        </div>
        <span class="mem-arrow">→</span>
        <span class="mem-value">${escapeHtml(it.value || "")}</span>
        ${when}
        ${del}
      </div>`;
    })
    .join("");
  list.querySelectorAll(".mem-del").forEach((btn) =>
    btn.addEventListener("click", () => deleteCorrection(btn.dataset.id))
  );
}

function renderMemoryDepth(depth) {
  const host = document.getElementById("mem-depth");
  if (!depth || !depth.runs) {
    host.innerHTML =
      `<div class="mem-empty">No pipeline runs recorded this session yet. Run a few dry-runs (or dictate) to see per-stage timings.</div>`;
    return;
  }
  const budget = Number(depth.budget_ms) || 0;
  const stages = depth.stages || {};
  const stageRows = Object.keys(stages)
    .map((sid) => {
      const q = stages[sid] || {};
      const p50 = Number(q.p50) || 0;
      const p95 = Number(q.p95) || 0;
      const pct = budget > 0 ? Math.min(100, Math.round((p95 / budget) * 100)) : 0;
      const warn = budget > 0 && p95 >= budget * 0.66;
      return `<div class="depth-stage">
        <div class="depth-stage-head">
          <span class="depth-stage-name">${escapeHtml(sid)}</span>
          <span class="depth-stage-nums">p50 ${p50.toFixed(0)}ms · p95 ${p95.toFixed(0)}ms${
            q.count != null ? ` · n=${q.count}` : ""
          }</span>
        </div>
        <div class="depth-track" title="p95 is ${pct}% of the ${budget || "—"}ms budget">
          <span class="depth-fill ${warn ? "warn" : ""}" style="width:${pct}%"></span>
        </div>
      </div>`;
    })
    .join("");

  const guidance = (depth.guidance || [])
    .map((g) => `<div class="depth-guidance">⚠ ${escapeHtml(g.message || "")}</div>`)
    .join("");

  const passes = Array.isArray(depth.rewrite_pass_ms) ? depth.rewrite_pass_ms : [];
  const passChips = passes.length
    ? `<div class="depth-passes">${passes
        .map((ms, i) => `<span class="depth-pass-chip">pass ${i + 1}: ${Number(ms).toFixed(0)}ms</span>`)
        .join("")}</div>`
    : "";

  const corr = depth.corrections || {};
  host.innerHTML = `
    <div class="depth-summary">
      <div class="depth-stat"><div class="depth-stat-num">${depth.runs}</div><div class="depth-stat-label">runs</div></div>
      <div class="depth-stat"><div class="depth-stat-num">${budget || "—"}</div><div class="depth-stat-label">budget ms</div></div>
      <div class="depth-stat"><div class="depth-stat-num">${corr.size ?? 0}</div><div class="depth-stat-label">corrections</div></div>
    </div>
    ${stageRows}
    ${passChips ? `<div><div class="depth-stat-label">last multi-pass rewrite</div>${passChips}</div>` : ""}
    ${guidance}
  `;
}

async function addCorrection(ev) {
  if (ev) ev.preventDefault();
  const msg = document.getElementById("mem-add-msg");
  msg.innerHTML = "";
  const kind = document.getElementById("mem-add-kind").value;
  const text = document.getElementById("mem-add-text").value.trim();
  const value = document.getElementById("mem-add-value").value.trim();
  if (!text || !value) {
    msg.innerHTML = `<div class="error-box">Both the gist and the corrected value are required.</div>`;
    return;
  }
  try {
    const res = await api("POST", "/api/dictation/corrections", { kind, text, value });
    if (!res.recorded) {
      msg.innerHTML = `<div class="error-box">Not stored — it looked secret-like or invalid (corrections are gist-only).</div>`;
      return;
    }
    document.getElementById("mem-add-text").value = "";
    document.getElementById("mem-add-value").value = "";
    await loadMemory();
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

async function deleteCorrection(id) {
  try {
    await api("DELETE", `/api/dictation/corrections/${encodeURIComponent(id)}`);
    await loadMemory();
  } catch (e) {
    document.getElementById("mem-meta-banner").textContent = e.message;
  }
}

async function clearAllCorrections() {
  if (!confirm("Forget everything the copilot has learned? This can't be undone.")) return;
  try {
    await api("DELETE", "/api/dictation/corrections");
    await loadMemory();
  } catch (e) {
    document.getElementById("mem-meta-banner").textContent = e.message;
  }
}

async function toggleCorrectionsEnabled() {
  const enabled = document.getElementById("mem-corrections-enabled").checked;
  try {
    await api("PUT", "/api/settings", {
      dictation: { pipeline: { corrections_enabled: enabled } },
    });
    await loadMemory();
  } catch (e) {
    document.getElementById("mem-meta-banner").textContent = e.message;
    await loadMemory();
  }
}

function relativeTime(iso) {
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

// ── Dry-run preview ────────────────────────────────────────────────
// ── Journal (HS-45-02) ───────────────────────────────────────────────
const journalState = { items: [], retention: 500, enabled: true };

async function loadJournal() {
  const meta = document.getElementById("journal-meta");
  meta.classList.remove("warn", "error");
  meta.textContent = "Loading…";
  try {
    const data = await api("GET", "/api/dictation/journal?limit=200");
    journalState.items = Array.isArray(data.items) ? data.items : [];
    journalState.retention = Number(data.retention) || 500;
    journalState.enabled = !!data.enabled;
    const trust = document.getElementById("journal-trust");
    if (trust) trust.classList.toggle("is-off", !data.enabled);
    meta.classList.toggle("warn", !data.enabled);
    meta.innerHTML = data.enabled
      ? `journaling: <strong>on</strong>  ·  stored: <strong>${data.count ?? 0}</strong>  ·  keeps the most recent <strong>${journalState.retention}</strong>`
      : `journaling: <strong>off</strong> — new dictations are not being recorded. Turn it on under <strong>Runtime → Copilot depth</strong>.`;
    renderJournal();
  } catch (e) {
    meta.classList.add("error");
    meta.textContent = e.message;
  }
}

function journalMatches(item) {
  const q = (document.getElementById("journal-search")?.value || "").trim().toLowerCase();
  const src = document.getElementById("journal-filter-source")?.value || "";
  const warnOnly = !!document.getElementById("journal-filter-warnings")?.checked;
  const corrOnly = !!document.getElementById("journal-filter-corrected")?.checked;
  if (src && item.source !== src) return false;
  if (warnOnly && !(item.warnings || []).length) return false;
  if (corrOnly && !item.corrected) return false;
  if (q) {
    const hay = `${item.transcript || ""}\n${item.final_text || ""}`.toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}

function renderJournal() {
  const list = document.getElementById("journal-list");
  if (!list) return;
  const items = journalState.items.filter(journalMatches);
  if (!journalState.items.length) {
    list.innerHTML = `<div class="journal-empty">
      <div class="journal-empty-glyph" aria-hidden="true">🎙️</div>
      <p class="journal-empty-head">Your dictations will appear here.</p>
      <p class="journal-empty-sub">Speak — or run a <strong>Dry-run</strong> — and each one is remembered: what you said, where it routed, and how long it took.</p>
    </div>`;
    return;
  }
  if (!items.length) {
    list.innerHTML = `<div class="journal-empty"><p class="journal-empty-sub">No entries match your search or filters.</p></div>`;
    return;
  }
  list.innerHTML = items.map(renderJournalEntry).join("");
  list.querySelectorAll("button[data-journal-del]").forEach((btn) =>
    btn.addEventListener("click", () => deleteJournalEntry(btn.dataset.journalDel))
  );
}

function renderLatencyStrip(item) {
  const stages = item.stage_ms || {};
  const ids = Object.keys(stages);
  const total = Number(item.total_ms) || ids.reduce((s, k) => s + (Number(stages[k]) || 0), 0);
  if (!ids.length || total <= 0) {
    return `<div class="lat-strip lat-strip--empty" title="no per-stage timing recorded">
      <span class="lat-total">${total ? `${total.toFixed(0)} ms` : "—"}</span>
    </div>`;
  }
  const segs = ids
    .map((sid) => {
      const ms = Number(stages[sid]) || 0;
      const pct = Math.max(2, Math.round((ms / total) * 100));
      const cls = sid.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
      return `<span class="lat-seg lat-${escapeAttr(cls)}" style="width:${pct}%" title="${escapeAttr(sid)} · ${ms.toFixed(0)} ms">
        <span class="lat-seg-label">${escapeHtml(sid)} ${ms.toFixed(0)}ms</span>
      </span>`;
    })
    .join("");
  return `<div class="lat-strip" role="img" aria-label="per-stage latency, total ${total.toFixed(0)} milliseconds">
    <div class="lat-bar">${segs}</div>
    <span class="lat-total">${total.toFixed(0)} ms total</span>
  </div>`;
}

function renderJournalEntry(item) {
  const spoken = item.source === "dictation";
  const sourceChip = `<span class="jr-source ${spoken ? "src-spoken" : "src-dry"}">${spoken ? "Spoken" : "Dry-run"}</span>`;
  const when = item.created_at ? `<span class="jr-when" title="${escapeAttr(item.created_at)}">${escapeHtml(relativeTime(item.created_at))}</span>` : "";
  const corrected = item.corrected
    ? `<span class="jr-corrected" title="You corrected this — the copilot learned from it">✓ corrected</span>`
    : "";
  const block = item.block_id
    ? `<span class="jr-badge jr-block" title="routed block">${escapeHtml(item.block_id)}${item.confidence != null ? ` · ${Number(item.confidence).toFixed(2)}` : ""}</span>`
    : `<span class="jr-badge jr-block jr-muted">no route</span>`;
  const target = item.target_profile
    ? `<span class="jr-badge jr-target" title="target profile">→ ${escapeHtml(item.target_profile)}</span>`
    : "";
  const warnings = (item.warnings || []).length
    ? `<details class="jr-warnings"><summary>${(item.warnings || []).length} warning${(item.warnings || []).length === 1 ? "" : "s"}</summary>
        <ul>${(item.warnings || []).map((w) => `<li>${escapeHtml(w)}</li>`).join("")}</ul></details>`
    : "";
  const transcript = item.transcript || "";
  const finalText = item.final_text || "";
  return `<article class="journal-card ${item.corrected ? "is-corrected" : ""}">
    <header class="jr-head">
      ${sourceChip}
      ${block}
      ${target}
      ${corrected}
      <span class="jr-spacer"></span>
      ${when}
      <button class="jr-del" type="button" data-journal-del="${escapeAttr(String(item.id))}" title="Delete this entry" aria-label="Delete this journal entry">×</button>
    </header>
    <div class="jr-flow">
      <figure class="jr-text jr-said">
        <figcaption>You said</figcaption>
        <div class="jr-text-frame">
          <p>${escapeHtml(transcript) || "<em>(empty)</em>"}</p>
          <button type="button" class="cmd-copy jr-copy" data-cmd-copy data-command="${escapeAttr(transcript)}" aria-label="Copy transcript"><span data-cmd-copy-label>Copy</span></button>
        </div>
      </figure>
      <div class="jr-arrow" aria-hidden="true">→</div>
      <figure class="jr-text jr-typed">
        <figcaption>It typed</figcaption>
        <div class="jr-text-frame">
          <p>${escapeHtml(finalText) || "<em>(empty)</em>"}</p>
          <button type="button" class="cmd-copy jr-copy" data-cmd-copy data-command="${escapeAttr(finalText)}" aria-label="Copy typed text"><span data-cmd-copy-label>Copy</span></button>
        </div>
      </figure>
    </div>
    ${renderLatencyStrip(item)}
    ${warnings}
  </article>`;
}

async function deleteJournalEntry(id) {
  try {
    await api("DELETE", `/api/dictation/journal/${encodeURIComponent(id)}`);
    journalState.items = journalState.items.filter((it) => String(it.id) !== String(id));
    renderJournal();
    loadJournal();
  } catch (e) {
    const meta = document.getElementById("journal-meta");
    meta.classList.add("error");
    meta.textContent = e.message;
  }
}

async function clearJournal() {
  if (!journalState.items.length) return;
  if (!window.confirm("Clear the entire dictation journal? This can't be undone.")) return;
  try {
    await api("DELETE", "/api/dictation/journal");
    journalState.items = [];
    loadJournal();
  } catch (e) {
    const meta = document.getElementById("journal-meta");
    meta.classList.add("error");
    meta.textContent = e.message;
  }
}

async function runDryRun() {
  const msg = document.getElementById("dry-msg");
  const meta = document.getElementById("dry-meta");
  const finalHost = document.getElementById("dry-final");
  const trace = document.getElementById("dry-trace");
  msg.innerHTML = "";
  meta.classList.remove("warn", "error");
  meta.textContent = "Running…";
  finalHost.innerHTML = "";
  trace.innerHTML = "";
  const utterance = document.getElementById("dry-utterance").value;
  try {
    const payload = { utterance };
    if (state.projectRootOverride.trim()) payload.project_root = state.projectRootOverride.trim();
    const data = await api("POST", "/api/dictation/dry-run", payload);
    renderDryRun(data);
  } catch (e) {
    meta.classList.add("error");
    meta.textContent = e.message;
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

function renderDryRun(data) {
  const meta = document.getElementById("dry-meta");
  const finalHost = document.getElementById("dry-final");
  const trace = document.getElementById("dry-trace");
  const suggestion = extractProjectDocSuggestion(data);
  if (suggestion) {
    hsState.suggestion = suggestion;
    renderProjectDocSuggestion();
  } else if (data && data.project) {
    hsState.suggestion = null;
    renderProjectDocSuggestion();
  }
  meta.classList.remove("warn", "error");
  if (data.runtime_status !== "loaded") meta.classList.add(data.runtime_status === "disabled" ? "warn" : "error");
  const project = data.project
    ? `${escapeHtml(data.project.name)} (${escapeHtml(data.project.anchor)} @ ${escapeHtml(data.project.root)})`
    : "(none detected)";
  const source = data.created_block_id
    ? `  ·  created: <strong>${escapeHtml(data.created_block_id)}</strong>` +
      ` from <strong>${escapeHtml(data.template_title || data.template_id || "template")}</strong>`
    : "";
  const sample = data.sample_utterance
    ? `  ·  input: <strong>${escapeHtml(data.sample_utterance)}</strong>`
    : "";
  meta.innerHTML =
    `runtime: <strong>${escapeHtml(data.runtime_status)}</strong> (${escapeHtml(data.runtime_detail || "")})` +
    `  ·  project: <strong>${project}</strong>` +
    `  ·  blocks: <strong>${data.blocks_count ?? 0}</strong>` +
    `  ·  total: <strong>${Number(data.total_elapsed_ms || 0).toFixed(2)} ms</strong>` +
    source +
    sample;

  const warnings = (data.warnings || []).length
    ? `<div class="error-box">${(data.warnings || []).map(escapeHtml).join("<br>")}</div>`
    : "";
  // HS-10-10 / HS-10-09: final text rendered through CommandPreview
  // markup so it inherits the standardized monospaced/copy treatment.
  // The component-level click delegator (data-cmd-copy) handles the
  // copy button; no per-render wiring required.
  const finalText = data.final_text || "";
  const finalAttr = escapeAttr(finalText);
  // HS-45-03: `telemetryHtml` was referenced here but only ever defined inside
  // `renderHSMeta` — a pre-existing ReferenceError that left every browser
  // dry-run result blank (caught by runDryRun's try/catch; never surfaced
  // because the dry-run was only API-tested, never browser-tested). Define it
  // in scope from this run's telemetry.
  const telemetryHtml = renderDryTelemetry(data.telemetry || {});
  finalHost.innerHTML = `
    <figure class="cmd cmd--neutral" aria-label="Dry-run final text">
      <figcaption class="cmd-caption">Final text</figcaption>
      <div class="cmd-frame">
        <pre class="cmd-pre" id="dry-final-text"><code class="cmd-code">${escapeHtml(finalText)}</code></pre>
        <button type="button" class="cmd-copy" data-cmd-copy data-command="${finalAttr}" aria-label="Copy final text to clipboard">
          <span class="cmd-copy-label" data-cmd-copy-label>Copy</span>
        </button>
      </div>
    </figure>
    ${telemetryHtml}
    ${warnings}
  `;

  renderMomentOfTruth(data);

  const stages = data.stages || [];
  if (!stages.length) {
    trace.innerHTML = `<p class="trace-empty">No stages executed.</p>`;
    return;
  }
  trace.innerHTML = stages.map((stage) => renderDryStage(stage)).join("");
}

// ── HS-45-03: the moment of truth — fix it in flow, and it teaches ──────
function momentRoute(data) {
  // The block the run routed to (newest intent across stages), for the prompt.
  let block = null;
  let conf = null;
  for (const s of data.stages || []) {
    if (s.intent && s.intent.block_id) {
      block = s.intent.block_id;
      conf = s.intent.confidence;
    }
  }
  const target = data.target && data.target.id ? data.target.id : null;
  return { block, conf, target };
}

function renderMomentOfTruth(data) {
  const host = document.getElementById("dry-moment");
  if (!host) return;
  // Only when this run was journaled (durable repo + journaling on) — there's
  // an entry to attach a correction to. Works offline (no mic / no runtime):
  // the dry-run still journals, so the fix-and-teach is provable without a mic.
  const journalId = data.journal_id;
  if (journalId == null) {
    host.hidden = true;
    host.innerHTML = "";
    return;
  }
  const { block, conf, target } = momentRoute(data);
  const routed = block
    ? `routed to <strong>${escapeHtml(block)}</strong>${conf != null ? ` <span class="moment-conf">@ ${Number(conf).toFixed(2)}</span>` : ""}${target ? ` · target <strong>${escapeHtml(target)}</strong>` : ""}`
    : target
      ? `target <strong>${escapeHtml(target)}</strong>`
      : "no route matched";
  host.hidden = false;
  host.dataset.journalId = String(journalId);
  host.innerHTML = `
    <div class="moment-head">
      <span class="moment-q">Was that right?</span>
      <span class="moment-routed">${routed}</span>
      <span class="moment-spacer"></span>
      <button type="button" class="btn moment-fix-btn" id="moment-fix-open">Fix it →</button>
    </div>
    <form class="moment-form" id="moment-form" hidden>
      <p class="moment-hint">Teach the copilot what this <em>should</em> have been — it'll nudge similar dictations next time, and this entry is marked corrected in your Journal.</p>
      <div class="row">
        <label>Correct the
          <select id="moment-kind">
            <option value="intent">route (block)</option>
            <option value="target">target (profile)</option>
          </select>
        </label>
        <label>to
          <input type="text" id="moment-value" placeholder="${escapeAttr(block || target || "block id / target profile")}" />
        </label>
      </div>
      <div class="actions">
        <button type="submit" class="btn primary" id="moment-submit">Teach &amp; record</button>
        <button type="button" class="btn" id="moment-cancel">Cancel</button>
      </div>
      <div id="moment-msg"></div>
    </form>`;
  // Focus-safe: the form is revealed on click; we never auto-focus an input
  // (the dictation flow / the dry-run textarea keeps focus until the user acts).
  document.getElementById("moment-fix-open").addEventListener("click", () => {
    document.getElementById("moment-form").hidden = false;
    document.getElementById("moment-fix-open").hidden = true;
  });
  document.getElementById("moment-cancel").addEventListener("click", () => {
    document.getElementById("moment-form").hidden = true;
    document.getElementById("moment-fix-open").hidden = false;
  });
  document.getElementById("moment-form").addEventListener("submit", submitMomentFix);
}

async function submitMomentFix(ev) {
  ev.preventDefault();
  const host = document.getElementById("dry-moment");
  const id = host.dataset.journalId;
  const kind = document.getElementById("moment-kind").value;
  const value = document.getElementById("moment-value").value.trim();
  const msg = document.getElementById("moment-msg");
  msg.innerHTML = "";
  if (!value) {
    msg.innerHTML = `<div class="error-box">Enter the correct ${kind === "target" ? "target profile" : "block id"}.</div>`;
    return;
  }
  try {
    const res = await api("POST", `/api/dictation/journal/${encodeURIComponent(id)}/correct`, { kind, value });
    const taught = res && res.taught;
    host.innerHTML = `<div class="moment-done" role="status">
      <span class="moment-check" aria-hidden="true">✓</span>
      <span>${taught
        ? "Taught — the copilot will nudge similar dictations toward this, and the Journal entry is marked corrected."
        : "Recorded against the Journal entry. (Nothing was taught — the text looked like a secret, so it wasn't stored.)"}</span>
    </div>`;
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

function escapeAttr(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function renderDryTelemetry(telemetry) {
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

function renderDryStage(stage) {
  const intent = stage.intent
    ? `matched=${stage.intent.matched} block=${escapeHtml(stage.intent.block_id || "—")} confidence=${Number(stage.intent.confidence || 0).toFixed(2)}`
    : "intent=—";
  const warnings = (stage.warnings || []).length
    ? `<div class="error-box">${stage.warnings.map(escapeHtml).join("<br>")}</div>`
    : "";
  const metadata = stage.metadata && Object.keys(stage.metadata).length
    ? `<pre class="trace-metadata">${escapeHtml(JSON.stringify(stage.metadata, null, 2))}</pre>`
    : "";
  const telemetry = stage.telemetry || {};
  const telemetryLine = telemetry.reason
    ? `<p class="trace-intent">status=${escapeHtml(telemetry.status || "unknown")} reason=${escapeHtml(telemetry.reason)}${telemetry.fallback ? ` fallback=${escapeHtml(telemetry.fallback_category || "yes")}` : ""}</p>`
    : "";
  // Stage text rendered through CommandPreview. Stages with warnings
  // surface in danger tone so failure points are scannable down the
  // trace at a glance.
  const stageText = stage.text || "";
  const stageAttr = escapeAttr(stageText);
  const tone = (stage.warnings || []).length ? "danger" : "neutral";
  return `
    <article class="trace-stage">
      <header class="trace-stage-head">
        <strong>${escapeHtml(stage.stage_id)}</strong>
        <span class="trace-stage-elapsed">${Number(stage.elapsed_ms || 0).toFixed(2)} ms</span>
      </header>
      <p class="trace-intent">${intent}</p>
      ${telemetryLine}
      ${warnings}
      ${metadata}
      <figure class="cmd cmd--${tone}" aria-label="Stage ${escapeAttr(stage.stage_id)} output">
        <div class="cmd-frame">
          <pre class="cmd-pre"><code class="cmd-code">${escapeHtml(stageText)}</code></pre>
          <button type="button" class="cmd-copy" data-cmd-copy data-command="${stageAttr}" aria-label="Copy stage output to clipboard">
            <span class="cmd-copy-label" data-cmd-copy-label>Copy</span>
          </button>
        </div>
      </figure>
    </article>
  `;
}

function clearDryRun() {
  document.getElementById("dry-utterance").value = "";
  document.getElementById("dry-msg").innerHTML = "";
  document.getElementById("dry-meta").textContent = "No dry-run yet.";
  document.getElementById("dry-meta").classList.remove("warn", "error");
  document.getElementById("dry-final").innerHTML = "";
  const moment = document.getElementById("dry-moment");
  if (moment) { moment.hidden = true; moment.innerHTML = ""; }
  document.getElementById("dry-trace").innerHTML = "";
}

async function loadAgentContext() {
  const banner = document.getElementById("agent-context-banner");
  if (!banner) return;
  try {
    const data = await api("GET", `/api/dictation/agent-context${projectRootParam("?")}`);
    renderAgentContext(data);
  } catch (_e) {
    state.agentSession = null;
    banner.hidden = true;
  }
}

function renderAgentContext(data) {
  const banner = document.getElementById("agent-context-banner");
  const title = document.getElementById("agent-context-title");
  const text = document.getElementById("agent-context-text");
  if (!banner || !title || !text) return;

  const session = data && data.session;
  if (!session || !session.awaiting_response || !session.last_assistant_text) {
    state.agentSession = null;
    banner.hidden = true;
    return;
  }

  state.agentSession = session;
  const label = [session.agent, session.project_name || basename(session.repo_root), session.cwd]
    .filter(Boolean)
    .join(" · ");
  const assistantText = String(session.last_assistant_text || "");
  const preview = assistantText.length > 320 ? `${assistantText.slice(0, 320)}…` : assistantText;
  const summary = session.summary && session.summary.summary ? String(session.summary.summary) : "";
  const summaryPreview = summary
    ? `<br><strong>Summary:</strong> ${escapeHtml(summary.length > 240 ? `${summary.slice(0, 240)}…` : summary)}`
    : "";
  title.textContent = `${session.agent || "Agent"} is waiting for your reply`;
  text.innerHTML = `${escapeHtml(label)}<br>${escapeHtml(preview)}${summaryPreview}`;
  banner.hidden = false;
}

async function clearAgentContext() {
  if (!state.agentSession) return;
  const button = document.getElementById("agent-context-clear");
  if (button) button.disabled = true;
  try {
    await api("POST", "/api/dictation/agent-context/clear", {
      agent: state.agentSession.agent,
      session_id: state.agentSession.session_id,
      project_root: state.projectRootOverride.trim() || state.agentSession.repo_root || "",
    });
    state.agentSession = null;
    renderAgentContext({ session: null });
  } catch (_e) {
    await loadAgentContext();
  } finally {
    if (button) button.disabled = false;
  }
}

async function summarizeAgentContext() {
  const button = document.getElementById("agent-summary-run");
  const status = document.getElementById("agent-summary-status");
  const provider = document.getElementById("agent-summary-provider").value;
  const timeout = Number(document.getElementById("agent-summary-timeout").value || 20);
  if (!button || !status) return;
  button.disabled = true;
  status.classList.remove("error", "warn");
  status.textContent = "Summarizing captured agent context…";
  try {
    const payload = {
      provider,
      timeout_seconds: Math.max(1, Math.min(60, timeout || 20)),
      project_root: state.projectRootOverride.trim(),
    };
    if (state.agentSession) {
      payload.agent = state.agentSession.agent;
    }
    const data = await api("POST", "/api/dictation/agent-context/summarize", payload);
    state.agentSession = data.session || state.agentSession;
    const summary = data.summary || {};
    status.textContent = summary.summary
      ? `${summary.provider || provider}: ${summary.summary}`
      : "Summary generated.";
    await loadAgentContext();
    if (state.activeSection === "hooks") await loadAgentHooks();
  } catch (e) {
    status.classList.add("error");
    status.textContent = e.message;
  } finally {
    button.disabled = false;
  }
}

async function loadAgentHooks() {
  const banner = document.getElementById("hooks-meta-banner");
  const list = document.getElementById("hooks-agent-list");
  if (!banner || !list) return;
  const capture = document.getElementById("hooks-capture-messages").checked;
  banner.classList.remove("warn", "error");
  banner.textContent = "Loading…";
  list.innerHTML = "";
  try {
    const data = await api("GET", `/api/dictation/agent-hooks?capture_messages=${capture ? "true" : "false"}`);
    state.hooks = data;
    renderAgentHooks(data);
  } catch (e) {
    banner.classList.add("error");
    banner.textContent = e.message;
  }
}

function renderAgentHooks(data) {
  const banner = document.getElementById("hooks-meta-banner");
  const list = document.getElementById("hooks-agent-list");
  const summaryProviderStatus = document.getElementById("agent-summary-provider-status");
  const capture = !!data.capture_messages;
  banner.classList.remove("warn", "error");
  banner.innerHTML =
    `registry: <strong>${escapeHtml(data.registry_path || "—")}</strong>` +
    `  ·  assistant capture: <strong>${capture ? "included" : "not included"}</strong>`;
  if (summaryProviderStatus) {
    const summarizers = data.summarizers || {};
    summaryProviderStatus.innerHTML = ["codex", "claude"].map((provider) => {
      const status = summarizers[provider] || {};
      const state = status.available ? "available" : "not installed";
      const safety = status.safe_default ? "safe default" : `unsafe: ${status.safe_default_error || "blocked"}`;
      const command = status.command_display || provider;
      return `<span class="hook-status-item"><strong>${escapeHtml(provider)}</strong>: ${escapeHtml(state)} · ${escapeHtml(safety)}<br><code>${escapeHtml(command)}</code></span>`;
    }).join("<br>");
  }

  const agents = data.agents || {};
  list.innerHTML = ["claude", "codex"].map((agent) => {
    const entry = agents[agent] || {};
    const latest = entry.latest_session;
    const destination = (data.destinations || {})[agent] || "";
    const status = latest
      ? [
          `latest: ${latest.updated_at || "unknown"}`,
          `cwd: ${latest.cwd || "—"}`,
          `capture: ${latest.capture_messages ? "enabled" : "disabled"}`,
          latest.awaiting_response ? "awaiting response" : "",
        ].filter(Boolean).join(" · ")
      : "No hook events recorded yet.";
    return `
      <article class="hook-card">
        <h3>${escapeHtml(agent)}</h3>
        <p class="hook-status">Destination: ${escapeHtml(destination)}</p>
        <p class="hook-status">${escapeHtml(status)}</p>
        <div class="actions">
          <button class="btn primary" data-copy-command="${escapeAttr(entry.template_json || "")}">Copy template</button>
        </div>
        <pre class="hook-template"><code>${escapeHtml(entry.template_json || "{}")}</code></pre>
      </article>
    `;
  }).join("");
  wireCopyCommandButtons(list);
}

function basename(path) {
  const text = String(path || "").replace(/\/+$/, "");
  if (!text) return "";
  const parts = text.split("/");
  return parts[parts.length - 1] || text;
}

function projectRootParam(prefix) {
  const value = state.projectRootOverride.trim();
  return value ? `${prefix}project_root=${encodeURIComponent(value)}` : "";
}

async function applyProjectRootOverride() {
  const input = document.getElementById("project-root-override");
  const raw = input.value.trim();
  const status = document.getElementById("project-root-status");
  status.style.color = "var(--muted)";
  status.textContent = raw ? "Validating…" : "Using cwd project detection.";
  if (raw) {
    try {
      const data = await api("GET", `/api/dictation/project-context?project_root=${encodeURIComponent(raw)}`);
      input.value = data.project.root;
      status.style.color = "var(--accent-2)";
      status.textContent = `Selected ${data.project.name} (${data.project.anchor})`;
    } catch (e) {
      status.style.color = "var(--danger)";
      status.textContent = e.message;
      return;
    }
  }
  state.projectRootOverride = input.value.trim();
  if (state.projectRootOverride) {
    localStorage.setItem("holdspeak.projectRootOverride", state.projectRootOverride);
    rememberProjectRoot(state.projectRootOverride);
  } else {
    localStorage.removeItem("holdspeak.projectRootOverride");
    loadDetectedProjectContext();
  }
  refreshProjectScopedView();
}

function clearProjectRootOverride() {
  state.projectRootOverride = "";
  document.getElementById("project-root-override").value = "";
  localStorage.removeItem("holdspeak.projectRootOverride");
  loadDetectedProjectContext();
  refreshProjectScopedView();
}

async function loadDetectedProjectContext() {
  const status = document.getElementById("project-root-status");
  if (state.projectRootOverride.trim()) {
    status.style.color = "var(--accent-2)";
    status.textContent = `Selected override: ${state.projectRootOverride.trim()}`;
    return;
  }
  status.style.color = "var(--muted)";
  status.textContent = "Detecting cwd project…";
  try {
    const data = await api("GET", "/api/dictation/project-context");
    const project = data.project || {};
    status.style.color = "var(--accent-2)";
    status.textContent =
      `Using cwd: ${project.name || "project"} (${project.anchor || "detected"}) @ ${project.root || ""}`;
  } catch (e) {
    status.style.color = e.status === 404 ? "var(--warn)" : "var(--danger)";
    status.textContent = e.status === 404 ? "No cwd project detected." : e.message;
  }
}

function loadRecentProjectRoots() {
  try {
    const raw = JSON.parse(localStorage.getItem("holdspeak.recentProjectRoots") || "[]");
    return Array.isArray(raw) ? raw.filter((x) => typeof x === "string" && x.trim()).slice(0, 6) : [];
  } catch (_e) {
    return [];
  }
}

function saveRecentProjectRoots() {
  localStorage.setItem("holdspeak.recentProjectRoots", JSON.stringify(state.recentProjectRoots.slice(0, 6)));
  renderRecentProjectRoots();
}

function rememberProjectRoot(root) {
  const normalized = String(root || "").trim();
  if (!normalized) return;
  state.recentProjectRoots = [
    normalized,
    ...state.recentProjectRoots.filter((r) => r !== normalized),
  ].slice(0, 6);
  saveRecentProjectRoots();
}

function renderRecentProjectRoots() {
  const select = document.getElementById("project-root-recent");
  select.innerHTML = `<option value="">Recent roots</option>` + state.recentProjectRoots.map((root) =>
    `<option value="${escapeAttr(root)}">${escapeHtml(root)}</option>`
  ).join("");
}

async function useRecentProjectRoot() {
  const select = document.getElementById("project-root-recent");
  if (!select.value) return;
  document.getElementById("project-root-override").value = select.value;
  await applyProjectRootOverride();
  select.value = "";
}

function refreshProjectScopedView() {
  loadAgentContext();
  if (state.activeSection === "readiness") loadReadiness();
  if (state.activeSection === "blocks" && state.scope === "project") loadScope("project");
  if (state.activeSection === "kb") loadKB();
  if (state.activeSection === "hs") loadHSContext();
  if (state.activeSection === "hooks") loadAgentHooks();
  if (state.activeSection === "dry-run") clearDryRun();
}

// ── Init ─────────────────────────────────────────────────────────────
document.getElementById("project-root-override").value = state.projectRootOverride;
document.querySelectorAll('.scope-row button[data-scope]').forEach((b) =>
  b.addEventListener("click", () => loadScope(b.dataset.scope))
);
document.querySelectorAll('.scope-row button[data-section]').forEach((b) =>
  b.addEventListener("click", () => activateSection(b.dataset.section))
);
document.getElementById("btn-new").addEventListener("click", newBlock);
document.getElementById("kb-btn-add").addEventListener("click", kbAdd);
document.getElementById("kb-btn-starter").addEventListener("click", createStarterKB);
document.getElementById("kb-btn-save").addEventListener("click", kbSave);
document.getElementById("kb-btn-reset").addEventListener("click", kbReset);
document.getElementById("kb-btn-delete").addEventListener("click", kbDelete);
document.getElementById("hs-btn-save").addEventListener("click", saveHSContext);
document.getElementById("hs-btn-reset").addEventListener("click", resetHSContext);
document.getElementById("hs-suggestion-apply").addEventListener("click", applyProjectDocSuggestion);
document.getElementById("hs-suggestion-dismiss").addEventListener("click", dismissProjectDocSuggestion);
document.getElementById("rt-btn-save").addEventListener("click", saveRuntime);
document.getElementById("rt-btn-test").addEventListener("click", saveRuntimeAndTest);
document.getElementById("rt-btn-reset").addEventListener("click", () => rtState.last && renderRuntime(rtState.last));
document.getElementById("rt-btn-refresh").addEventListener("click", loadRuntime);
document.getElementById("rt-target-auto").addEventListener("click", () => {
  document.getElementById("rt-target-profile").value = "auto";
});
// Copilot depth controls (HS-40-03): segmented rewrite-passes + the
// reveal-on-toggle threshold.
document.querySelectorAll("#rt-rewrite-seg .seg-btn").forEach((btn) =>
  btn.addEventListener("click", () => setRewritePasses(btn.dataset.value))
);
document
  .getElementById("rt-target-detect-llm-enabled")
  .addEventListener("change", updateTargetDetectReveal);
// Memory + telemetry (HS-40-04).
document.getElementById("mem-add-form").addEventListener("submit", addCorrection);
document.getElementById("mem-btn-clear").addEventListener("click", clearAllCorrections);
document.getElementById("mem-btn-refresh").addEventListener("click", loadMemory);
document
  .getElementById("mem-corrections-enabled")
  .addEventListener("change", toggleCorrectionsEnabled);
// Journal (HS-45-02).
document.getElementById("journal-btn-refresh").addEventListener("click", loadJournal);
document.getElementById("journal-btn-clear").addEventListener("click", clearJournal);
document.getElementById("journal-search").addEventListener("input", renderJournal);
document.getElementById("journal-filter-source").addEventListener("change", renderJournal);
document.getElementById("journal-filter-warnings").addEventListener("change", renderJournal);
document.getElementById("journal-filter-corrected").addEventListener("change", renderJournal);
document.getElementById("dry-btn-run").addEventListener("click", runDryRun);
document.getElementById("dry-btn-clear").addEventListener("click", clearDryRun);
document.getElementById("project-root-apply").addEventListener("click", applyProjectRootOverride);
document.getElementById("project-root-clear").addEventListener("click", clearProjectRootOverride);
document.getElementById("project-root-recent").addEventListener("change", useRecentProjectRoot);
document.getElementById("agent-context-clear").addEventListener("click", clearAgentContext);
document.getElementById("agent-summary-run").addEventListener("click", summarizeAgentContext);
document.getElementById("agent-summary-refresh").addEventListener("click", loadAgentContext);
document.getElementById("hooks-btn-refresh").addEventListener("click", loadAgentHooks);
document.getElementById("hooks-capture-messages").addEventListener("change", loadAgentHooks);
document.getElementById("ready-btn-refresh").addEventListener("click", loadReadiness);
renderRecentProjectRoots();
loadDetectedProjectContext();
loadAgentContext();
loadStarterTemplates();
loadScope("global");
window.setInterval(loadAgentContext, 10000);
