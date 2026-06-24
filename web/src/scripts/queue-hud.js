// HS-69-07: the app-wide Queue HUD — store + render.
//
// A Dynamic-Island-style collapsed pill under the nav that expands into a live
// per-job ledger, present on EVERY page (the iPad `QueueHUD` mounted at app
// root, MeetingCaptureApp.swift:36; web-technical-design §2). It is the web's
// missing `RunQueueStore` + the floating shell, fed by the shared `runtime-bus`
// — no backend message-type change.
//
// Framework-free (the shell must work with or without Alpine). The markup +
// CSS live in `QueueHud.astro`; this module owns the tiny reactive store and
// the DOM render.
//
// ── How jobs are DERIVED (honest mapping) ────────────────────────────────
// The web has no `runtime_queue` feed, so jobs are synthesized from the frames
// that already flow (web-technical-design §2 "derive-first, no backend change"):
//
//   • `intel_status` → the meeting-intelligence job (a single job id "intel").
//       state: live|running → working · queued → queued · ready → done ·
//       error → failed · disabled → (no job). `detail` becomes the note;
//       `egress` (when present) the target chip.
//   • `runtime_activity` → the runtime/dictation job (a single job id "runtime").
//       state: listening|recording|transcribing|processing|typing|saving →
//       working · error → blocked · idle|complete → done (and a done job is
//       auto-pruned after a short settle so the pill returns to idle).
//
// HONEST GAPS (described, not faked):
//   • TRUE PROGRESS (0..1) is not in any frame. `intel_token` frames are a
//     heartbeat only, so the working job shows an INDETERMINATE shimmer bar,
//     not a real percentage. A real per-job progress would need the additive
//     `runtime_queue` backend frame (noted, not built).
//   • Only TWO concurrent jobs are derivable (one intel, one runtime) — the
//     coarse frames carry no per-workflow job array. The store is keyed by id
//     so a richer feed slots in without a rewrite.
//   • `blocked` (the iPad's endpoint-down-auto-resume state) has no clean
//     source today; an errored runtime maps to `blocked` as the closest honest
//     reading, and intel `error` maps to `failed`. There is no auto-resume
//     signal to surface, so no resume footnote is fabricated.

import { subscribe, seedState } from "./runtime-bus.js";

// Status vocabulary → web-wins palette + glyph (web-technical-design §2;
// tokens are the CANONICAL web status colors per the web-wins decision).
const STATUS = {
  working: { label: "Working", rank: 0, glyph: "bolt" },
  blocked: { label: "Blocked", rank: 1, glyph: "pause" },
  queued: { label: "Queued", rank: 2, glyph: "hourglass" },
  done: { label: "Done", rank: 3, glyph: "check" },
  failed: { label: "Failed", rank: 4, glyph: "octagon" },
};

const GLYPH_PATHS = {
  bolt: "M13 2L4.5 13H11l-1 9 8.5-11H12l1-9z",
  pause: "M8 5v14M16 5v14",
  hourglass: "M6 3h12M6 21h12M7 3c0 4 3 5 5 7 2-2 5-3 5-7M7 21c0-4 3-5 5-7 2 2 5 3 5 7",
  check: "M5 13l4 4L19 7",
  octagon: "M8 2h8l6 6v8l-6 6H8l-6-6V8z M12 8v4 M12 16h.01",
};

const ACTIVE_RUNTIME = new Set([
  "listening",
  "recording",
  "transcribing",
  "processing",
  "typing",
  "saving",
  "meeting_live",
]);

// ── the store ────────────────────────────────────────────────────────────
const jobs = new Map(); // id -> { id, label, target, status, note, indeterminate }
let pruneTimers = new Map();

function rankedJobs() {
  return [...jobs.values()].sort((a, b) => STATUS[a.status].rank - STATUS[b.status].rank);
}

function countByStatus(status) {
  let n = 0;
  for (const j of jobs.values()) if (j.status === status) n++;
  return n;
}

// A done/failed job lingers briefly (so the user sees the resolution) then is
// pruned, returning the pill to its quiet idle state.
function schedulePrune(id, ms) {
  if (pruneTimers.has(id)) window.clearTimeout(pruneTimers.get(id));
  pruneTimers.set(
    id,
    window.setTimeout(() => {
      jobs.delete(id);
      pruneTimers.delete(id);
      render();
    }, ms),
  );
}

function clearPrune(id) {
  if (pruneTimers.has(id)) {
    window.clearTimeout(pruneTimers.get(id));
    pruneTimers.delete(id);
  }
}

function upsert(id, patch) {
  const prev = jobs.get(id) || { id };
  jobs.set(id, { ...prev, ...patch });
}

// intel_status → the "intel" job.
function fromIntelStatus(data) {
  const state = String(data?.state || "").toLowerCase();
  const detail = String(data?.detail || "").trim();
  const target = egressTarget(data?.egress);
  const id = "intel";
  if (state === "disabled" || !state) {
    jobs.delete(id);
    clearPrune(id);
    return;
  }
  let status = null;
  if (state === "live" || state === "running") status = "working";
  else if (state === "queued") status = "queued";
  else if (state === "ready") status = "done";
  else if (state === "error") status = "failed";
  if (!status) return;

  clearPrune(id);
  upsert(id, {
    id,
    label: "Meeting intelligence",
    target: target || (status === "working" ? "Processing" : undefined),
    status,
    note: detail || undefined,
    indeterminate: status === "working",
  });
  if (status === "done") schedulePrune(id, 4000);
  if (status === "failed") schedulePrune(id, 8000);
}

// runtime_activity → the "runtime" job.
const RUNTIME_LABELS = {
  listening: "Listening",
  recording: "Recording",
  transcribing: "Transcribing",
  processing: "Processing",
  typing: "Typing",
  saving: "Saving",
  meeting_live: "Meeting live",
};
function fromRuntimeActivity(data) {
  const state = String(data?.state || "idle").toLowerCase();
  const id = "runtime";
  if (state === "idle") {
    // returned to rest — let any lingering "done" remain, but a bare idle prunes.
    if (jobs.has(id) && jobs.get(id).status !== "done") {
      jobs.delete(id);
      clearPrune(id);
    }
    return;
  }
  if (state === "complete") {
    clearPrune(id);
    upsert(id, { id, label: "Dictation", status: "done", note: undefined, indeterminate: false });
    schedulePrune(id, 3000);
    return;
  }
  if (state === "error") {
    clearPrune(id);
    upsert(id, {
      id,
      label: "Dictation",
      status: "blocked",
      note: String(data?.last_error || data?.detail || "Needs attention").trim() || undefined,
      indeterminate: false,
    });
    return;
  }
  if (ACTIVE_RUNTIME.has(state)) {
    clearPrune(id);
    upsert(id, {
      id,
      label: RUNTIME_LABELS[state] || "Runtime",
      target: String(data?.source || "").trim() || undefined,
      status: "working",
      note: undefined,
      indeterminate: true,
    });
  }
}

function egressTarget(egress) {
  if (!egress || typeof egress !== "object") return undefined;
  if (egress.can_transmit_offmachine && egress.provider) {
    const p = String(egress.provider).toLowerCase();
    return p === "auto" ? "Endpoint" : "Cloud";
  }
  if (egress.enabled === false) return undefined;
  return "On-device";
}

// ── render ───────────────────────────────────────────────────────────────
let els = null;
let expanded = false;

function ensureEls() {
  if (els) return els;
  const root = document.querySelector("[data-queue-hud]");
  if (!root) return null;
  els = {
    root,
    pill: root.querySelector("[data-qh-pill]"),
    summary: root.querySelector("[data-qh-summary]"),
    beacon: root.querySelector("[data-qh-beacon]"),
    blockedChip: root.querySelector("[data-qh-blocked]"),
    panel: root.querySelector("[data-qh-panel]"),
    ledger: root.querySelector("[data-qh-ledger]"),
  };
  els.pill.addEventListener("click", () => {
    expanded = !expanded;
    render();
  });
  return els;
}

function svgGlyph(name, cls) {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "2");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  if (cls) svg.setAttribute("class", cls);
  const path = document.createElementNS(ns, "path");
  path.setAttribute("d", GLYPH_PATHS[name] || "");
  svg.appendChild(path);
  return svg;
}

function mostUrgentStatus() {
  // working > blocked > failed > queued for the beacon color.
  if (countByStatus("working")) return "working";
  if (countByStatus("blocked")) return "blocked";
  if (countByStatus("failed")) return "failed";
  if (countByStatus("queued")) return "queued";
  return null;
}

function summaryText() {
  const parts = [];
  const w = countByStatus("working");
  const q = countByStatus("queued");
  const b = countByStatus("blocked");
  if (w) parts.push(`${w} working`);
  if (q) parts.push(`${q} queued`);
  if (b) parts.push(`${b} blocked`);
  return parts.join(" · ");
}

function render() {
  const e = ensureEls();
  if (!e) return;

  const hasAny = jobs.size > 0;

  // Idle + empty → the pill is hidden entirely (unobtrusive when nothing runs).
  if (!hasAny) {
    e.root.hidden = true;
    expanded = false;
    e.pill.setAttribute("aria-expanded", "false");
    return;
  }
  e.root.hidden = false;

  // ── collapsed pill ──
  const urgent = mostUrgentStatus();
  e.beacon.className = "qh-beacon" + (urgent ? ` is-${urgent}` : "");
  if (urgent === "working" || urgent === "blocked") e.beacon.classList.add("is-live");
  e.summary.textContent = summaryText() || `${jobs.size} done`;

  const blocked = countByStatus("blocked") + countByStatus("failed");
  if (blocked > 0) {
    e.blockedChip.hidden = false;
    e.blockedChip.textContent = String(blocked);
  } else {
    e.blockedChip.hidden = true;
  }

  e.pill.setAttribute("aria-expanded", expanded ? "true" : "false");
  e.panel.hidden = !expanded;

  if (!expanded) return;

  // ── expanded ledger ──
  e.ledger.textContent = "";
  let i = 0;
  for (const job of rankedJobs()) {
    const meta = STATUS[job.status];
    const row = document.createElement("div");
    row.className = `qh-row signal-card is-${job.status} hs-materialize`;
    row.style.setProperty("--i", String(i++));

    const orb = document.createElement("span");
    orb.className = `qh-orb is-${job.status}`;
    if (job.status === "working" || job.status === "blocked") orb.classList.add("is-live");
    orb.appendChild(svgGlyph(meta.glyph));

    const body = document.createElement("div");
    body.className = "qh-body";

    const top = document.createElement("div");
    top.className = "qh-row-top";
    const label = document.createElement("span");
    label.className = "qh-label";
    label.textContent = job.label;
    const chip = document.createElement("span");
    chip.className = `qh-status-chip is-${job.status}`;
    chip.textContent = meta.label;
    top.append(label, chip);

    const bar = document.createElement("div");
    bar.className = "qh-bar";
    const fill = document.createElement("div");
    fill.className =
      "qh-bar-fill" + (job.indeterminate ? " is-indeterminate" : "") + ` is-${job.status}`;
    if (!job.indeterminate) {
      fill.style.width =
        job.status === "done" ? "100%" : job.status === "queued" ? "8%" : "100%";
    }
    bar.appendChild(fill);

    const foot = document.createElement("div");
    foot.className = "qh-row-foot";
    if (job.target) {
      const t = document.createElement("span");
      t.className = "qh-target";
      t.textContent = job.target;
      foot.appendChild(t);
    }
    if (job.note) {
      const n = document.createElement("span");
      n.className = "qh-note";
      n.textContent = job.note;
      foot.appendChild(n);
    }

    body.append(top, bar);
    if (foot.childElementCount) body.appendChild(foot);
    row.append(orb, body);
    e.ledger.appendChild(row);
  }
}

// ── boot ─────────────────────────────────────────────────────────────────
export function mountQueueHud() {
  if (!document.querySelector("[data-queue-hud]")) return;
  ensureEls();
  subscribe("intel_status", (data) => {
    fromIntelStatus(data);
    render();
  });
  subscribe("runtime_activity", (data) => {
    fromRuntimeActivity(data);
    render();
  });
  // intel_token is a heartbeat that keeps the working job's shimmer alive — the
  // store already shows indeterminate; no per-token state is fabricated.
  subscribe("intel_complete", (data) => {
    fromIntelStatus({ state: "ready", detail: (data && data.detail) || "" });
    render();
  });
  seedState().then(() => render());
  render();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", mountQueueHud);
} else {
  mountQueueHud();
}
