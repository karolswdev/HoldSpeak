// ── HS-53-04: Activity Pre-Briefing nudges ──────────────────────────
// Render the source-cited nudges from `/api/activity/nudges` as quiet,
// dismissible cards above the cockpit. Two actions per card:
//   * "Dictate with this" — pins the selected ActivityRecord id in
//     localStorage so the dictation pipeline includes it as context
//     (HS-53-03 wired the override on the server). A visible pin
//     confirms what the next dictation will carry, with a "Clear".
//   * "Dismiss"           — POST /api/activity/nudges/{key}/dismiss,
//     remove the card; dismissal persists server-side (the engine
//     drops dismissed keys on the next GET).
// role="note" / role="region" — never steals focus.
import { api } from "./core.js";

const AN_PIN_KEY = "holdspeak.activityNudgePin";

function anSavePin(payload) {
  try {
    if (payload) {
      localStorage.setItem(AN_PIN_KEY, JSON.stringify(payload));
    } else {
      localStorage.removeItem(AN_PIN_KEY);
    }
  } catch (e) { /* ignore quota / disabled storage */ }
}

function anReadPin() {
  try {
    const raw = localStorage.getItem(AN_PIN_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) { return null; }
}

function anEntityLabel(citation) {
  if (!citation) return "this page";
  if (citation.entity_type && citation.entity_id) {
    return `${citation.entity_type} ${citation.entity_id}`;
  }
  return citation.title || citation.url || "this page";
}

function anLastSeenLabel(citation) {
  if (!citation || !citation.last_seen_at) return "recently";
  const parsed = new Date(citation.last_seen_at);
  if (Number.isNaN(parsed.getTime())) return "recently";
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function anRenderPin() {
  const pinHost = document.getElementById("activity-nudges-pin");
  const entityEl = document.getElementById("activity-nudges-pin-entity");
  if (!pinHost || !entityEl) return;
  const pin = anReadPin();
  if (!pin) {
    pinHost.hidden = true;
    entityEl.textContent = "";
    return;
  }
  entityEl.textContent = pin.entity_label || "this page";
  pinHost.hidden = false;
}

// SVG glyph paths (Lucide-style strokes) — kept inline so JS-injected DOM
// doesn't need a sprite or a fetch. Stroke="currentColor" so the CSS owns
// the tint.
const AN_SVG = {
  window: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">'
    + '<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    + ' d="M12 8v4l3 2M21 12a9 9 0 1 1-3-6.7"/></svg>',
  record: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">'
    + '<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    + ' d="M6 4h12v17l-6-4-6 4V4z"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">'
    + '<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    + ' d="M5 12h14M13 6l6 6-6 6"/></svg>',
  source: '<svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true">'
    + '<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    + ' d="M4 12c4-7 12-7 16 0M4 12c4 7 12 7 16 0M12 5v14"/></svg>',
  clock: '<svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true">'
    + '<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    + ' d="M12 7v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>',
  entity: '<svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true">'
    + '<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    + ' d="M9 12l2 2 4-4M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>',
};

function anChip({ className, glyph, label, value }) {
  const chip = document.createElement("span");
  chip.className = `an-chip ${className || ""}`.trim();
  if (glyph) {
    const g = document.createElement("span");
    g.setAttribute("aria-hidden", "true");
    g.innerHTML = glyph;
    chip.appendChild(g.firstChild);
  }
  if (label) {
    chip.appendChild(document.createTextNode(label + " "));
  }
  if (value) {
    const strong = document.createElement("strong");
    strong.textContent = value;
    chip.appendChild(strong);
  }
  return chip;
}

function anSourceLabel(citation) {
  const browser = citation.source_browser || "browser";
  return citation.source_profile ? `${browser}/${citation.source_profile}` : browser;
}

function anRenderCards(nudges) {
  const list = document.getElementById("activity-nudges-list");
  const shell = document.getElementById("activity-nudges");
  if (!list || !shell) return;
  list.innerHTML = "";
  if (!nudges || nudges.length === 0) {
    shell.hidden = anReadPin() == null;
    return;
  }
  shell.hidden = false;
  for (const nudge of nudges) {
    const card = document.createElement("article");
    card.className = "activity-nudge";
    card.dataset.kind = nudge.kind || "record";
    card.dataset.key = nudge.key;
    card.setAttribute("role", "note");
    card.setAttribute("aria-label", nudge.title || "Activity nudge");

    // Glyph — Lucide-style SVG, kind-aware.
    const glyph = document.createElement("div");
    glyph.className = "activity-nudge-glyph";
    glyph.setAttribute("aria-hidden", "true");
    glyph.innerHTML = nudge.kind === "window" ? AN_SVG.window : AN_SVG.record;
    card.appendChild(glyph);

    // Body — display-font title, summary, then a row of citation chips
    // (or a stat strip for the windowed summary).
    const body = document.createElement("div");
    body.className = "activity-nudge-body";

    const headline = document.createElement("div");
    headline.className = "activity-nudge-headline";
    const title = document.createElement("h3");
    title.className = "activity-nudge-title";
    title.textContent = nudge.title || "Activity nudge";
    headline.appendChild(title);
    body.appendChild(headline);

    if (nudge.body) {
      const summary = document.createElement("p");
      summary.className = "activity-nudge-summary";
      summary.textContent = nudge.body;
      body.appendChild(summary);
    }

    const citation = (nudge.citations && nudge.citations[0]) || null;
    if (nudge.kind === "window" && Array.isArray(nudge.citations)) {
      // Stat strip: total + the top entity/source mix, derived from window_record_count.
      const stats = document.createElement("div");
      stats.className = "activity-nudge-stats";
      const total = document.createElement("span");
      total.className = "an-stat";
      const num = document.createElement("span");
      num.className = "an-stat-num";
      num.textContent = String(nudge.window_record_count || nudge.citations.length);
      const label = document.createElement("span");
      label.className = "an-stat-label";
      label.textContent = "records";
      total.appendChild(num);
      total.appendChild(label);
      stats.appendChild(total);
      // One source chip per distinct browser among the citations.
      const seenSources = new Set();
      for (const c of nudge.citations) {
        const src = anSourceLabel(c);
        if (seenSources.has(src)) continue;
        seenSources.add(src);
        stats.appendChild(anChip({ glyph: AN_SVG.source, value: src }));
      }
      body.appendChild(stats);
    } else if (citation) {
      const chips = document.createElement("div");
      chips.className = "activity-nudge-cite";
      chips.appendChild(anChip({
        className: "an-chip-entity",
        glyph: AN_SVG.entity,
        value: anEntityLabel(citation),
      }));
      chips.appendChild(anChip({ glyph: AN_SVG.source, value: anSourceLabel(citation) }));
      chips.appendChild(anChip({ glyph: AN_SVG.clock, value: `last on ${anLastSeenLabel(citation)}` }));
      body.appendChild(chips);
    }
    card.appendChild(body);

    // Actions — primary CTA on record cards, ghost dismiss on every card.
    const actions = document.createElement("div");
    actions.className = "activity-nudge-actions";
    if (nudge.kind === "record" && citation && citation.record_id) {
      const dictate = document.createElement("button");
      dictate.className = "an-btn an-btn-primary";
      dictate.type = "button";
      dictate.innerHTML = `${AN_SVG.arrow}<span>Dictate with this</span>`;
      dictate.addEventListener("click", async () => {
        anSavePin({
          record_id: citation.record_id,
          entity_label: anEntityLabel(citation),
        });
        anRenderPin();
        // HS-53-07: park the selection server-side so the next dictation folds
        // this record into its rewrite. The localStorage pin is the visible
        // affordance; this POST is what actually closes the loop.
        try {
          await api("POST", "/api/activity/nudges/select", {
            record_id: citation.record_id,
          });
        } catch (e) { /* the pin still shows; the server simply has no selection */ }
      });
      actions.appendChild(dictate);
    }
    const dismiss = document.createElement("button");
    dismiss.className = "an-btn an-btn-ghost";
    dismiss.type = "button";
    dismiss.textContent = "Dismiss";
    dismiss.addEventListener("click", async () => {
      try {
        await api("POST", `/api/activity/nudges/${encodeURIComponent(nudge.key)}/dismiss`);
      } catch (e) { /* swallow — the GET will re-evaluate */ }
      card.remove();
      if (!list.querySelector(".activity-nudge")) {
        shell.hidden = anReadPin() == null;
      }
    });
    actions.appendChild(dismiss);
    card.appendChild(actions);

    list.appendChild(card);
  }
}

export async function maybeShowActivityNudges() {
  anRenderPin();
  let payload;
  try {
    payload = await api("GET", "/api/activity/nudges");
  } catch (e) { return; }
  if (!payload || payload.activity_enabled === false) {
    anRenderCards([]);
    return;
  }
  anRenderCards(payload.nudges || []);
}

// HS-53-04: wire the pin-clear button (called once from init).
export function wireActivityNudgePinClear() {
  document.getElementById("activity-nudges-pin-clear").addEventListener("click", async () => {
    anSavePin(null);
    anRenderPin();
    // HS-53-07: drop the server-side selection too, so Clear actually un-arms the
    // next dictation (not just the visible pin).
    try {
      await api("POST", "/api/activity/nudges/select/clear");
    } catch (e) { /* the visible pin is already cleared */ }
    // If there are no visible cards either, hide the whole shell again.
    const list = document.getElementById("activity-nudges-list");
    const shell = document.getElementById("activity-nudges");
    if (shell && list && !list.querySelector(".activity-nudge")) shell.hidden = true;
  });
}
