// The Cadence coach (CAD-2-04). Reads /api/cadence/* and renders the open loops
// with their prepared next action, evidence deep-links, and an egress badge.
//
// SECURITY: loop titles/bodies derive from meeting transcripts (untrusted), so every
// piece of source text is written with textContent — never innerHTML. Source text is
// data, never markup (the cadence prompt-injection rule).
import { renderEgressBadge } from "./egress-badge.js";

const API = "/api/cadence";

async function jget(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}
async function jpost(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : "{}",
  });
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

function egressChip(badge) {
  const chip = el("span", "egress-badge");
  renderEgressBadge(chip, badge || { scope: "local", label: "Local only" });
  return chip;
}

function loopCard(loop) {
  const card = el("article", "cad-card");
  card.dataset.loopId = loop.id;
  if (loop.needs_review) card.classList.add("is-review");

  const head = el("div", "cad-card-head");
  head.appendChild(el("span", "cad-score", loop.stale_score.toFixed(0)));
  const titleWrap = el("div", "cad-title-wrap");
  titleWrap.appendChild(el("h3", "cad-title", loop.title));
  const meta = el("div", "cad-meta");
  meta.appendChild(el("span", "cad-badge", loop.source_type.replace("_", " ")));
  if (loop.owner) meta.appendChild(el("span", "cad-owner", loop.owner));
  if (loop.needs_review) meta.appendChild(el("span", "cad-review", "needs review"));
  titleWrap.appendChild(meta);
  head.appendChild(titleWrap);
  head.appendChild(egressChip(loop.egress));
  card.appendChild(head);

  // The prepared next move — the whole point: the next decision is cheap.
  if (loop.next_action) {
    const na = el("div", "cad-next");
    na.appendChild(el("div", "cad-next-label", "Prepared next move"));
    na.appendChild(el("div", "cad-next-title", loop.next_action.title));
    if (loop.next_action.body_markdown) {
      na.appendChild(el("pre", "cad-next-body", loop.next_action.body_markdown));
    }
    card.appendChild(na);
  }

  // Evidence — why this loop exists, with deep links.
  if (loop.evidence && loop.evidence.length) {
    const ev = el("div", "cad-evidence");
    ev.appendChild(el("span", "cad-evidence-label", "Evidence"));
    loop.evidence.forEach((e) => {
      if (e.deep_link) {
        const a = el("a", "cad-evidence-link", e.label || e.kind);
        a.href = e.deep_link;
        ev.appendChild(a);
      } else {
        ev.appendChild(el("span", "cad-evidence-link", e.label || e.kind));
      }
    });
    card.appendChild(ev);
  }

  // An awaiting coding agent gets a reply composer — type and Send delivers the reply
  // into its terminal pane (CAD-3-04). Never autonomous: nothing is sent until you click.
  if (loop.source_type === "agent_question") {
    const composer = el("div", "cad-reply");
    const ta = el("textarea", "cad-reply-input");
    ta.placeholder = "Type your reply to the agent…";
    ta.rows = 2;
    const send = el("button", "cad-btn cad-btn-send", "Send reply");
    send.dataset.act = "reply";
    composer.append(ta, send);
    card.appendChild(composer);
  }

  // One-tap decisions.
  const actions = el("div", "cad-actions");
  const snooze = el("button", "cad-btn", "Snooze 1d");
  snooze.dataset.act = "snooze";
  const close = el("button", "cad-btn", "Mark done");
  close.dataset.act = "close";
  const kill = el("button", "cad-btn cad-btn-danger", "Kill loop");
  kill.dataset.act = "kill";
  actions.append(snooze, close, kill);
  card.appendChild(actions);

  return card;
}

function emptyState(msg) {
  return el("p", "cad-empty", msg);
}

async function refresh() {
  const [status, loopsResp] = await Promise.all([
    jget(`${API}/status`),
    jget(`${API}/loops`),
  ]);
  const loops = loopsResp.loops || [];

  // Policy summary.
  const pol = document.getElementById("cad-policy");
  if (pol) {
    pol.textContent = "";
    const q = status.quiet_hours;
    const line = `${status.enabled ? "On" : "Off"} · ${status.pressure} · ` +
      `quiet ${String(q.start).padStart(2, "0")}:00–${String(q.end).padStart(2, "0")}:00 · ` +
      `max ${status.max_nudges_per_day}/day`;
    pol.appendChild(el("span", null, line));
  }

  // "Now": the highest-staleness pushable loops (not needs_review).
  const now = document.getElementById("cad-now");
  const later = document.getElementById("cad-loops");
  if (now) now.textContent = "";
  if (later) later.textContent = "";

  const pushable = loops.filter((l) => !l.needs_review);
  const top = pushable.slice(0, 3);
  const rest = loops.filter((l) => !top.includes(l));

  if (now) {
    if (top.length) top.forEach((l) => now.appendChild(loopCard(l)));
    else now.appendChild(emptyState("Nothing pressing. Run a tick to refresh from your meetings."));
  }
  if (later) {
    if (rest.length) rest.forEach((l) => later.appendChild(loopCard(l)));
    else later.appendChild(emptyState("No other open loops."));
  }
}

function recCard(rec) {
  const card = loopCard(rec.loop);
  if (rec.severity === "escalated") card.classList.add("cad-sev-escalated");
  else if (rec.severity === "persistent") card.classList.add("cad-sev-persistent");
  // surface the recommended action as a badge in the head
  const head = card.querySelector(".cad-card-head");
  if (head) {
    const badge = el("span", "cad-rec-action", rec.action);
    badge.title = rec.reason;
    head.insertBefore(badge, head.querySelector(".egress-badge"));
  }
  return card;
}

async function loadCloseout() {
  const co = await jget(`${API}/closeout`);
  const host = document.getElementById("cad-closeout");
  if (!host) return;
  host.textContent = "";
  if (!co.recs || !co.recs.length) {
    host.appendChild(emptyState("Your loops are clear. Nice."));
    return;
  }
  co.recs.forEach((rec) => host.appendChild(recCard(rec)));
}

async function loadHistory() {
  const data = await jget(`${API}/history?limit=20`);
  const host = document.getElementById("cad-history");
  if (!host) return;
  host.textContent = "";
  const nudges = data.nudges || [];
  if (!nudges.length) {
    host.appendChild(emptyState("No nudges yet."));
    return;
  }
  nudges.forEach((n) => {
    const row = el("div", "cad-history-row");
    row.appendChild(el("span", "cad-history-surface", n.surface));
    row.appendChild(el("span", null, n.title || n.status));
    host.appendChild(row);
  });
}

async function onAction(loopId, act, card) {
  if (act === "snooze") await jpost(`${API}/loops/${loopId}/snooze`, { hours: 24 });
  else if (act === "close") await jpost(`${API}/loops/${loopId}/close`);
  else if (act === "kill") await jpost(`${API}/loops/${loopId}/kill`);
  else if (act === "reply") {
    const ta = card && card.querySelector(".cad-reply-input");
    const text = ta ? ta.value.trim() : "";
    if (!text) return;
    await jpost(`${API}/loops/${loopId}/reply`, { text });
  }
  await refresh();
}

export function initCadence() {
  const runBtn = document.getElementById("cad-run-now");
  if (runBtn) {
    runBtn.addEventListener("click", async () => {
      runBtn.disabled = true;
      runBtn.textContent = "Running…";
      try {
        await jpost(`${API}/run-now`);
        await refresh();
      } finally {
        runBtn.disabled = false;
        runBtn.textContent = "Run now";
      }
    });
  }
  const closeoutBtn = document.getElementById("cad-closeout-btn");
  if (closeoutBtn) {
    closeoutBtn.addEventListener("click", () => loadCloseout().catch((e) => console.error(e)));
  }
  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-act]");
    if (!btn) return;
    const card = btn.closest("[data-loop-id]");
    if (!card) return;
    onAction(card.dataset.loopId, btn.dataset.act, card)
      .then(() => loadHistory().catch(() => {}))
      .catch((e) => console.error(e));
  });
  refresh().catch((e) => console.error(e));
  loadHistory().catch((e) => console.error(e));
}
