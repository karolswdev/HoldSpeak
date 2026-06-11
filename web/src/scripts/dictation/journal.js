// ── Journal (HS-45-02): the said → routed → typed afterlife ──────────
// Plus replay (HS-45-04) and the one-tap correction ritual hooks (HS-48-03).
import {
  api,
  escapeHtml,
  escapeAttr,
  relativeTime,
  learnSigChip,
  registerSection,
} from "./core.js";
import { correctionRitual, wireFixit } from "./dryrun.js";

const journalState = { items: [], retention: 500, enabled: true };

export async function loadJournal() {
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

export function renderJournal() {
  const list = document.getElementById("journal-list");
  if (!list) return;
  const items = journalState.items.filter(journalMatches);
  if (!journalState.items.length) {
    list.innerHTML = `<div class="journal-empty">
      <svg class="journal-empty-glyph" viewBox="0 0 24 24" width="40" height="40" aria-hidden="true">
        <path fill="currentColor" d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2Z"/>
      </svg>
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
  list.querySelectorAll("button[data-journal-replay]").forEach((btn) =>
    btn.addEventListener("click", () => replayJournalEntry(btn.dataset.journalReplay, btn))
  );
  // HS-48-03: wire the one-tap right/wrong ritual on each entry.
  wireFixit(list);
}

// ── Replay (HS-45-04): prove it learned ────────────────────────────────
function replayDiffRow(label, before, after) {
  const changed = (before || "—") !== (after || "—");
  return `<div class="replay-row ${changed ? "is-changed" : ""}">
    <span class="replay-label">${escapeHtml(label)}</span>
    <span class="replay-before">${escapeHtml(before || "—")}</span>
    <span class="replay-arrow" aria-hidden="true">→</span>
    <span class="replay-after">${escapeHtml(after || "—")}</span>
  </div>`;
}

async function replayJournalEntry(id, btn) {
  const host = document.querySelector(`[data-replay-host="${CSS.escape(String(id))}"]`);
  if (!host) return;
  host.hidden = false;
  host.innerHTML = `<p class="replay-pending">Replaying through the current pipeline…</p>`;
  if (btn) btn.disabled = true;
  try {
    const data = await api("POST", `/api/dictation/journal/${encodeURIComponent(id)}/replay`);
    const b = data.before || {};
    const a = data.after || {};
    const blockBefore = b.block_id ? `${b.block_id}${b.confidence != null ? ` @ ${Number(b.confidence).toFixed(2)}` : ""}` : "";
    const blockAfter = a.block_id ? `${a.block_id}${a.confidence != null ? ` @ ${Number(a.confidence).toFixed(2)}` : ""}` : "";
    const headline = data.changed
      ? `<span class="replay-changed">↻ The pipeline routes this differently now.</span>`
      : `<span class="replay-same">Same result as before — nothing's changed for this one yet.</span>`;
    const finalText = a.final_text || "";
    host.innerHTML = `
      <div class="replay-head">${headline}</div>
      ${replayDiffRow("route", blockBefore, blockAfter)}
      ${replayDiffRow("target", b.target_profile, a.target_profile)}
      <div class="replay-final">
        <span class="replay-label">now types</span>
        <div class="replay-final-frame">
          <p>${escapeHtml(finalText) || "<em>(empty)</em>"}</p>
          <button type="button" class="cmd-copy" data-cmd-copy data-command="${escapeAttr(finalText)}" aria-label="Copy the improved result"><span data-cmd-copy-label>Copy</span></button>
        </div>
      </div>
      <p class="replay-note">Preview only — nothing was typed. Copy the improved result to use it.</p>`;
  } catch (e) {
    host.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  } finally {
    if (btn) btn.disabled = false;
  }
}

function latSegClass(sid) {
  return "lat-" + sid.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
}

function renderLatencyStrip(item) {
  const stages = item.stage_ms || {};
  const ids = Object.keys(stages);
  const total = Number(item.total_ms) || ids.reduce((s, k) => s + (Number(stages[k]) || 0), 0);
  if (!ids.length || total <= 0) {
    return `<div class="lat-strip lat-strip--empty">No per-stage timing recorded${
      total ? ` · ${total.toFixed(0)} ms total` : ""
    }.</div>`;
  }
  const segs = ids
    .map((sid) => {
      const ms = Number(stages[sid]) || 0;
      const pct = Math.max(3, Math.round((ms / total) * 100));
      return `<span class="lat-seg ${escapeAttr(latSegClass(sid))}" style="width:${pct}%" title="${escapeAttr(sid)} · ${ms.toFixed(0)} ms"></span>`;
    })
    .join("");
  const keys = ids
    .map((sid) => {
      const ms = Number(stages[sid]) || 0;
      return `<span class="lat-key"><span class="lat-dot ${escapeAttr(latSegClass(sid))}"></span>${escapeHtml(sid)} <b>${ms.toFixed(0)}ms</b></span>`;
    })
    .join("");
  return `<div class="lat-strip" role="img" aria-label="per-stage latency, total ${total.toFixed(0)} milliseconds">
    <div class="lat-strip-head">
      <span class="lat-strip-title">Latency</span>
      <span class="lat-total">${total.toFixed(0)} ms total</span>
    </div>
    <div class="lat-bar">${segs}</div>
    <div class="lat-legend">${keys}</div>
  </div>`;
}

function renderJournalEntry(item) {
  const spoken = item.source === "dictation";
  const sourceChip = `<span class="jr-source ${spoken ? "src-spoken" : "src-dry"}">${spoken ? "Spoken" : "Dry-run"}</span>`;
  const when = item.created_at ? `<span class="jr-when" title="${escapeAttr(item.created_at)}">${escapeHtml(relativeTime(item.created_at))}</span>` : "";
  const corrected = item.corrected
    ? `<span class="jr-corrected" title="You corrected this — the copilot learned from it">✓ corrected</span>`
    : "";
  const learnSig = item.learning && item.learning.matched ? learnSigChip(item.learning.similar) : "";
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
      ${learnSig}
      <span class="jr-spacer"></span>
      ${when}
      <button class="jr-replay-btn" type="button" data-journal-replay="${escapeAttr(String(item.id))}" title="Re-run this through the current pipeline">
        <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M12 5V2L7 7l5 5V8a5 5 0 1 1-5 5H5a7 7 0 1 0 7-8Z"/></svg>
        Replay
      </button>
      <button class="jr-del" type="button" data-journal-del="${escapeAttr(String(item.id))}" title="Delete this entry" aria-label="Delete this journal entry">
        <svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h4v2H4V5h4l1-2Zm-3 6h12l-1 11a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 9Z"/></svg>
      </button>
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
    ${item.corrected ? "" : correctionRitual({ journalId: item.id, block: item.block_id, target: item.target_profile, routed: "", sig: "" })}
    <div class="jr-replay" data-replay-host="${escapeAttr(String(item.id))}" hidden></div>
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

export async function clearJournal() {
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

registerSection("journal", loadJournal);
