// ── Readiness snapshot: the cockpit's health cards + next actions ────
import {
  api,
  escapeHtml,
  escapeAttr,
  projectRootParam,
  activateSection,
  registerSection,
  renderRuntimeGuidance,
  wireCopyCommandButtons,
} from "./core.js";
import { createFromTemplate } from "./blocks.js";
import { createStarterKB } from "./knowledge.js";
import { enablePipelineFromReadiness } from "./runtime.js";

export async function loadReadiness() {
  const meta = document.getElementById("ready-meta");
  const cards = document.getElementById("ready-cards");
  const actions = document.getElementById("ready-actions");
  meta.classList.remove("warn", "error");
  meta.textContent = "Loading…";
  cards.innerHTML = "";
  actions.innerHTML = "";
  try {
    const data = await api("GET", `/api/dictation/readiness${projectRootParam("?")}`);
    renderReadiness(data);
  } catch (e) {
    meta.classList.add("error");
    meta.textContent = e.message;
  }
}

function renderReadiness(data) {
  const meta = document.getElementById("ready-meta");
  meta.classList.remove("warn", "error");
  if (!data.ready) meta.classList.add("warn");
  const project = data.project
    ? `${escapeHtml(data.project.name)} (${escapeHtml(data.project.anchor)} @ ${escapeHtml(data.project.root)})`
    : "(none selected)";
  meta.innerHTML =
    `status: <strong>${data.ready ? "ready" : "needs attention"}</strong>` +
    `  ·  project: <strong>${project}</strong>`;

  const blocks = data.blocks || {};
  const kb = data.project_kb || {};
  const runtime = data.runtime || {};
  const telemetry = data.telemetry || runtime.telemetry || {};
  const telemetryCounters = telemetry.counters || runtime.counters || {};
  const telemetryLatency = telemetry.latency || {};
  const telemetryFallbacks = telemetry.fallbacks || [];
  const target = data.target || {};
  const agentHooks = data.agent_hooks || {};
  const freshHooks = Object.entries(agentHooks)
    .filter(([_agent, entry]) => entry && entry.fresh)
    .map(([agent]) => agent);
  const config = data.config || {};
  document.getElementById("ready-cards").innerHTML = [
    readinessCard(
      "Pipeline",
      config.pipeline_enabled ? "enabled" : "disabled",
      config.pipeline_enabled ? "ok" : "warn",
      `${config.max_total_latency_ms || "?"} ms target`
    ),
    readinessCard(
      "Target",
      target.label || "Unknown",
      target.id && target.id !== "unknown" ? "ok" : "warn",
      `${target.source || "none"} · ${Math.round(Number(target.confidence || 0) * 100)}% confidence`
    ),
    readinessCard(
      "Blocks",
      `${blocks.resolved?.count ?? 0} loaded`,
      (blocks.resolved?.valid && (blocks.resolved?.count || 0) > 0) ? "ok" : "warn",
      `${blocks.resolved_scope || "global"} · ${blocks.resolved?.path || "no file"}`
    ),
    readinessCard(
      "Project Facts",
      kb.exists ? `${(kb.keys || []).length} keys` : "missing",
      kb.valid && kb.exists ? "ok" : "warn",
      kb.path || "no project"
    ),
    readinessCard(
      "Runtime",
      runtime.status || "unknown",
      runtime.status === "available" ? "ok" : (runtime.status === "disabled" ? "warn" : "error"),
      runtime.resolved_backend || runtime.requested_backend || "not resolved"
    ),
    readinessCard(
      "Telemetry",
      telemetryFallbacks.length ? `${telemetryFallbacks.length} fallback` : `${telemetryCounters.classify_calls ?? 0} classify calls`,
      telemetryFallbacks.length ? "warn" : "ok",
      `budget ${telemetryLatency.max_total_latency_ms || config.max_total_latency_ms || "?"} ms · successes ${telemetryCounters.classify_successes ?? 0}`
    ),
    readinessCard(
      "Agent hooks",
      freshHooks.length ? `${freshHooks.join(" + ")} fresh` : "no recent hooks",
      freshHooks.length ? "ok" : "warn",
      "Claude/Codex hook context freshness"
    ),
  ].join("");

  const warnings = data.warnings || [];
  const actions = document.getElementById("ready-actions");
  if (!warnings.length) {
    actions.innerHTML = `<div class="ok-box">Ready for dry-run and live dictation.</div>`;
    return;
  }
  actions.innerHTML = warnings.map((w) => `
    <div class="${w.section === "runtime" && w.code !== "pipeline_disabled" ? "error-box" : "meta-banner warn"}">
      <strong>${escapeHtml(w.message)}</strong><br />
      <span>${escapeHtml(w.action || "")}</span>
      ${w.section && w.section !== "readiness" ? `<button class="btn" data-ready-section="${escapeAttr(w.section)}" style="float:right;">Open</button>` : ""}
      ${w.template_id ? `<button class="btn primary" data-ready-template-id="${escapeAttr(w.template_id)}" data-ready-template-scope="${escapeAttr(w.template_scope || "global")}" style="float:right;margin-right:8px;">Create + dry-run</button>` : ""}
      ${w.kb_action === "create_starter" ? `<button class="btn primary" data-ready-kb-starter="1" style="float:right;margin-right:8px;">Create starter facts</button>` : ""}
      ${w.runtime_action === "enable_pipeline" ? `<button class="btn primary" data-ready-runtime-action="enable_pipeline" style="float:right;margin-right:8px;">Enable pipeline</button>` : ""}
      ${renderRuntimeGuidance(w.guidance)}
    </div>
  `).join("");
  actions.querySelectorAll("button[data-ready-section]").forEach((btn) => {
    btn.addEventListener("click", () => activateSection(btn.dataset.readySection));
  });
  actions.querySelectorAll("button[data-ready-template-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      activateSection("blocks");
      createFromTemplate(btn.dataset.readyTemplateId, {
        dryRun: true,
        scope: btn.dataset.readyTemplateScope || "global",
      });
    });
  });
  actions.querySelectorAll("button[data-ready-kb-starter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      createStarterKB({ switchToKB: true });
    });
  });
  actions.querySelectorAll("button[data-ready-runtime-action]").forEach((btn) => {
    btn.addEventListener("click", () => enablePipelineFromReadiness());
  });
  wireCopyCommandButtons(actions);
}

function readinessCard(title, value, status, detail) {
  return `
    <div class="readiness-card ${status}">
      <strong>${escapeHtml(title)}</strong>
      <div class="value">${escapeHtml(value)}</div>
      <div style="color:var(--muted);font-size:12px;margin-top:8px;word-break:break-word;">${escapeHtml(detail || "")}</div>
    </div>
  `;
}

registerSection("readiness", loadReadiness);
