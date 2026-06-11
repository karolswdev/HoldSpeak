// ── HS-47-04: discovery nudge ────────────────────────────────────────
// Ambient, dismissible, focus-safe. Shows only when a detected project has no
// knowledge (no facts, no .hs/), is not dismissed for this project, and the
// global switch is on. Dismissal is durable (localStorage). Reuses the existing
// readiness signal; adds no detection path.
import { api, projectRootParam } from "./core.js";

const KN_NUDGE_DISABLED_KEY = "holdspeak.knNudgeDisabled";
const KN_NUDGE_DISMISSED_KEY = "holdspeak.knNudgeDismissed";

export const knNudgeState = { root: null, pendingOpen: false };

function knNudgeGloballyOff() {
  try { return localStorage.getItem(KN_NUDGE_DISABLED_KEY) === "1"; } catch (e) { return false; }
}
function knNudgeDismissedRoots() {
  try { return JSON.parse(localStorage.getItem(KN_NUDGE_DISMISSED_KEY) || "{}") || {}; } catch (e) { return {}; }
}
function knNudgeIsDismissed(root) {
  return !!(root && knNudgeDismissedRoots()[root]);
}
export function knNudgeDismiss(root) {
  if (!root) return;
  try {
    const map = knNudgeDismissedRoots();
    map[root] = true;
    localStorage.setItem(KN_NUDGE_DISMISSED_KEY, JSON.stringify(map));
  } catch (e) { /* ignore quota / disabled storage */ }
}
export function knNudgeDisableGlobally() {
  try { localStorage.setItem(KN_NUDGE_DISABLED_KEY, "1"); } catch (e) { /* ignore */ }
}
export function hideKnNudge() {
  const el = document.getElementById("kn-nudge");
  if (el) el.hidden = true;
}

export async function maybeShowKnNudge() {
  const el = document.getElementById("kn-nudge");
  if (!el) return;
  el.hidden = true;  // re-evaluate cleanly every time.
  if (knNudgeGloballyOff()) return;
  let data;
  try {
    data = await api("GET", `/api/dictation/readiness${projectRootParam("?")}`);
  } catch (e) {
    return;  // no project / error -> no nudge.
  }
  const project = data && data.project;
  if (!project || !project.root) return;
  const hasFacts = !!(data.project_kb && data.project_kb.exists);
  const hasContext = !!(data.project_context && data.project_context.exists);
  if (hasFacts || hasContext) return;            // already has knowledge.
  if (knNudgeIsDismissed(project.root)) return;  // dismissed for this project.
  knNudgeState.root = project.root;
  const label = document.getElementById("kn-nudge-project");
  if (label) label.textContent = project.name ? `"${project.name}" has none yet.` : "";
  el.hidden = false;
}
