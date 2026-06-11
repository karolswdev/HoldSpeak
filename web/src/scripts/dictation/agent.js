// ── Agent context + hooks, and the project-root override ────────────
// The Claude/Codex hook surfaces (captured agent context, hook templates,
// summarization) and the project-root override + recent-roots picker that
// re-scopes every project-aware tab.
import {
  state,
  api,
  escapeHtml,
  escapeAttr,
  basename,
  projectRootParam,
  registerSection,
  loadSection,
  wireCopyCommandButtons,
} from "./core.js";
import { loadScope } from "./blocks.js";
import { clearDryRun } from "./dryrun.js";
import { maybeShowKnNudge } from "./discovery-nudge.js";

export async function loadAgentContext() {
  const banner = document.getElementById("agent-context-banner");
  if (!banner) return;
  try {
    const data = await api("GET", `/api/dictation/agent-context${projectRootParam("?")}`);
    renderAgentContext(data);
  } catch (_e) {
    state.agentSession = null;
    banner.hidden = true;
  }
}

function renderAgentContext(data) {
  const banner = document.getElementById("agent-context-banner");
  const title = document.getElementById("agent-context-title");
  const text = document.getElementById("agent-context-text");
  if (!banner || !title || !text) return;

  const session = data && data.session;
  if (!session || !session.awaiting_response || !session.last_assistant_text) {
    state.agentSession = null;
    banner.hidden = true;
    return;
  }

  state.agentSession = session;
  const label = [session.agent, session.project_name || basename(session.repo_root), session.cwd]
    .filter(Boolean)
    .join(" · ");
  const assistantText = String(session.last_assistant_text || "");
  const preview = assistantText.length > 320 ? `${assistantText.slice(0, 320)}…` : assistantText;
  const summary = session.summary && session.summary.summary ? String(session.summary.summary) : "";
  const summaryPreview = summary
    ? `<br><strong>Summary:</strong> ${escapeHtml(summary.length > 240 ? `${summary.slice(0, 240)}…` : summary)}`
    : "";
  title.textContent = `${session.agent || "Agent"} is waiting for your reply`;
  text.innerHTML = `${escapeHtml(label)}<br>${escapeHtml(preview)}${summaryPreview}`;
  banner.hidden = false;
}

export async function clearAgentContext() {
  if (!state.agentSession) return;
  const button = document.getElementById("agent-context-clear");
  if (button) button.disabled = true;
  try {
    await api("POST", "/api/dictation/agent-context/clear", {
      agent: state.agentSession.agent,
      session_id: state.agentSession.session_id,
      project_root: state.projectRootOverride.trim() || state.agentSession.repo_root || "",
    });
    state.agentSession = null;
    renderAgentContext({ session: null });
  } catch (_e) {
    await loadAgentContext();
  } finally {
    if (button) button.disabled = false;
  }
}

export async function summarizeAgentContext() {
  const button = document.getElementById("agent-summary-run");
  const status = document.getElementById("agent-summary-status");
  const provider = document.getElementById("agent-summary-provider").value;
  const timeout = Number(document.getElementById("agent-summary-timeout").value || 20);
  if (!button || !status) return;
  button.disabled = true;
  status.classList.remove("error", "warn");
  status.textContent = "Summarizing captured agent context…";
  try {
    const payload = {
      provider,
      timeout_seconds: Math.max(1, Math.min(60, timeout || 20)),
      project_root: state.projectRootOverride.trim(),
    };
    if (state.agentSession) {
      payload.agent = state.agentSession.agent;
    }
    const data = await api("POST", "/api/dictation/agent-context/summarize", payload);
    state.agentSession = data.session || state.agentSession;
    const summary = data.summary || {};
    status.textContent = summary.summary
      ? `${summary.provider || provider}: ${summary.summary}`
      : "Summary generated.";
    await loadAgentContext();
    if (state.activeSection === "hooks") await loadAgentHooks();
  } catch (e) {
    status.classList.add("error");
    status.textContent = e.message;
  } finally {
    button.disabled = false;
  }
}

export async function loadAgentHooks() {
  const banner = document.getElementById("hooks-meta-banner");
  const list = document.getElementById("hooks-agent-list");
  if (!banner || !list) return;
  const capture = document.getElementById("hooks-capture-messages").checked;
  banner.classList.remove("warn", "error");
  banner.textContent = "Loading…";
  list.innerHTML = "";
  try {
    const data = await api("GET", `/api/dictation/agent-hooks?capture_messages=${capture ? "true" : "false"}`);
    state.hooks = data;
    renderAgentHooks(data);
  } catch (e) {
    banner.classList.add("error");
    banner.textContent = e.message;
  }
}

function renderAgentHooks(data) {
  const banner = document.getElementById("hooks-meta-banner");
  const list = document.getElementById("hooks-agent-list");
  const summaryProviderStatus = document.getElementById("agent-summary-provider-status");
  const capture = !!data.capture_messages;
  banner.classList.remove("warn", "error");
  banner.innerHTML =
    `registry: <strong>${escapeHtml(data.registry_path || "—")}</strong>` +
    `  ·  assistant capture: <strong>${capture ? "included" : "not included"}</strong>`;
  if (summaryProviderStatus) {
    const summarizers = data.summarizers || {};
    summaryProviderStatus.innerHTML = ["codex", "claude"].map((provider) => {
      const status = summarizers[provider] || {};
      const state = status.available ? "available" : "not installed";
      const safety = status.safe_default ? "safe default" : `unsafe: ${status.safe_default_error || "blocked"}`;
      const command = status.command_display || provider;
      return `<span class="hook-status-item"><strong>${escapeHtml(provider)}</strong>: ${escapeHtml(state)} · ${escapeHtml(safety)}<br><code>${escapeHtml(command)}</code></span>`;
    }).join("<br>");
  }

  const agents = data.agents || {};
  list.innerHTML = ["claude", "codex"].map((agent) => {
    const entry = agents[agent] || {};
    const latest = entry.latest_session;
    const destination = (data.destinations || {})[agent] || "";
    const status = latest
      ? [
          `latest: ${latest.updated_at || "unknown"}`,
          `cwd: ${latest.cwd || "—"}`,
          `capture: ${latest.capture_messages ? "enabled" : "disabled"}`,
          latest.awaiting_response ? "awaiting response" : "",
        ].filter(Boolean).join(" · ")
      : "No hook events recorded yet.";
    return `
      <article class="hook-card">
        <h3>${escapeHtml(agent)}</h3>
        <p class="hook-status">Destination: ${escapeHtml(destination)}</p>
        <p class="hook-status">${escapeHtml(status)}</p>
        <div class="actions">
          <button class="btn primary" data-copy-command="${escapeAttr(entry.template_json || "")}">Copy template</button>
        </div>
        <pre class="hook-template"><code>${escapeHtml(entry.template_json || "{}")}</code></pre>
      </article>
    `;
  }).join("");
  wireCopyCommandButtons(list);
}

export async function applyProjectRootOverride() {
  const input = document.getElementById("project-root-override");
  const raw = input.value.trim();
  const status = document.getElementById("project-root-status");
  status.style.color = "var(--muted)";
  status.textContent = raw ? "Validating…" : "Using cwd project detection.";
  if (raw) {
    try {
      const data = await api("GET", `/api/dictation/project-context?project_root=${encodeURIComponent(raw)}`);
      input.value = data.project.root;
      status.style.color = "var(--accent-2)";
      status.textContent = `Selected ${data.project.name} (${data.project.anchor})`;
    } catch (e) {
      status.style.color = "var(--danger)";
      status.textContent = e.message;
      return;
    }
  }
  state.projectRootOverride = input.value.trim();
  if (state.projectRootOverride) {
    localStorage.setItem("holdspeak.projectRootOverride", state.projectRootOverride);
    rememberProjectRoot(state.projectRootOverride);
  } else {
    localStorage.removeItem("holdspeak.projectRootOverride");
    loadDetectedProjectContext();
  }
  refreshProjectScopedView();
}

export function clearProjectRootOverride() {
  state.projectRootOverride = "";
  document.getElementById("project-root-override").value = "";
  localStorage.removeItem("holdspeak.projectRootOverride");
  loadDetectedProjectContext();
  refreshProjectScopedView();
}

export async function loadDetectedProjectContext() {
  const status = document.getElementById("project-root-status");
  if (state.projectRootOverride.trim()) {
    status.style.color = "var(--accent-2)";
    status.textContent = `Selected override: ${state.projectRootOverride.trim()}`;
    return;
  }
  status.style.color = "var(--muted)";
  status.textContent = "Detecting cwd project…";
  try {
    const data = await api("GET", "/api/dictation/project-context");
    const project = data.project || {};
    status.style.color = "var(--accent-2)";
    status.textContent =
      `Using cwd: ${project.name || "project"} (${project.anchor || "detected"}) @ ${project.root || ""}`;
  } catch (e) {
    status.style.color = e.status === 404 ? "var(--warn)" : "var(--danger)";
    status.textContent = e.status === 404 ? "No cwd project detected." : e.message;
  }
}

function saveRecentProjectRoots() {
  localStorage.setItem("holdspeak.recentProjectRoots", JSON.stringify(state.recentProjectRoots.slice(0, 6)));
  renderRecentProjectRoots();
}

function rememberProjectRoot(root) {
  const normalized = String(root || "").trim();
  if (!normalized) return;
  state.recentProjectRoots = [
    normalized,
    ...state.recentProjectRoots.filter((r) => r !== normalized),
  ].slice(0, 6);
  saveRecentProjectRoots();
}

export function renderRecentProjectRoots() {
  const select = document.getElementById("project-root-recent");
  select.innerHTML = `<option value="">Recent roots</option>` + state.recentProjectRoots.map((root) =>
    `<option value="${escapeAttr(root)}">${escapeHtml(root)}</option>`
  ).join("");
}

export async function useRecentProjectRoot() {
  const select = document.getElementById("project-root-recent");
  if (!select.value) return;
  document.getElementById("project-root-override").value = select.value;
  await applyProjectRootOverride();
  select.value = "";
}

function refreshProjectScopedView() {
  loadAgentContext();
  if (state.activeSection === "readiness") loadSection("readiness");
  if (state.activeSection === "blocks" && state.scope === "project") loadScope("project");
  if (state.activeSection === "kb") loadSection("kb");
  if (state.activeSection === "hs") loadSection("hs");
  if (state.activeSection === "hooks") loadAgentHooks();
  if (state.activeSection === "dry-run") clearDryRun();
  maybeShowKnNudge();
}

registerSection("hooks", loadAgentHooks);
