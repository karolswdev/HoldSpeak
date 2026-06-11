// ── Dry-run preview + the moment of truth (HS-45-03 / HS-48-03) ──────
// The dry-run trace, the "was that right? fix it here" ritual (shared with
// every journal entry), and the honest post-correction copy.
import {
  state,
  api,
  escapeHtml,
  escapeAttr,
  plural,
  learnSigChip,
  renderDryTelemetry,
} from "./core.js";
import {
  hsState,
  extractProjectDocSuggestion,
  renderProjectDocSuggestion,
} from "./knowledge.js";
import { loadLearningDigest } from "./memory.js";

export async function runDryRun() {
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

export function renderDryRun(data) {
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
  // A dry-run still produces output without a runtime (lexical routing) — so
  // "disabled"/"unavailable"/no-runtime is an advisory amber state, not a red
  // error. Only a genuine error status is alarming.
  if (data.runtime_status !== "loaded")
    meta.classList.add(data.runtime_status === "error" ? "error" : "warn");
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

  // Advisory notes (stage skips, "llm disabled", target fallbacks) are calm —
  // not a red error box. They read as informational context, not failure.
  const warnings = (data.warnings || []).length
    ? `<div class="dry-notes"><span class="dry-notes-title">Notes</span><ul>${(data.warnings || [])
        .map((w) => `<li>${escapeHtml(w)}</li>`)
        .join("")}</ul></div>`
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
  const sig = data.learning && data.learning.matched ? learnSigChip(data.learning.similar) : "";
  host.hidden = false;
  host.innerHTML = correctionRitual({ journalId, block, target, routed, sig });
  wireFixit(host);
}

// ── HS-48-03: the one-tap right/wrong ritual ──────────────────────────────
// One inline component, reused by the dry-run result and every journal entry,
// so "that was wrong" is a normal tap instead of a buried form. "Right" is a
// calm client-only acknowledgement (no write churn). "Wrong" opens the existing
// correct path pre-scoped — block or target chosen in one tap, the routed value
// pre-filled as the placeholder. Submit reuses POST /journal/{id}/correct (no
// new write primitive) and states honest coverage. Focus-safe: panels reveal on
// click and keyboard focus stays where the user put it (never stolen).
export function correctionRitual(opts) {
  const { journalId, block, target, routed, sig } = opts;
  const routedLine = routed ? `<span class="moment-routed">${routed}</span>` : "";
  const targetScope = target
    ? `<button type="button" class="fixit-scope" data-fixit-scope="target">Wrong target</button>`
    : "";
  return `<div class="fixit" data-journal-id="${escapeAttr(String(journalId))}" data-block="${escapeAttr(block || "")}" data-target="${escapeAttr(target || "")}">
    <div class="fixit-ask">
      <span class="moment-q">Was that right?</span>
      ${routedLine}
      ${sig || ""}
      <span class="moment-spacer"></span>
      <button type="button" class="btn fixit-yes" data-fixit-yes>Right</button>
      <button type="button" class="btn moment-fix-btn" data-fixit-no>Fix it →</button>
    </div>
    <div class="fixit-scopes" hidden>
      <span class="fixit-scope-q">What was wrong?</span>
      <button type="button" class="fixit-scope" data-fixit-scope="intent">Wrong block</button>
      ${targetScope}
    </div>
    <form class="moment-form fixit-form" hidden>
      <p class="moment-hint">Teach the copilot the right <span data-fixit-kind-label>block</span> — it'll nudge similar dictations next time, and this entry is marked corrected.</p>
      <div class="row">
        <label>Correct to
          <input type="text" data-fixit-value placeholder="block id" />
        </label>
        <div class="actions">
          <button type="submit" class="btn primary" data-fixit-submit>Teach</button>
          <button type="button" class="btn" data-fixit-cancel>Cancel</button>
        </div>
      </div>
      <div data-fixit-msg></div>
    </form>
    <div class="fixit-done moment-done" role="status" hidden></div>
  </div>`;
}

export function wireFixit(root) {
  if (!root) return;
  root.querySelectorAll(".fixit:not([data-wired])").forEach((el) => {
    el.dataset.wired = "1";
    el.addEventListener("click", onFixitClick);
    const form = el.querySelector(".fixit-form");
    if (form) form.addEventListener("submit", submitMomentFix);
  });
}

function onFixitClick(ev) {
  const root = ev.target.closest(".fixit");
  if (!root) return;
  if (ev.target.closest("[data-fixit-yes]")) {
    showFixitDone(root, "Glad it landed. Nothing to teach.");
    return;
  }
  if (ev.target.closest("[data-fixit-no]")) {
    // One teachable dimension -> go straight to it; two -> pick in one tap.
    if (root.dataset.target) {
      root.querySelector(".fixit-ask").hidden = true;
      root.querySelector(".fixit-scopes").hidden = false;
    } else {
      setFixitScope(root, "intent");
    }
    return;
  }
  const scope = ev.target.closest("[data-fixit-scope]");
  if (scope) {
    setFixitScope(root, scope.dataset.fixitScope);
    return;
  }
  if (ev.target.closest("[data-fixit-cancel]")) {
    root.querySelector(".fixit-form").hidden = true;
    root.querySelector(".fixit-scopes").hidden = true;
    root.querySelector(".fixit-ask").hidden = false;
  }
}

function setFixitScope(root, kind) {
  const isTarget = kind === "target";
  root.dataset.fixitKind = kind;
  const label = root.querySelector("[data-fixit-kind-label]");
  if (label) label.textContent = isTarget ? "target profile" : "block";
  const input = root.querySelector("[data-fixit-value]");
  if (input) {
    input.value = "";
    input.setAttribute(
      "placeholder",
      isTarget ? root.dataset.target || "target profile" : root.dataset.block || "block id",
    );
  }
  root.querySelector(".fixit-ask").hidden = true;
  root.querySelector(".fixit-scopes").hidden = true;
  // Focus-safe: the input is revealed but never programmatically focused.
  root.querySelector(".fixit-form").hidden = false;
}

function showFixitDone(root, text) {
  root.querySelector(".fixit-ask").hidden = true;
  const scopes = root.querySelector(".fixit-scopes");
  if (scopes) scopes.hidden = true;
  const form = root.querySelector(".fixit-form");
  if (form) form.hidden = true;
  const done = root.querySelector(".fixit-done");
  done.hidden = false;
  done.innerHTML = `<span class="moment-check" aria-hidden="true">✓</span><span>${text}</span>`;
}

// Honest post-correction copy — real coverage, split on the corrections posture,
// shared by every surface that teaches. Quiet about reach it cannot claim.
function correctionDoneText(res) {
  if (!res || !res.taught) {
    return "Recorded against the Journal entry. (Nothing was taught — the text looked like a secret, so it wasn't stored.)";
  }
  const n = Number(res.similar) || 0;
  let reach = "";
  if (n > 0) {
    reach = res.enabled
      ? ` It now nudges ${n} similar ${plural(n, "dictation")} toward this.`
      : ` It matches ${n} similar ${plural(n, "dictation")} — turn on corrections to use it.`;
  } else if (!res.enabled) {
    reach = " Turn on corrections to use it while routing.";
  }
  return `Taught — the Journal entry is marked corrected.${reach}`;
}

async function submitMomentFix(ev) {
  ev.preventDefault();
  const root = ev.target.closest(".fixit");
  if (!root) return;
  const id = root.dataset.journalId;
  const kind = root.dataset.fixitKind || "intent";
  const input = root.querySelector("[data-fixit-value]");
  const value = input ? input.value.trim() : "";
  const msg = root.querySelector("[data-fixit-msg]");
  if (msg) msg.innerHTML = "";
  if (!value) {
    if (msg)
      msg.innerHTML = `<div class="error-box">Enter the correct ${kind === "target" ? "target profile" : "block id"}.</div>`;
    return;
  }
  try {
    const res = await api("POST", `/api/dictation/journal/${encodeURIComponent(id)}/correct`, { kind, value });
    showFixitDone(root, correctionDoneText(res));
    // Reflect it: flag the journal card corrected + refresh the digest hero
    // (harmless when the Memory tab isn't showing).
    const card = root.closest(".journal-card");
    if (card) card.classList.add("is-corrected");
    try {
      loadLearningDigest();
    } catch (_) {}
  } catch (e) {
    if (msg) msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
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

export function clearDryRun() {
  document.getElementById("dry-utterance").value = "";
  document.getElementById("dry-msg").innerHTML = "";
  document.getElementById("dry-meta").textContent = "No dry-run yet.";
  document.getElementById("dry-meta").classList.remove("warn", "error");
  document.getElementById("dry-final").innerHTML = "";
  const moment = document.getElementById("dry-moment");
  if (moment) { moment.hidden = true; moment.innerHTML = ""; }
  document.getElementById("dry-trace").innerHTML = "";
}
