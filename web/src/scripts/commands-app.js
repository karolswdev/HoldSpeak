// HS-52-05: the Voice Commands board behavior.
//
// Vanilla JS (no Alpine), matching the dictation-app list-editor pattern: cards are
// built with createElement (never innerHTML for user values — a keyword or command is
// user data), and persisted through PUT /api/settings. "What you see is what fires":
// the card preview and the editor preview are the same plain-language string the
// Python `VoiceMacroAction.preview()` produces, kept in lockstep here.

const KINDS = ["open_url", "launch_app", "shell", "type_text"];
const KIND_LABEL = {
  open_url: "Open URL",
  launch_app: "Launch app",
  shell: "Shell",
  type_text: "Type text",
};

function normalizeKeyword(text) {
  return String(text || "").trim().toLowerCase().replace(/[.!?,]+$/, "");
}

function previewFor(action) {
  const p = action.payload || "";
  if (action.kind === "open_url") return `opens ${p}`;
  if (action.kind === "launch_app") return `launches ${p}`;
  if (action.kind === "shell") return `runs: ${p}`;
  if (action.kind === "type_text") return `types: ${p}`;
  return p;
}

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2).toLowerCase(), v);
    else if (v !== undefined && v !== null) node.setAttribute(k, v);
  }
  for (const c of children) if (c != null) node.append(c);
  return node;
}

async function apiJson(url, options) {
  const res = await fetch(url, options);
  let data = {};
  try { data = await res.json(); } catch (_e) { data = {}; }
  if (!res.ok) throw new Error(data.error || data.detail || `Request failed (${res.status})`);
  return data;
}

export function mountVoiceCommands() {
  const root = document.querySelector(".vc");
  if (!root) return;

  const board = root.querySelector("[data-vc-board]");
  const flash = root.querySelector("[data-vc-flash]");
  const masterInput = root.querySelector("[data-vc-master]");
  const masterState = root.querySelector("[data-vc-master-state]");
  const emptyTemplate = root.querySelector("[data-vc-empty-template]");

  // editor elements
  const overlay = root.querySelector("[data-vc-editor]");
  const editorTitle = root.querySelector("[data-vc-editor-title]");
  const form = root.querySelector("[data-vc-form]");
  const keywordInput = root.querySelector("[data-vc-keyword]");
  const matchEl = root.querySelector("[data-vc-match]");
  const conflictEl = root.querySelector("[data-vc-conflict]");
  const previewWrap = root.querySelector("[data-vc-preview-wrap]");
  const previewEl = root.querySelector("[data-vc-preview]");
  const testBtn = root.querySelector("[data-vc-test]");
  const testResult = root.querySelector("[data-vc-test-result]");
  const saveBtn = root.querySelector("[data-vc-save]");

  const state = { settings: null, enabled: false, items: [], editingIndex: -1, draftKind: "open_url" };

  function showFlash(msg, tone) {
    flash.textContent = msg;
    flash.setAttribute("data-tone", tone);
    flash.hidden = false;
    setTimeout(() => { flash.hidden = true; }, tone === "error" ? 7000 : 3500);
  }

  function currentAction() {
    const input = root.querySelector(`[data-vc-payload-input="${state.draftKind}"]`);
    return { kind: state.draftKind, payload: input ? input.value : "" };
  }

  // ── render the board ──────────────────────────────────────────────────────
  function render() {
    board.setAttribute("aria-busy", "false");
    board.textContent = "";
    masterInput.checked = state.enabled;
    masterState.textContent = state.enabled ? "On" : "Off";
    root.querySelector("[data-vc-master-label]").classList.toggle("is-on", state.enabled);

    if (state.items.length === 0) {
      board.append(emptyTemplate.content.cloneNode(true));
      wireStarters();
      return;
    }

    const grid = el("div", { class: "vc-grid" });
    state.items.forEach((macro, i) => grid.append(card(macro, i)));
    const add = el("button", { class: "vc-add-card", type: "button", "aria-label": "Add a command", onclick: () => openEditor(-1) },
      el("span", { class: "vc-add-plus", "aria-hidden": "true", text: "+" }),
      el("span", { text: "Add a command" }),
    );
    grid.append(add);
    board.append(grid);
    if (!state.enabled) {
      board.prepend(el("p", { class: "vc-match", text: "Voice commands are off. Turn them on (top right) to use them." }));
    }
  }

  function card(macro, index) {
    const kind = macro.action.kind;
    const node = el("div", { class: `vc-card kind-${kind}` });

    const badge = el("span", { class: `vc-badge kind-${kind}`, text: KIND_LABEL[kind] || kind });
    const head = el("div", { class: "vc-card-head" },
      el("span", { class: "vc-keyword", text: macro.keyword, title: macro.keyword }),
      kind === "shell"
        ? el("span", { class: "vc-card-head", style: "gap:6px" }, badge, el("span", { class: "vc-runs-code", text: "⚠ runs code" }))
        : badge,
    );

    const preview = el("p", { class: "vc-preview-text", text: previewFor(macro.action) });
    const match = el("p", { class: "vc-match", text: `matches: ${normalizeKeyword(macro.keyword)}` });

    const testChip = el("span", { class: "vc-test-chip" });
    const foot = el("div", { class: "vc-card-foot" },
      el("button", { class: "vc-btn vc-btn--ghost", type: "button", onclick: (e) => testCard(macro.action, testChip, e.currentTarget) },
        el("span", { text: "▷ Test" })),
      testChip,
      el("span", { class: "vc-card-spacer" }),
      el("button", { class: "vc-icon-btn", type: "button", "aria-label": `Edit ${macro.keyword}`, onclick: () => openEditor(index) }, iconEdit()),
      el("button", { class: "vc-icon-btn", type: "button", "aria-label": `Delete ${macro.keyword}`, onclick: (e) => confirmDelete(index, e.currentTarget) }, iconTrash()),
    );

    node.append(head, preview, match, foot);
    return node;
  }

  function iconEdit() {
    const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("width", "16"); s.setAttribute("height", "16"); s.setAttribute("viewBox", "0 0 24 24");
    s.setAttribute("fill", "none"); s.setAttribute("stroke", "currentColor"); s.setAttribute("stroke-width", "2");
    s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
    s.innerHTML = '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/>';
    return s;
  }
  function iconTrash() {
    const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("width", "16"); s.setAttribute("height", "16"); s.setAttribute("viewBox", "0 0 24 24");
    s.setAttribute("fill", "none"); s.setAttribute("stroke", "currentColor"); s.setAttribute("stroke-width", "2");
    s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
    s.innerHTML = '<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m2 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>';
    return s;
  }

  // ── starters (empty state) ────────────────────────────────────────────────
  function wireStarters() {
    root.querySelectorAll("[data-vc-starter]").forEach((b) => {
      b.addEventListener("click", () => {
        try {
          const seed = JSON.parse(b.getAttribute("data-vc-starter"));
          openEditor(-1, { keyword: seed.keyword, action: { kind: seed.kind, payload: seed.payload } });
        } catch (_e) { /* ignore */ }
      });
    });
    const add = root.querySelector("[data-vc-add]");
    if (add) add.addEventListener("click", () => openEditor(-1));
  }

  // ── the editor ────────────────────────────────────────────────────────────
  function setKind(kind) {
    state.draftKind = kind;
    root.querySelectorAll("[data-vc-kind]").forEach((b) => {
      const on = b.getAttribute("data-vc-kind") === kind;
      b.setAttribute("aria-checked", on ? "true" : "false");
    });
    root.querySelectorAll("[data-vc-pf]").forEach((f) => { f.hidden = f.getAttribute("data-vc-pf") !== kind; });
    updatePreview();
  }

  function updatePreview() {
    const action = currentAction();
    const has = action.payload.trim().length > 0;
    previewWrap.hidden = !has;
    if (has) previewEl.textContent = previewFor(action);
    // match hint + conflict
    const norm = normalizeKeyword(keywordInput.value);
    matchEl.textContent = norm ? `matches: ${norm}` : "";
    const clash = norm && state.items.some((m, i) => i !== state.editingIndex && normalizeKeyword(m.keyword) === norm);
    conflictEl.hidden = !clash;
    if (clash) conflictEl.textContent = "⚠ another command already uses this keyword";
    saveBtn.disabled = !(keywordInput.value.trim() && has);
  }

  function openEditor(index, seed) {
    state.editingIndex = index;
    testResult.textContent = "";
    testResult.className = "vc-test-result";
    const macro = seed || (index >= 0 ? state.items[index] : { keyword: "", action: { kind: "open_url", payload: "" } });
    editorTitle.textContent = index >= 0 ? "Edit command" : "New command";
    keywordInput.value = macro.keyword || "";
    KINDS.forEach((k) => { const inp = root.querySelector(`[data-vc-payload-input="${k}"]`); if (inp) inp.value = ""; });
    const inp = root.querySelector(`[data-vc-payload-input="${macro.action.kind}"]`);
    if (inp) inp.value = macro.action.payload || "";
    setKind(macro.action.kind);
    overlay.hidden = false;
    requestAnimationFrame(() => { overlay.querySelector(".vc-editor").focus(); keywordInput.focus(); });
  }

  function closeEditor() { overlay.hidden = true; }

  async function testCurrent() {
    const action = currentAction();
    testResult.textContent = "Testing…";
    testResult.className = "vc-test-result";
    try {
      const data = await apiJson("/api/commands/test", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(action),
      });
      if (data.ok) { testResult.textContent = data.tested ? "ran ✓" : (data.note || "ok"); testResult.className = "vc-test-result ok"; }
      else { testResult.textContent = data.error || "failed"; testResult.className = "vc-test-result err"; }
    } catch (e) { testResult.textContent = e.message; testResult.className = "vc-test-result err"; }
  }

  async function testCard(action, chip, btn) {
    chip.textContent = "…"; chip.className = "vc-test-chip";
    if (btn) btn.disabled = true;
    try {
      const data = await apiJson("/api/commands/test", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(action),
      });
      if (data.ok) { chip.textContent = data.tested ? "ran ✓" : "ok"; chip.className = "vc-test-chip ok"; }
      else { chip.textContent = data.error || "failed"; chip.className = "vc-test-chip err"; }
    } catch (e) { chip.textContent = e.message; chip.className = "vc-test-chip err"; }
    finally { if (btn) btn.disabled = false; setTimeout(() => { chip.textContent = ""; }, 5000); }
  }

  // ── persistence ───────────────────────────────────────────────────────────
  async function persist(items, enabled) {
    const data = await apiJson("/api/settings", {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dictation: { macros: { enabled, items } } }),
    });
    state.settings = data.settings || state.settings;
    const macros = (((state.settings || {}).dictation || {}).macros) || { enabled, items };
    state.enabled = !!macros.enabled;
    state.items = macros.items || [];
  }

  async function saveFromEditor(ev) {
    ev.preventDefault();
    const action = currentAction();
    const keyword = keywordInput.value.trim();
    if (!keyword || !action.payload.trim()) return;
    const macro = { keyword, action: { kind: action.kind, payload: action.payload } };
    const items = state.items.slice();
    if (state.editingIndex >= 0) items[state.editingIndex] = macro; else items.push(macro);
    saveBtn.disabled = true;
    try {
      await persist(items, state.enabled);
      closeEditor();
      render();
      showFlash(state.editingIndex >= 0 ? "Command updated." : `Added "${keyword}".`, "ok");
    } catch (e) {
      showFlash(e.message, "error");
      saveBtn.disabled = false;
    }
  }

  function confirmDelete(index, btn) {
    const foot = btn.closest(".vc-card-foot");
    if (!foot) return;
    const macro = state.items[index];
    const confirm = el("span", { class: "vc-confirm" },
      el("span", { text: `Delete "${macro.keyword}"?` }),
      el("button", { class: "vc-btn vc-btn--ghost", type: "button", text: "Cancel", onclick: () => render() }),
      el("button", { class: "vc-btn vc-btn--danger", type: "button", text: "Delete", onclick: async () => {
        const items = state.items.slice(); items.splice(index, 1);
        try { await persist(items, state.enabled); render(); showFlash("Command deleted.", "ok"); }
        catch (e) { showFlash(e.message, "error"); }
      } }),
    );
    foot.textContent = "";
    foot.append(confirm);
  }

  async function toggleMaster() {
    const next = masterInput.checked;
    try { await persist(state.items, next); render(); }
    catch (e) { masterInput.checked = !next; showFlash(e.message, "error"); }
  }

  // ── wire static controls ──────────────────────────────────────────────────
  masterInput.addEventListener("change", toggleMaster);
  root.querySelectorAll("[data-vc-kind]").forEach((b) => b.addEventListener("click", () => setKind(b.getAttribute("data-vc-kind"))));
  keywordInput.addEventListener("input", updatePreview);
  root.querySelectorAll("[data-vc-payload-input]").forEach((i) => i.addEventListener("input", updatePreview));
  testBtn.addEventListener("click", testCurrent);
  form.addEventListener("submit", saveFromEditor);
  root.querySelectorAll("[data-vc-editor-close]").forEach((b) => b.addEventListener("click", closeEditor));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !overlay.hidden) closeEditor(); });

  // ── load ──────────────────────────────────────────────────────────────────
  (async () => {
    try {
      const settings = await apiJson("/api/settings");
      state.settings = settings;
      const macros = ((settings.dictation || {}).macros) || { enabled: false, items: [] };
      state.enabled = !!macros.enabled;
      state.items = macros.items || [];
      render();
    } catch (e) {
      board.setAttribute("aria-busy", "false");
      board.textContent = "";
      board.append(el("p", { class: "vc-match", text: `Could not load voice commands: ${e.message}` }));
    }
  })();
}
