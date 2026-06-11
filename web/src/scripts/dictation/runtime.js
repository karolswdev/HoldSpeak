// ── Runtime config: the pipeline + backend editor and copilot depth ──
import {
  api,
  escapeHtml,
  projectRootParam,
  activateSection,
  registerSection,
  renderRuntimeGuidance,
  wireCopyCommandButtons,
} from "./core.js";

export const rtState = { last: null };

export async function loadRuntime() {
  const banner = document.getElementById("rt-meta-banner");
  banner.classList.remove("warn", "error");
  banner.textContent = "Loading…";
  try {
    const data = await api("GET", "/api/settings");
    let readiness = null;
    try {
      readiness = await api("GET", `/api/dictation/readiness${projectRootParam("?")}`);
    } catch (_) {
      readiness = null;
    }
    rtState.last = data;
    renderRuntime(data, readiness);
  } catch (e) {
    banner.classList.add("error");
    banner.textContent = e.message;
  }
}

export function renderRuntime(data, readiness = null) {
  const dictation = data.dictation || {};
  const pipeline = dictation.pipeline || {};
  const runtime = dictation.runtime || {};
  const status = data._runtime_status || { counters: {}, session: {} };

  const passes = Number(pipeline.rewrite_passes ?? 1);
  document.getElementById("rt-meta-banner").innerHTML =
    `pipeline: <strong>${pipeline.enabled ? "enabled" : "disabled"}</strong>  ·  ` +
    `target: <strong>${escapeHtml(pipeline.target_profile_override || "auto")}</strong>  ·  ` +
    `backend: <strong>${escapeHtml(runtime.backend || "auto")}</strong>  ·  ` +
    `cold-start cap: <strong>${(pipeline.max_total_latency_ms || 0) * 5} ms</strong>  ·  ` +
    `depth: <strong>${passes}× pass${passes === 1 ? "" : "es"}</strong>` +
    `${pipeline.corrections_enabled ? " · <strong>learns</strong>" : ""}` +
    `${pipeline.target_detect_llm_enabled ? " · <strong>infers target</strong>" : ""}`;

  document.getElementById("rt-enabled").checked = !!pipeline.enabled;
  document.getElementById("rt-stage-rewriter").checked =
    Array.isArray(pipeline.stages) && pipeline.stages.includes("project-rewriter");
  document.getElementById("rt-target-profile").value = pipeline.target_profile_override || "auto";
  document.getElementById("rt-backend").value = runtime.backend || "auto";
  document.getElementById("rt-mlx-model").value = runtime.mlx_model || "";
  document.getElementById("rt-llama-path").value = runtime.llama_cpp_model_path || "";
  document.getElementById("rt-openai-model").value = runtime.openai_compatible_model || "";
  document.getElementById("rt-openai-base-url").value = runtime.openai_compatible_base_url || "";
  document.getElementById("rt-openai-api-key-env").value = runtime.openai_compatible_api_key_env || "";
  document.getElementById("rt-openai-timeout").value = runtime.openai_compatible_timeout_seconds || 8;
  document.getElementById("rt-warm").checked = !!runtime.warm_on_start;
  const slider = document.getElementById("rt-latency");
  slider.value = pipeline.max_total_latency_ms || 600;
  slider.oninput = updateLatencyVis;
  updateLatencyVis();

  // ── Copilot depth (HS-40-03) ──
  setRewritePasses(passes);
  document.getElementById("rt-corrections-enabled").checked = !!pipeline.corrections_enabled;
  document.getElementById("rt-target-detect-llm-enabled").checked = !!pipeline.target_detect_llm_enabled;
  const below = document.getElementById("rt-target-detect-llm-below");
  below.value = pipeline.target_detect_llm_below ?? 0.8;
  below.oninput = updateTargetBelowVis;
  updateTargetBelowVis();
  updateTargetDetectReveal();

  // Counters
  const counters = status.counters || {};
  document.getElementById("rt-counters").innerHTML = `
    <div>model_loads:        <strong>${counters.model_loads ?? 0}</strong></div>
    <div>classify_calls:     <strong>${counters.classify_calls ?? 0}</strong></div>
    <div>classify_failures:  <strong>${counters.classify_failures ?? 0}</strong></div>
    <div>constrained_retries: <strong>${counters.constrained_retries ?? 0}</strong></div>
  `;

  // Session-disabled banner
  const sessionBanner = document.getElementById("rt-session-banner");
  const session = status.session || {};
  if (session.llm_disabled_for_session) {
    sessionBanner.innerHTML = `<div class="error-box">LLM disabled for this session: ${escapeHtml(session.disabled_reason || "(no reason)")}</div>`;
  } else {
    sessionBanner.innerHTML = `<div class="ok-box">LLM stage active for this session.</div>`;
  }

  const guidance = readiness?.runtime?.guidance ||
    (readiness?.warnings || []).find((w) => w.guidance)?.guidance;
  const guidanceHost = document.getElementById("rt-guidance");
  guidanceHost.innerHTML = renderRuntimeGuidance(guidance);
  wireCopyCommandButtons(guidanceHost);
}

function updateLatencyVis() {
  const v = Number(document.getElementById("rt-latency").value);
  document.getElementById("rt-latency-vis").textContent =
    `${v} ms  ·  cold-start cap: ${v * 5} ms (DIR-R-003)`;
}

// ── Copilot depth controls (HS-40-03) ──
const REWRITE_PASS_DESC = {
  1: "Single pass — fastest; byte-identical to a plain rewrite.",
  2: "Two passes — one critique-and-refine after the draft.",
  3: "Three passes — balanced refinement (recommended for project work).",
  4: "Four passes — deeper polish; watch the latency budget.",
  5: "Five passes — maximum refinement; most latency-budget gating.",
};

export function setRewritePasses(n) {
  const passes = Math.min(5, Math.max(1, Math.round(Number(n) || 1)));
  document.getElementById("rt-rewrite-passes").value = String(passes);
  document.getElementById("rt-rewrite-badge").textContent = `${passes}×`;
  document.getElementById("rt-rewrite-desc").textContent =
    REWRITE_PASS_DESC[passes] || "";
  document.querySelectorAll("#rt-rewrite-seg .seg-btn").forEach((btn) =>
    btn.setAttribute(
      "aria-pressed",
      btn.dataset.value === String(passes) ? "true" : "false"
    )
  );
}

function updateTargetBelowVis() {
  const v = Number(document.getElementById("rt-target-detect-llm-below").value);
  document.getElementById("rt-target-below-val").textContent = v.toFixed(2);
}

export function updateTargetDetectReveal() {
  const on = document.getElementById("rt-target-detect-llm-enabled").checked;
  document.getElementById("rt-target-below-wrap").hidden = !on;
}

export async function saveRuntime(options = {}) {
  const msg = document.getElementById("rt-msg");
  msg.innerHTML = "";

  // Inline validation mirroring the API bounds (HS-40-01) so out-of-range is
  // caught before submit. The segmented control + 0–1 slider already constrain
  // input, but guard anyway for keyboard/programmatic edits.
  const rewritePasses = Number(document.getElementById("rt-rewrite-passes").value);
  const targetBelow = Number(document.getElementById("rt-target-detect-llm-below").value);
  if (!Number.isInteger(rewritePasses) || rewritePasses < 1 || rewritePasses > 5) {
    msg.innerHTML = `<div class="error-box">Rewrite passes must be a whole number between 1 and 5.</div>`;
    return;
  }
  if (!(targetBelow >= 0 && targetBelow <= 1)) {
    msg.innerHTML = `<div class="error-box">Infer-target threshold must be between 0.00 and 1.00.</div>`;
    return;
  }

  const payload = {
    dictation: {
      pipeline: {
        enabled: document.getElementById("rt-enabled").checked,
        stages: [
          "intent-router",
          ...(document.getElementById("rt-stage-rewriter").checked ? ["project-rewriter"] : []),
          "kb-enricher",
        ],
        max_total_latency_ms: Number(document.getElementById("rt-latency").value),
        target_profile_override: document.getElementById("rt-target-profile").value,
        rewrite_passes: rewritePasses,
        corrections_enabled: document.getElementById("rt-corrections-enabled").checked,
        target_detect_llm_enabled: document.getElementById("rt-target-detect-llm-enabled").checked,
        target_detect_llm_below: targetBelow,
      },
      runtime: {
        backend: document.getElementById("rt-backend").value,
        mlx_model: document.getElementById("rt-mlx-model").value.trim(),
        llama_cpp_model_path: document.getElementById("rt-llama-path").value.trim(),
        openai_compatible_model: document.getElementById("rt-openai-model").value.trim(),
        openai_compatible_base_url: document.getElementById("rt-openai-base-url").value.trim(),
        openai_compatible_api_key_env: document.getElementById("rt-openai-api-key-env").value.trim(),
        openai_compatible_timeout_seconds: Number(document.getElementById("rt-openai-timeout").value),
        warm_on_start: document.getElementById("rt-warm").checked,
      },
    },
  };
  try {
    await api("PUT", "/api/settings", payload);
    msg.innerHTML = `<div class="ok-box">${escapeHtml(options.message || "Saved. New utterances pick up the config on next pipeline rebuild.")}</div>`;
    await loadRuntime();
  } catch (e) {
    msg.innerHTML = `<div class="error-box">${escapeHtml(e.message)}</div>`;
  }
}

export async function saveRuntimeAndTest() {
  // Save the cockpit config, then jump to the dry-run so the user can try the
  // exact config they just set (HS-40-03 "test this config" affordance).
  await saveRuntime({ message: "Saved — opening dry-run so you can test this config." });
  const errored = document.querySelector("#rt-msg .error-box");
  if (!errored) activateSection("dry-run");
}

export async function enablePipelineFromReadiness() {
  activateSection("runtime");
  await loadRuntime();
  document.getElementById("rt-enabled").checked = true;
  await saveRuntime({ message: "Enabled. New utterances pick up the config on next pipeline rebuild." });
}

registerSection("runtime", loadRuntime);
