// ── Blocks: the intent-block list, starter templates, and the editor ─
import {
  state,
  api,
  deepClone,
  escapeHtml,
  escapeAttr,
  projectRootParam,
  activateSection,
} from "./core.js";
import { renderDryRun } from "./dryrun.js";

const PLACEHOLDER_RE = /\{([^{}]*)\}/g;
const VALID_NAME_RE = /^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$/;

// ── Loading ──────────────────────────────────────────────────────────
export async function loadScope(scope) {
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

export async function loadStarterTemplates() {
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

export async function createFromTemplate(templateId, options = {}) {
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

export function newBlock() {
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
