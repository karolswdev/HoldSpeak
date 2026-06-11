// ── Project knowledge: Facts (project.yaml kb) + Context (.hs/) ──────
// Two related-but-distinct teaching surfaces (HS-47 settled the concepts):
// "Project Facts" is the project.yaml kb map behind {project.kb.*}
// placeholders; "Project Context" is the .hs/ Markdown folder the optional
// project-rewriter stage reads. Plus the HS-47-03 guided setup and the
// HS-48-01 project-doc suggestion review panel.
import {
  state,
  api,
  escapeHtml,
  escapeAttr,
  projectRootParam,
  activateSection,
  registerSection,
  loadSection,
  renderDryTelemetry,
} from "./core.js";
import { knNudgeState } from "./discovery-nudge.js";

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
// HS-47-02: a small worked example the empty state loads into the editor so a
// first-time user sees what good context looks like. Loaded unsaved; the user
// reviews and saves (never written without approval).
const HS_EXAMPLE_INSTRUCTIONS = `# How HoldSpeak should rewrite for this project

- Keep dictation terse and imperative; this is a developer's repo.
- Expand spoken shorthand into our real names (see .hs/terms.md).
- Never invent file paths or commands; if you are unsure, leave a TODO.
- Match the target: tighter for the terminal, fuller prose for chat.
`;
export const hsState = {
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
  // HS-47-02: the teaching empty state is static markup in dictation.astro; we
  // only toggle its `hidden` attribute so its scoped CSS keeps applying.
  const empty = document.getElementById("kb-empty");
  if (!kbState.detected) {
    if (empty) empty.hidden = true;
    host.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">No project detected. Navigate <code>holdspeak</code> from inside a project directory.</p>`;
    return;
  }
  if (!kbState.rows.length) {
    if (empty) empty.hidden = false;
    host.innerHTML = "";
    return;
  }
  if (empty) empty.hidden = true;
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

export function kbAdd() {
  if (!kbState.detected) return;
  kbState.rows.push({ key: "", value: "" });
  renderKBRows();
}

export function kbReset() {
  kbState.rows = Object.entries(kbState.lastLoaded || {}).map(([k, v]) => ({ key: k, value: v ?? "" }));
  document.getElementById("kb-msg").innerHTML = "";
  renderKBRows();
}

export async function kbSave() {
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

export async function createStarterKB(options = {}) {
  const msg = document.getElementById("kb-msg");
  msg.innerHTML = "";
  try {
    const data = await api("POST", `/api/dictation/project-kb/starter${projectRootParam("?")}`);
    if (options.switchToKB) activateSection("kb");
    kbState.lastLoaded = data.kb;
    kbState.detected = data.detected;
    kbState.kbPath = data.kb_path;
    kbState.rows = Object.entries(data.kb || {}).map(([k, v]) => ({ key: k, value: v ?? "" }));
    msg.innerHTML = youreSetHtml("Created starter project facts. Fill in a value (like stack), add the \"Project facts context\" block in Blocks, then");
    renderKBMeta(data);
    renderKBRows();
    if (state.activeSection === "readiness") loadSection("readiness");
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

export async function kbDelete() {
  if (!kbState.detected) return;
  const ok = await window.holdspeakConfirm({
    title: `Delete ${kbState.kbPath}?`,
    body: "The project facts file is removed from disk. The enclosing .holdspeak/ directory is preserved so other project state (blocks, runtime config) stays intact.",
    scopeNote: "Only the local project facts file is affected. Source files referenced from inside it are not touched.",
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
    // HS-47-04: if we arrived here from the discovery nudge, open the guided
    // setup now that the project is detected.
    if (knNudgeState.pendingOpen) {
      knNudgeState.pendingOpen = false;
      openHsSetup();
    }
  } catch (e) {
    knNudgeState.pendingOpen = false;
    banner.classList.add(e.status === 404 ? "warn" : "error");
    banner.textContent = e.message;
    const hsEmpty = document.getElementById("hs-empty");
    if (hsEmpty) hsEmpty.hidden = true;
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
  // HS-47-02: teaching empty state when a project is detected but .hs/ does not
  // exist yet. Static markup, toggled (not re-rendered) so scoped CSS applies.
  const empty = document.getElementById("hs-empty");
  if (empty) empty.hidden = !(hsState.detected && !hsState.contextDirExists);
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

// HS-47-02: one-click starter for the .hs/ empty state. Drops an example into
// the instructions.md editor without writing anything; the user reviews and
// clicks Save, honoring the never-write-without-approval rule.
export function hsLoadExample() {
  if (!hsState.detected) return;
  hsState.selected = "instructions.md";
  hsState.files = hsState.files || {};
  hsState.files["instructions.md"] = {
    ...(hsState.files["instructions.md"] || {}),
    content: HS_EXAMPLE_INSTRUCTIONS,
    source: "new",
    exists: false,
    truncated: false,
  };
  renderHSFileList();
  renderHSEditor();
  // Focus-safe: bring the editor into view but never steal keyboard focus — the
  // dictation flow is sacred (see test_moment_affordance_present_and_focus_safe).
  const editor = document.getElementById("hs-editor");
  if (editor) {
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    editor.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
  }
  const msg = document.getElementById("hs-msg");
  if (msg) {
    msg.innerHTML = `<div class="ok-box">Loaded an example into .hs/instructions.md. Review it, then click Save to create the file.</div>`;
  }
}

// ── HS-47-03: guided setup ───────────────────────────────────────────
// A curated starter set: short templates with fill-in prompts, kept to the
// files most worth having on day one.
const STARTER_HS_FILES = {
  "instructions.md": HS_EXAMPLE_INSTRUCTIONS,
  "context.md": `# Project context

- What this repo is: <one line>
- Key entry points and paths: <e.g. the CLI, src/, the web app>
- Important constraints: <perf budgets, security rules, things to never touch>
`,
  "terms.md": `# Project vocabulary

- <ProductName>: what we call the product in writing.
- <ACRONYM>: what it expands to.
- Spelling: <e.g. British spelling, "colour" not "color">
`,
};

// A copiable, repo-aware prompt the user pastes into their own coding agent
// (Claude / Codex) to draft the .hs/ files. The drafting happens on the user's
// machine; HoldSpeak never calls a model here.
function buildAgentPrompt(project) {
  const name = (project && project.name) || "this repo";
  const root = (project && project.root) || ".";
  return `You are setting up "project context" for HoldSpeak in the repo ${name} (at ${root}).

HoldSpeak is a local dictation tool. When its optional rewrite stage is on, it
reads the Markdown files in this repo's .hs/ folder and uses them to rewrite my
spoken dictation so it matches this project's conventions. Your job: read this
repo and write those .hs/ files. Keep every file short, factual, and specific to
THIS repo. No boilerplate, no secrets, no invented facts. If you are unsure about
something, leave a clearly marked TODO instead of guessing.

Create these files under .hs/ (skip any that do not apply):

- instructions.md: how HoldSpeak should rewrite dictation here. Tone, length,
  what to expand, and what to leave exactly as said.
- context.md: the architecture, the key paths, and the constraints a new
  contributor needs to know.
- terms.md: project vocabulary, acronyms, product names, and preferred spellings.
- workflows.md: the real test, build, review, and deploy commands.
- targets.md: per-target style notes (Codex, Claude, terminal, browser, editor,
  chat) if they should differ.

Worked example for instructions.md:

    # How HoldSpeak should rewrite for this project
    - Keep dictation terse and imperative; this is a developer's repo.
    - Expand "the CLI" to its real name (see terms.md).
    - Never invent file paths or commands; if unsure, leave a TODO.

When you are done, list which files you created with a one-line summary of each,
so I can review them in HoldSpeak's Project Context tab before they take effect.`;
}

function renderHsAgentPrompt() {
  const pre = document.getElementById("hs-agent-prompt");
  if (pre) pre.textContent = buildAgentPrompt(hsState.detected);
}

export function openHsSetup() {
  if (!hsState.detected) return;
  const empty = document.getElementById("hs-empty");
  if (empty) empty.hidden = true;
  renderHsAgentPrompt();
  const setup = document.getElementById("hs-setup");
  if (setup) {
    setup.hidden = false;
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setup.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  }
}

export function closeHsSetup() {
  const setup = document.getElementById("hs-setup");
  if (setup) setup.hidden = true;
  const empty = document.getElementById("hs-empty");
  if (empty) empty.hidden = !(hsState.detected && !hsState.contextDirExists);
}

export async function hsCopyAgentPrompt() {
  const prompt = buildAgentPrompt(hsState.detected);
  const msg = document.getElementById("hs-setup-msg");
  try {
    await navigator.clipboard.writeText(prompt);
    if (msg) msg.innerHTML = `<div class="ok-box">Prompt copied. Paste it into Claude or Codex, then review the files it writes here.</div>`;
  } catch (e) {
    if (msg) msg.innerHTML = `<div class="error-box">Could not copy automatically. Select the prompt text above and copy it manually.</div>`;
  }
}

// "You're set" hand-off: a success line that routes into the dry-run.
function youreSetHtml(prefix) {
  return `<div class="ok-box">${escapeHtml(prefix)} <button class="kn-linkbtn" type="button" data-section-jump="dry-run">Try a dry-run</button> to see it affect your dictation.</div>`;
}

export async function hsCreateStarterSet() {
  if (!hsState.detected) return;
  const names = Object.keys(STARTER_HS_FILES);
  const ok = await window.holdspeakConfirm({
    title: "Create a starter context set?",
    body: `HoldSpeak will create ${names.length} files under .hs/: ${names.join(", ")}. They are templates with fill-in prompts; review and edit each here afterward.`,
    scopeNote: "Existing .hs/ files with these names are overwritten. Nothing else in the repo is touched.",
    confirmLabel: "Create files",
  });
  if (!ok) return;
  const msg = document.getElementById("hs-setup-msg");
  if (msg) msg.innerHTML = "";
  try {
    await api("PUT", `/api/dictation/project-hs${projectRootParam("?")}`, { files: STARTER_HS_FILES });
    await loadHSContext();
    if (msg) {
      msg.innerHTML = youreSetHtml("Starter context created under .hs/. Refine each file, turn on the rewrite stage in Runtime, then");
    }
  } catch (e) {
    if (msg) msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

export async function saveHSContext() {
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
    if (state.activeSection === "readiness") loadSection("readiness");
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

export function resetHSContext() {
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

export function renderProjectDocSuggestion() {
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

export function extractProjectDocSuggestion(data) {
  const stages = data && Array.isArray(data.stages) ? data.stages : [];
  for (const stage of stages) {
    const suggestion = stage && stage.metadata && stage.metadata.project_doc_suggestion;
    if (suggestion && typeof suggestion === "object") return suggestion;
  }
  return null;
}

export async function applyProjectDocSuggestion() {
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

export async function dismissProjectDocSuggestion() {
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

registerSection("kb", loadKB);
registerSection("hs", loadHSContext);
