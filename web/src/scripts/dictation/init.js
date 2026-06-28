// ── Init: event wiring + page-load sequence ──────────────────────────
// Runs at module evaluation (the page entry is a deferred type="module"
// script, so the DOM is parsed by the time this executes). The wiring
// order and the load sequence are behavior — preserve them.
import { state, activateSection } from "./core.js";
import { loadScope, loadStarterTemplates, newBlock } from "./blocks.js";
import { loadReadiness } from "./readiness.js";
import {
  kbAdd,
  kbReset,
  kbSave,
  kbDelete,
  createStarterKB,
  hsLoadExample,
  openHsSetup,
  closeHsSetup,
  hsCreateStarterSet,
  hsCopyAgentPrompt,
  saveHSContext,
  resetHSContext,
  applyProjectDocSuggestion,
  dismissProjectDocSuggestion,
} from "./knowledge.js";
import {
  rtState,
  renderRuntime,
  loadRuntime,
  saveRuntime,
  saveRuntimeAndTest,
  setRewritePasses,
  updateTargetDetectReveal,
} from "./runtime.js";
import {
  loadMemory,
  addCorrection,
  clearAllCorrections,
  toggleCorrectionsEnabled,
  setLearnWindow,
} from "./memory.js";
import { loadJournal, clearJournal, renderJournal } from "./journal.js";
import { runDryRun, clearDryRun } from "./dryrun.js";
import { initMic } from "./mic.js";
import {
  loadAgentContext,
  clearAgentContext,
  summarizeAgentContext,
  loadAgentHooks,
  applyProjectRootOverride,
  clearProjectRootOverride,
  loadDetectedProjectContext,
  renderRecentProjectRoots,
  useRecentProjectRoot,
} from "./agent.js";
import {
  knNudgeState,
  knNudgeDismiss,
  knNudgeDisableGlobally,
  hideKnNudge,
  maybeShowKnNudge,
} from "./discovery-nudge.js";
import { maybeShowActivityNudges, wireActivityNudgePinClear } from "./activity-nudges.js";

document.getElementById("project-root-override").value = state.projectRootOverride;
document.querySelectorAll('.scope-row button[data-scope]').forEach((b) =>
  b.addEventListener("click", () => loadScope(b.dataset.scope))
);
document.querySelectorAll('.scope-row button[data-section]').forEach((b) =>
  b.addEventListener("click", () => activateSection(b.dataset.section))
);
document.getElementById("btn-new").addEventListener("click", newBlock);
document.getElementById("kb-btn-add").addEventListener("click", kbAdd);
document.getElementById("kb-btn-starter").addEventListener("click", createStarterKB);
document.getElementById("kb-btn-save").addEventListener("click", kbSave);
document.getElementById("kb-btn-reset").addEventListener("click", kbReset);
document.getElementById("kb-btn-delete").addEventListener("click", kbDelete);
// HS-47-02: empty-state actions reuse the existing starter/add/example paths.
document.getElementById("kb-empty-starter").addEventListener("click", createStarterKB);
document.getElementById("kb-empty-add").addEventListener("click", kbAdd);
document.getElementById("hs-empty-example").addEventListener("click", hsLoadExample);
// HS-47-03: guided setup wiring.
document.getElementById("hs-empty-setup").addEventListener("click", openHsSetup);
document.getElementById("hs-setup-close").addEventListener("click", closeHsSetup);
document.getElementById("hs-setup-starter").addEventListener("click", hsCreateStarterSet);
document.getElementById("hs-setup-copy-prompt").addEventListener("click", hsCopyAgentPrompt);
// HS-47-04: discovery-nudge wiring.
document.getElementById("kn-nudge-setup").addEventListener("click", () => {
  if (knNudgeState.root) knNudgeDismiss(knNudgeState.root);  // acting on it counts.
  hideKnNudge();
  knNudgeState.pendingOpen = true;  // open the guided panel once .hs loads.
  activateSection("hs");
});
document.getElementById("kn-nudge-dismiss").addEventListener("click", () => {
  if (knNudgeState.root) knNudgeDismiss(knNudgeState.root);
  hideKnNudge();
});
document.getElementById("kn-nudge-off").addEventListener("click", () => {
  knNudgeDisableGlobally();
  hideKnNudge();
});
// Delegated jump for "Try a dry-run" / "Project Facts" links rendered into
// success messages and the guided panel.
document.addEventListener("click", (ev) => {
  const jump = ev.target.closest ? ev.target.closest("[data-section-jump]") : null;
  if (jump) activateSection(jump.dataset.sectionJump);
});
document.getElementById("hs-btn-save").addEventListener("click", saveHSContext);
document.getElementById("hs-btn-reset").addEventListener("click", resetHSContext);
document.getElementById("hs-suggestion-apply").addEventListener("click", applyProjectDocSuggestion);
document.getElementById("hs-suggestion-dismiss").addEventListener("click", dismissProjectDocSuggestion);
document.getElementById("rt-btn-save").addEventListener("click", saveRuntime);
document.getElementById("rt-btn-test").addEventListener("click", saveRuntimeAndTest);
document.getElementById("rt-btn-reset").addEventListener("click", () => rtState.last && renderRuntime(rtState.last));
document.getElementById("rt-btn-refresh").addEventListener("click", loadRuntime);
document.getElementById("rt-target-auto").addEventListener("click", () => {
  document.getElementById("rt-target-profile").value = "auto";
});
// Copilot depth controls (HS-40-03): segmented rewrite-passes + the
// reveal-on-toggle threshold.
document.querySelectorAll("#rt-rewrite-seg .seg-btn").forEach((btn) =>
  btn.addEventListener("click", () => setRewritePasses(btn.dataset.value))
);
document
  .getElementById("rt-target-detect-llm-enabled")
  .addEventListener("change", updateTargetDetectReveal);
// Memory + telemetry (HS-40-04).
document.getElementById("mem-add-form").addEventListener("submit", addCorrection);
document.getElementById("mem-btn-clear").addEventListener("click", clearAllCorrections);
document.getElementById("mem-btn-refresh").addEventListener("click", loadMemory);
document
  .getElementById("mem-corrections-enabled")
  .addEventListener("change", toggleCorrectionsEnabled);
// HS-48-01: the learning-digest window toggle.
document.getElementById("learn-window-week").addEventListener("click", () => setLearnWindow("week"));
document.getElementById("learn-window-all").addEventListener("click", () => setLearnWindow("all"));
// Journal (HS-45-02).
document.getElementById("journal-btn-refresh").addEventListener("click", loadJournal);
document.getElementById("journal-btn-clear").addEventListener("click", clearJournal);
document.getElementById("journal-search").addEventListener("input", renderJournal);
document.getElementById("journal-filter-source").addEventListener("change", renderJournal);
document.getElementById("journal-filter-warnings").addEventListener("change", renderJournal);
document.getElementById("journal-filter-corrected").addEventListener("change", renderJournal);
document.getElementById("dry-btn-run").addEventListener("click", runDryRun);
document.getElementById("dry-btn-clear").addEventListener("click", clearDryRun);
initMic();
document.getElementById("project-root-apply").addEventListener("click", applyProjectRootOverride);
document.getElementById("project-root-clear").addEventListener("click", clearProjectRootOverride);
document.getElementById("project-root-recent").addEventListener("change", useRecentProjectRoot);
document.getElementById("agent-context-clear").addEventListener("click", clearAgentContext);
document.getElementById("agent-summary-run").addEventListener("click", summarizeAgentContext);
document.getElementById("agent-summary-refresh").addEventListener("click", loadAgentContext);
document.getElementById("hooks-btn-refresh").addEventListener("click", loadAgentHooks);
document.getElementById("hooks-capture-messages").addEventListener("change", loadAgentHooks);
document.getElementById("ready-btn-refresh").addEventListener("click", loadReadiness);
renderRecentProjectRoots();
loadDetectedProjectContext();
loadAgentContext();
loadStarterTemplates();
loadScope("global");
maybeShowKnNudge();  // HS-47-04: evaluate the discovery nudge on load.
// HS-53-04: wire the pin-clear button and load the activity nudges.
wireActivityNudgePinClear();
maybeShowActivityNudges();
window.setInterval(loadAgentContext, 10000);
