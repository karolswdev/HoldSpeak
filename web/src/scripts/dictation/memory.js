// ── Memory + telemetry (HS-40-04) ───────────────────────────────────
// HS-48-01: the "What HoldSpeak learned" digest. Read-only; every number is
// real and comes from the same Jaccard matcher that nudges routing.
import {
  api,
  escapeHtml,
  escapeAttr,
  relativeTime,
  plural,
  learnSigChip,
  projectRootParam,
  registerSection,
} from "./core.js";

let learnWindow = "week";

export async function loadLearningDigest(win) {
  const host = document.getElementById("learn-digest");
  if (!host) return;
  if (win) learnWindow = win;
  host.textContent = "Loading…";
  try {
    const data = await api("GET", `/api/dictation/learning-digest?window=${encodeURIComponent(learnWindow)}`);
    renderLearningDigest(data);
  } catch (e) {
    host.innerHTML = `<div class="learn-empty"><p class="learn-empty-sub">${escapeHtml(e.message)}</p></div>`;
  }
}

function renderLearningDigest(data) {
  const host = document.getElementById("learn-digest");
  if (!host) return;
  const t = (data && data.totals) || {};
  const made = Number(t.corrections_made) || 0;
  const corrected = Number(t.dictations_corrected) || 0;
  const nudged = Number(t.similar_nudged) || 0;
  const windowLabel = data.window === "all" ? "all time" : "this week";

  // Stay quiet when there is nothing real to show (no invented learning).
  if (!made && !corrected) {
    host.innerHTML = `<div class="learn-empty">
      <div class="learn-empty-glyph">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
          <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>
          <circle cx="12" cy="12" r="3.2"/>
        </svg>
      </div>
      <p class="learn-empty-head">Nothing learned ${data.window === "all" ? "yet" : "this week"}.</p>
      <p class="learn-empty-sub">Correct a dictation and it shows up here, with how many similar utterances in your journal it now nudges. The Journal tab has a one-tap fix on every entry.</p>
    </div>`;
    return;
  }

  // The honest one-liner. "Now nudged" only when corrections actually route.
  let reach = "";
  if (nudged > 0) {
    const isAre = nudged === 1 ? "is" : "are";
    reach = data.enabled
      ? ` <span class="learn-reach-on">${nudged} similar ${plural(nudged, "utterance")} in your journal ${isAre} now nudged toward your fixes.</span>`
      : ` <span class="learn-reach-off">${nudged} similar ${plural(nudged, "utterance")} would be nudged once you turn corrections on.</span>`;
  }
  const sentence = `You made <strong>${made}</strong> ${plural(made, "correction")} and corrected <strong>${corrected}</strong> ${plural(corrected, "dictation")} ${windowLabel}.${reach}`;

  const stats = `
    <div class="learn-stats">
      <div class="learn-stat"><div class="learn-stat-num">${made}</div><div class="learn-stat-label">corrections made</div></div>
      <div class="learn-stat"><div class="learn-stat-num">${corrected}</div><div class="learn-stat-label">dictations corrected</div></div>
      <div class="learn-stat is-reach"><div class="learn-stat-num">${nudged}</div><div class="learn-stat-label">utterances nudged</div></div>
    </div>`;

  const blocks = Array.isArray(data.by_block) ? data.by_block : [];
  const targets = Array.isArray(data.by_target) ? data.by_target : [];
  const chip = (name, count) =>
    `<span class="learn-chip">${escapeHtml(name)}<span class="learn-chip-count">×${count}</span></span>`;
  const breakdownRows = [];
  if (blocks.length) {
    breakdownRows.push(
      `<div class="learn-break-row"><span class="learn-break-label">Routed to block</span>${blocks
        .map((b) => chip(b.block_id, b.count))
        .join("")}</div>`
    );
  }
  if (targets.length) {
    breakdownRows.push(
      `<div class="learn-break-row"><span class="learn-break-label">Target profile</span>${targets
        .map((b) => chip(b.target_profile, b.count))
        .join("")}</div>`
    );
  }
  const breakdown = breakdownRows.length
    ? `<div class="learn-breakdown">${breakdownRows.join("")}</div>`
    : "";

  const corrections = Array.isArray(data.corrections) ? data.corrections : [];
  let rows = "";
  if (corrections.length) {
    const rowHtml = corrections
      .map((c) => {
        const target = c.kind === "target";
        // Stay quiet at N=0: no reach chip when nothing is within reach yet.
        const reachChip =
          Number(c.similar) > 0
            ? `<span class="learn-reach-chip">learned from ${c.similar} similar</span>`
            : "";
        return `<div class="learn-row">
          <span class="learn-row-kind">${target ? "target" : "intent"}</span>
          <span class="learn-row-gist" title="${escapeAttr(c.gist || "")}">${escapeHtml(c.gist || "")}</span>
          <span class="learn-row-arrow">→</span>
          <span class="learn-row-value">${escapeHtml(c.value || "")}</span>
          ${reachChip}
        </div>`;
      })
      .join("");
    rows = `<p class="learn-rows-head">Each correction, and how far it reaches</p><div class="learn-rows">${rowHtml}</div>`;
  }

  host.innerHTML = `<p class="learn-sentence">${sentence}</p>${stats}${breakdown}${rows}`;
}

export async function loadMemory() {
  loadLearningDigest();
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
      const sig = learnSigChip(it.similar);
      return `<div class="mem-item ${target ? "kind-target" : "kind-intent"}">
        <div class="mem-item-body">
          <span class="mem-kind">${target ? "target → profile" : "intent → block"}</span>
          <span class="mem-gist" title="${escapeAttr(it.key || "")}">${escapeHtml(it.key || "")}</span>
        </div>
        <span class="mem-arrow">→</span>
        <span class="mem-value">${escapeHtml(it.value || "")}</span>
        ${sig}
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

export async function addCorrection(ev) {
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

export async function clearAllCorrections() {
  if (!confirm("Forget everything the copilot has learned? This can't be undone.")) return;
  try {
    await api("DELETE", "/api/dictation/corrections");
    await loadMemory();
  } catch (e) {
    document.getElementById("mem-meta-banner").textContent = e.message;
  }
}

export async function toggleCorrectionsEnabled() {
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

// HS-48-01: the learning-digest window toggle.
export function setLearnWindow(win) {
  const weekBtn = document.getElementById("learn-window-week");
  const allBtn = document.getElementById("learn-window-all");
  const isWeek = win === "week";
  weekBtn.classList.toggle("is-active", isWeek);
  allBtn.classList.toggle("is-active", !isWeek);
  weekBtn.setAttribute("aria-selected", String(isWeek));
  allBtn.setAttribute("aria-selected", String(!isWeek));
  loadLearningDigest(win);
}

registerSection("memory", loadMemory);
