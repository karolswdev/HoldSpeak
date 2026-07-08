/* Delivery Workbench — hash-routed, API-backed. Views are read-only;
 * mutations go only through the preview → apply workflow below.
 * Every byte of state comes from /api/*, which derives live from the
 * Markdown roadmap through the dw_pmo core. No local persistence. */

"use strict";

const app = document.getElementById("app");
const crumbs = document.getElementById("crumbs");
const refreshTime = document.getElementById("refresh-time");
const footRoot = document.getElementById("foot-root");

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

/* ?snapshot=1 switches to synchronous XHR so headless screenshot tools
 * that capture at the window load event see fully rendered data. Not
 * for interactive use. */
const SNAPSHOT_MODE = new URLSearchParams(location.search).has("snapshot");

function syncGet(path) {
  const xhr = new XMLHttpRequest();
  xhr.open("GET", path, false);
  xhr.send();
  return { status: xhr.status, body: JSON.parse(xhr.responseText) };
}

async function postJson(path, payload) {
  if (SNAPSHOT_MODE) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", path, false);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify(payload));
    return { status: xhr.status, body: JSON.parse(xhr.responseText) };
  }
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return { status: res.status, body: await res.json() };
}

function diffHtml(diff) {
  return diff.split("\n").map((line) => {
    const cls = line.startsWith("+") ? "add" : line.startsWith("-") ? "del" : line.startsWith("@@") ? "hunk" : "";
    return cls ? `<span class="${cls}">${esc(line)}</span>` : esc(line);
  }).join("\n");
}

async function api(path) {
  let status;
  let body;
  if (SNAPSHOT_MODE) {
    ({ status, body } = syncGet(path));
  } else {
    const res = await fetch(path, { cache: "no-store" });
    status = res.status;
    body = await res.json();
  }
  if (status >= 400 || body.ok === false) {
    const msg = (body.issues && body.issues[0]) || `API error ${status}`;
    throw new Error(msg);
  }
  refreshTime.textContent = `refreshed ${new Date().toLocaleTimeString()}`;
  return body;
}

function setCrumbs(parts) {
  crumbs.innerHTML = parts
    .map((p, i) => (i < parts.length - 1 && p.href
      ? `<a href="${p.href}">${esc(p.label)}</a>`
      : `<span>${esc(p.label)}</span>`))
    .join(" / ");
}

function stateHtml(text, isError) {
  return `<div class="state${isError ? " error" : ""}">${esc(text)}</div>`;
}

function badge(text, cls) {
  return `<span class="badge ${cls || esc(String(text))}">${esc(text)}</span>`;
}

function statusCounts(counts) {
  const order = ["in-progress", "ready", "backlog", "blocked", "done"];
  const keys = Object.keys(counts).sort(
    (a, b) => (order.indexOf(a) + 99) - (order.indexOf(b) + 99) || a.localeCompare(b)
  );
  if (!keys.length) return '<span class="badge">no stories</span>';
  return keys.map((k) => badge(`${k} ${counts[k]}`, k)).join(" ");
}

/* ── mission control (WLA-15-01): the read-only belt ──────────────
 * The workbench is the fourth consumer of the mission-control
 * substrate (feed + sessions + events), read-only by charter — the
 * picture without the hands. A single-flight 10s poll keeps it live
 * while the view is open; leaving the view stops the poll. */

let mcPoll = null;
let mcInFlight = false;

function stopMcPoll() {
  if (mcPoll) { clearInterval(mcPoll); mcPoll = null; }
}

function mcPin(s) {
  return `<span class="mc-pin${s.awaiting_response ? " awaiting" : ""}${s.stale ? " stale" : ""}"
    title="${esc(s.key)}${s.awaiting_response ? " — awaiting a response" : ""}${s.stale ? " (stale)" : ""}">${s.awaiting_response ? "🙋" : "🤖"}${esc(s.agent)}</span>`;
}

function mcBelt(project, pins) {
  const current = project.current_phase;
  const beltStories = current
    ? project.stories.filter((s) => s.phase === current.number) : [];
  const nextId = project.next_story ? project.next_story.story_id : null;
  return `
    <div class="mc-project">
      <div class="mc-phases">
        <span class="mc-slug">${esc(project.slug)}</span>
        ${project.phases.map((ph) => `
          <span class="mc-phase${ph.status === "closed" ? " closed" : ""}${current && ph.number === current.number ? " current" : ""}"
                title="${esc(ph.title)} — ${ph.stories_done}/${ph.stories_total}">${ph.number}</span>`).join("")}
        ${project.warnings ? `<span class="mc-warn">⚠ ${project.warnings}</span>` : ""}
      </div>
      <div class="mc-belt">
        ${beltStories.map((s) => `
          <span class="mc-story st-${esc(s.status)}${s.story_id === nextId ? " next" : ""}"
                title="${esc(s.title)} [${esc(s.status)}]${s.evidence_exists ? " ·evidence" : ""}">
            <a href="#/p/${encodeURIComponent(project.slug)}/s/${encodeURIComponent(s.story_id)}">${esc(s.story_id)}</a>${s.evidence_exists ? " ✓" : ""}${(pins[s.story_id] || []).map(mcPin).join("")}
          </span>`).join("")}
      </div>
    </div>`;
}

function mcOffBelt(doc, offBelt) {
  if (!doc || doc.registry !== "ok") {
    return `<div class="sub">sessions: registry ${esc(doc ? String(doc.registry) : "unavailable")}</div>`;
  }
  if (!offBelt.length) return `<div class="sub">every live session is pinned to its story on the belt</div>`;
  return offBelt.map((s) => {
    const where = s.correlation === "ambiguous" && s.stories.length
      ? `ambiguous: ${s.stories.map((st) => st.story_id).join(", ")}`
      : s.correlation.replace(/_/g, " ");
    return `<div class="mc-session${s.awaiting_response ? " awaiting" : ""}${s.stale ? " stale" : ""}">
      <code>${esc(s.key)}</code> — ${esc(s.agent)} — ${esc(where)}
      ${s.awaiting_response ? badge("awaiting a response", "warn") : ""}
      ${s.stale ? badge("stale") : ""}
    </div>`;
  }).join("");
}

function mcEvents(events) {
  if (!events.length) return `<div class="sub">no rail events yet</div>`;
  return `<div class="mc-ticker">` + events.slice().reverse().map((e) => {
    const detail = Object.entries(e.detail || {})
      .filter(([, v]) => v !== null && v !== undefined)
      .map(([k, v]) => `${k}=${v}`).join(" ");
    const refusal = e.event === "gate_refusal";
    return `<div class="mc-event${refusal ? " refusal" : ""}">
      ${refusal ? "✕ " : ""}${esc(e.ts || "?")}  ${esc(e.event || "?")}${e.story ? `  ${esc(e.story)}` : ""}${detail ? `  ${esc(detail)}` : ""}
    </div>`;
  }).join("") + `</div>`;
}

async function loadMissionControl() {
  if (mcInFlight) return; // single-flight: a slow poll skips ticks
  mcInFlight = true;
  try {
    const body = await api("/api/missioncontrol");
    const data = body.data;
    const el = document.getElementById("mc-root");
    if (!el) { stopMcPoll(); return; } // view left; stop polling
    el.innerHTML = `
      <div class="section"><h2>the belt</h2>
        ${data.feed.projects.map((p) => mcBelt(p, data.pins || {})).join("") || stateHtml("no projects on the rails here")}
      </div>
      <div class="section"><h2>off the belt</h2>${mcOffBelt(data.sessions, data.off_belt || [])}</div>
      <div class="section"><h2>rail events</h2>${mcEvents(data.events)}</div>
      <div class="sub">read-only — the workbench never stages or commits; steering lives on the phone and the Desk.</div>`;
  } finally {
    mcInFlight = false;
  }
}

async function viewMissionControl() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "mission control" }]);
  app.innerHTML = `<div id="mc-root">${stateHtml("Loading the belt…")}</div>`;
  await loadMissionControl();
  mcPoll = setInterval(() => { loadMissionControl().catch(() => {}); }, 10000);
}

/* ── views ─────────────────────────────────────────────────────────── */

async function viewOverview() {
  setCrumbs([{ label: "overview" }]);
  const body = await api("/api/projects");
  const projects = body.data.projects;
  if (!projects.length) {
    app.innerHTML = stateHtml("No roadmap projects found under pm/roadmap/. Scaffold one with `dw phase create` or `dw adopt`.");
    return;
  }
  app.innerHTML = `<div class="grid">` + projects.map((p) => `
    <div class="card">
      <h3><a href="#/p/${encodeURIComponent(p.slug)}">${esc(p.slug)}</a>
        <span class="badge">${esc(p.prefix)}</span></h3>
      <div class="sub">${esc(p.path)}</div>
      <div class="stats">
        <span>phases <b>${p.phase_count}</b></span>
        <span>active <b>${p.active_phase_count}</b></span>
        <span>${p.issue_count ? badge(`${p.issue_count} issue${p.issue_count > 1 ? "s" : ""}`, "issue") : badge("checks ok", "ok")}</span>
        <span>${p.warning_count ? badge(`${p.warning_count} warning${p.warning_count > 1 ? "s" : ""}`, "warn") : ""}</span>
      </div>
      <div class="stats" style="margin-top:6px">${statusCounts(p.story_status_counts)}</div>
      ${p.next_story ? `
        <div class="next"><span class="lbl">next</span>
          <a href="#/p/${encodeURIComponent(p.slug)}/s/${encodeURIComponent(p.next_story.story_id)}">
            <code>${esc(p.next_story.story_id)}</code></a>
          ${esc(p.next_story.title)} ${badge(p.next_story.status)}
        </div>` : `<div class="next"><span class="lbl">next</span> nothing actionable</div>`}
    </div>`).join("") + `</div>`;
}

async function viewProject(slug) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: slug }]);
  const body = await api(`/api/projects/${encodeURIComponent(slug)}`);
  const p = body.data;
  const phases = p.phases.map((ph) => {
    const counts = {};
    ph.stories.forEach((s) => { counts[s.status] = (counts[s.status] || 0) + 1; });
    const evidenced = ph.stories.filter((s) => s.evidence_exists).length;
    return `<tr>
      <td><a href="#/p/${encodeURIComponent(slug)}/ph/${ph.number}"><code>${ph.number}</code> ${esc(ph.slug)}</a></td>
      <td>${ph.active ? badge("active", "in-progress") : badge("closed", "done")}</td>
      <td>${statusCounts(counts)}</td>
      <td>${evidenced}/${ph.stories.length}</td>
      <td>${ph.final_summary_exists
        ? `<a href="#/f/${encodeURIComponent(ph.final_summary)}">${badge("summary", "ok")}</a>` : "—"}</td>
    </tr>`;
  }).join("");
  app.innerHTML = `
    ${p.next_story ? `<div class="next"><span class="lbl">next</span>
      <a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(p.next_story.story_id)}">
        <code>${esc(p.next_story.story_id)}</code></a> ${esc(p.next_story.title)} ${badge(p.next_story.status)}</div>` : ""}
    <div class="section"><h2>Phases</h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>Phase</th><th>State</th><th>Stories</th><th>Evidence</th><th>Summary</th></tr>
        ${phases || '<tr><td colspan="5">no phases yet</td></tr>'}
      </table></div></div>
    ${p.issues.length ? `<div class="guard">mutations guarded — <a href="#/health">${p.issues.length} validation issue${p.issues.length === 1 ? "" : "s"}</a> must be resolved first</div>
    <div class="section"><h2>Validation issues (<a href="#/health">health console</a>)</h2>
      <ul class="plain">${p.issues.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul></div>` : ""}
    ${p.warnings.length ? `<div class="section"><h2>Warnings</h2>
      <ul class="plain">${p.warnings.map((w) => `<li class="warn">${esc(w)}</li>`).join("")}</ul></div>` : ""}
    <div class="section"><h2>Supplemental canon</h2>
      <ul class="plain">${p.supplemental_canon.length ? p.supplemental_canon.map((c) =>
        `<li><a href="#/f/${encodeURIComponent(c.path)}">${esc(c.path)}</a>
         <code>${esc(c.kind)} · ${esc(c.scope)}</code></li>`).join("")
        : "<li>none</li>"}</ul></div>`;
}

async function viewPhase(slug, number) {
  setCrumbs([{ label: "overview", href: "#/" },
    { label: slug, href: `#/p/${encodeURIComponent(slug)}` },
    { label: `phase ${number}` }]);
  const body = await api(`/api/projects/${encodeURIComponent(slug)}/phases/${encodeURIComponent(number)}`);
  const ph = body.data;
  const rows = ph.stories.map((s) => `<tr>
    <td><a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(s.story_id)}"><code>${esc(s.story_id)}</code></a></td>
    <td>${esc(s.title)}</td>
    <td>${badge(s.status)}${s.header_status && s.header_status !== s.status ? " " + badge("header: " + s.header_status, "issue") : ""}</td>
    <td>${s.evidence_exists ? badge("evidence", "ok") : badge("no evidence", s.status === "done" ? "issue" : "")}</td>
    <td><a href="#/f/${encodeURIComponent(s.story_path)}"><code>story</code></a>${s.evidence_exists
      ? ` · <a href="#/f/${encodeURIComponent(s.evidence_path)}"><code>evidence</code></a>` : ""}
      · <a href="#/p/${encodeURIComponent(slug)}/t/${encodeURIComponent(s.story_id)}"><code>trace</code></a></td>
  </tr>`).join("");
  app.innerHTML = `
    <div class="meta">
      <div class="kv"><div class="k">status file</div><div class="v"><a href="#/f/${encodeURIComponent(ph.status_file)}">${esc(ph.status_file)}</a></div></div>
      <div class="kv"><div class="k">state</div><div class="v">${ph.active ? "active" : "closed"}</div></div>
      <div class="kv"><div class="k">final summary</div><div class="v">${ph.final_summary_exists
        ? `<a href="#/f/${encodeURIComponent(ph.final_summary)}">${esc(ph.final_summary)}</a>` : "not written"}</div></div>
    </div>
    <div class="section"><h2>Stories (normalized from current-phase-status.md)</h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>ID</th><th>Story</th><th>Status</th><th>Evidence</th><th>Source</th></tr>
        ${rows || '<tr><td colspan="5">no stories yet</td></tr>'}
      </table></div></div>
    <div class="section"><h2>Recent commits (phase trace)</h2>
      <div id="phase-events" class="state">Loading…</div></div>
    ${ph.final_summary_content ? `<div class="section"><h2>Final summary</h2>
      <pre class="src">${esc(ph.final_summary_content)}</pre></div>` : ""}`;
  api(`/api/projects/${encodeURIComponent(slug)}/phases/${encodeURIComponent(number)}/events`).then((ev) => {
    const rows = ev.data.events.map((c) => `<tr>
      <td><code>${esc(c.date)}</code></td><td>${esc(c.subject)}
        ${c.pmo_story ? " " + badge(c.pmo_story, "ok") : ""}
        ${c.contract_digest ? ` <span class="badge" title="${esc(c.contract_digest)}">digest</span>` : ""}</td>
      <td><code>${esc(String(c.sha).slice(0, 9))}</code></td></tr>`).join("");
    document.getElementById("phase-events").outerHTML = rows
      ? `<div class="tblwrap"><table class="tbl"><tr><th>Date</th><th>Commit</th><th>SHA</th></tr>${rows}</table></div>`
      : `<div class="state">no commits touch this phase directory yet</div>`;
  }).catch(() => {
    const el = document.getElementById("phase-events");
    if (el) el.textContent = "phase commits unavailable (no git history)";
  });
}

async function viewStory(slug, storyId) {
  setCrumbs([{ label: "overview", href: "#/" },
    { label: slug, href: `#/p/${encodeURIComponent(slug)}` },
    { label: storyId }]);
  const body = await api(`/api/projects/${encodeURIComponent(slug)}/stories/${encodeURIComponent(storyId)}`);
  const s = body.data;
  app.innerHTML = `
    <div class="meta">
      <div class="kv"><div class="k">story</div><div class="v">${esc(s.story_id)} — ${esc(s.title)}</div></div>
      <div class="kv"><div class="k">status</div><div class="v">${badge(s.status)}${s.header_status && s.header_status !== s.status ? " " + badge("header: " + s.header_status, "issue") : ""}</div></div>
      <div class="kv"><div class="k">phase</div><div class="v"><a href="#/p/${encodeURIComponent(slug)}/ph/${s.phase_number}">phase ${s.phase_number}</a></div></div>
      <div class="kv"><div class="k">evidence</div><div class="v">${s.evidence_exists ? esc(s.evidence_path) : "none"}</div></div>
      <div class="kv"><div class="k">trace</div><div class="v"><a href="#/p/${encodeURIComponent(slug)}/t/${encodeURIComponent(s.story_id)}">intent → proof timeline</a></div></div>
    </div>
    <div class="section pair">
      <div><h2>story · <code>${esc(s.story_path)}</code></h2>
        <pre class="src">${esc(s.story_markdown || "(missing story file)")}</pre></div>
      <div><h2>evidence · <code>${esc(s.evidence_path || "—")}</code></h2>
        <pre class="src">${esc(s.evidence_markdown || "(no evidence file yet)")}</pre></div>
    </div>`;
}

async function viewFile(path) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: path }]);
  const body = await api(`/api/file?path=${encodeURIComponent(path)}`);
  app.innerHTML = `
    <div class="section"><h2>source · <code>${esc(body.data.path)}</code> (read-only)</h2>
      <pre class="src">${esc(body.data.content)}</pre></div>`;
}


const CATEGORY_LABELS = {
  "project": "Project pointers",
  "phase": "Phases",
  "story-evidence": "Stories & evidence",
  "hook-runtime": "Hooks & runtime",
  "supplemental-canon": "Supplemental canon",
};

function healthItem(item) {
  const kindCls = item.kind === "stale-pointer" ? "issue" : (item.severity === "error" ? "issue" : "warn");
  const folders = item.phase_folders
    ? `<div class="why">phase folders: ${item.phase_folders.map((f) => `<code>${esc(f)}</code>`).join(", ")}</div>` : "";
  return `<div class="hitem">
    ${badge(item.severity, item.severity === "error" ? "issue" : "warn")}
    ${badge(item.kind, kindCls)}
    <span class="msg">${item.path ? `<a href="#/f/${encodeURIComponent(item.path)}"><code>${esc(item.path)}</code></a> — ` : ""}${esc(item.message)}</span>
    ${item.explanation ? `<div class="why">${esc(item.explanation)}</div>` : ""}
    ${folders}
  </div>`;
}

async function viewHealth() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "health" }]);
  const body = await api("/api/health");
  const h = body.data;
  const sections = [];
  for (const proj of h.projects) {
    const byCat = {};
    proj.issues.concat(proj.warnings).forEach((item) => {
      (byCat[item.category] = byCat[item.category] || []).push(item);
    });
    const cats = Object.keys(byCat).map((cat) => `
      <div class="section"><h2>${esc(proj.slug)} · ${esc(CATEGORY_LABELS[cat] || cat)} (${byCat[cat].length})</h2>
        ${byCat[cat].map(healthItem).join("")}</div>`).join("");
    sections.push(cats || `<div class="section"><h2>${esc(proj.slug)}</h2>
      <div class="guard ok">no validation issues or warnings — mutations safe</div></div>`);
  }
  const hook = h.hook_snapshot;
  const hookRows = [
    ["pre-commit installed", hook.pre_commit_exists],
    ["post-commit installed", hook.post_commit_exists],
    ["config seam (pre-commit.config)", hook.has_config_seam],
    ["local rule seam (pre-commit.local)", hook.has_local_seam],
    ["work-log capture", hook.has_work_log_capture],
  ].map(([k, v]) => `<div class="hitem">${badge(v ? "ok" : "missing", v ? "ok" : "issue")}<span class="msg">${esc(k)}</span></div>`).join("");
  app.innerHTML = `
    <div class="guard ${h.mutation_safe ? "ok" : ""}">${h.mutation_safe
      ? "mutation-safe: no validation issues; editor operations (future) are unguarded"
      : `mutations guarded: ${h.total_issues} validation issue${h.total_issues === 1 ? "" : "s"} must be resolved in the source Markdown first`}</div>
    ${sections.join("")}
    <div class="section"><h2>Hook snapshot</h2>${hookRows}
      ${h.hook_explanations.length ? `<ul class="plain">${h.hook_explanations.map((e) => `<li class="warn">${esc(e)}</li>`).join("")}</ul>` : ""}</div>
    <div class="section"><h2>Work-log configuration (read-only)</h2>
      <div class="meta">
        <div class="kv"><div class="k">enabled</div><div class="v">${esc(h.work_log_config.enabled)}</div></div>
        <div class="kv"><div class="k">directory</div><div class="v">${esc(h.work_log_config.dir)}</div></div>
        <div class="kv"><div class="k">project slug</div><div class="v">${esc(h.work_log_config.project_slug)}</div></div>
        <div class="kv"><div class="k">exclude regex</div><div class="v">${esc(h.work_log_config.exclude_regex)}</div></div>
      </div></div>
    <div class="section"><h2>dw check (copyable)</h2>
      <div class="copybar"><button id="copy-check" type="button">copy</button></div>
      <pre class="src" id="check-output">${esc(h.check_output)}</pre></div>`;
  document.getElementById("copy-check").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("check-output").textContent);
  });
}


const HOP_LABELS = {
  readme: "project README",
  phase_status: "phase status",
  story: "story",
  evidence: "evidence",
  final_summary: "final summary",
};

let traceSortAsc = false;

async function viewTrace(slug, storyId) {
  setCrumbs([{ label: "overview", href: "#/" },
    { label: slug, href: `#/p/${encodeURIComponent(slug)}` },
    { label: storyId, href: `#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(storyId)}` },
    { label: "trace" }]);
  const apiPath = `/api/projects/${encodeURIComponent(slug)}/trace/${encodeURIComponent(storyId)}`;
  const body = await api(apiPath);
  const tl = body.data;
  const chain = tl.chain.map((hop) => `
    <div class="hitem">
      ${badge(hop.exists ? "present" : "absent", hop.exists ? "ok" : "issue")}
      <span class="msg"><b>${esc(HOP_LABELS[hop.hop] || hop.hop)}</b> —
        ${hop.exists && hop.path
          ? `<a href="#/f/${encodeURIComponent(hop.path)}"><code>${esc(hop.path)}</code></a>`
          : hop.path ? `<code>${esc(hop.path)}</code> <span class="badge issue">not written yet</span>`
                     : '<span class="badge issue">no path</span>'}</span>
    </div>`).join("");
  const events = tl.events.slice();
  if (traceSortAsc) events.reverse();
  const eventRows = events.length ? events.map((ev) => `<tr>
      <td>${badge(ev.type, ev.type === "commit" ? "in-progress" : "ok")}</td>
      <td><code>${esc(ev.sort_key || ev.date)}</code></td>
      <td>${esc(ev.subject || "(no subject)")}
        ${ev.pmo_story ? " " + badge(ev.pmo_story, "ok") : ""}
        ${ev.contract_digest ? ` <span class="badge" title="${esc(ev.contract_digest)}">digest</span>` : ""}</td>
      <td>${ev.type === "commit"
        ? `<code>${esc(String(ev.sha).slice(0, 9))}</code>`
        : `<a href="#/wl/${encodeURIComponent(ev.source)}"><code>${esc(ev.source)}</code></a>`}</td>
    </tr>`).join("")
    : '<tr><td colspan="4">no commits found for this story\u2019s PMO files; no work-log entries (optional evidence \u2014 absent, not an error)</td></tr>';
  app.innerHTML = `
    <div class="guard ${tl.shipped ? "ok" : ""}">${tl.shipped
      ? `shipped: story is done and its evidence exists`
      : `not shipped: ${esc(tl.not_shipped_reason)}`}</div>
    <div class="section"><h2>Trace chain — intent to proof</h2>${chain}</div>
    <div class="section"><h2>Events (commits + work-log)
      <button id="trace-sort" type="button" class="badge" style="cursor:pointer">${traceSortAsc ? "oldest first ↑" : "newest first ↓"}</button>
      <a class="badge" href="${apiPath}" target="_blank" title="machine-readable timeline">export JSON</a></h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>Type</th><th>When</th><th>What</th><th>Source</th></tr>
        ${eventRows}
      </table></div>
      <p class="hint">work-log entries are supplementary evidence; evidence-story-NN.md
        remains the proof of record and is required before a story counts as shipped.</p></div>
    <div class="section"><h2>Agent handoff</h2>
      <div class="copybar"><button id="copy-handoff" type="button">copy</button></div>
      <pre class="src" id="handoff-text">Loading\u2026</pre></div>`;
  api(`/api/projects/${encodeURIComponent(slug)}/handoff/${encodeURIComponent(storyId)}`).then((h) => {
    document.getElementById("handoff-text").textContent = h.data.text;
  }).catch((err) => {
    document.getElementById("handoff-text").textContent = `handoff unavailable: ${err.message}`;
  });
  document.getElementById("copy-handoff").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("handoff-text").textContent);
  });
  document.getElementById("trace-sort").addEventListener("click", () => {
    traceSortAsc = !traceSortAsc;
    route();
  });
}


async function viewWorklog(path) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "work log" }]);
  const body = await api(`/api/worklog?path=${encodeURIComponent(path)}`);
  app.innerHTML = `
    <div class="guard ok">supplementary evidence \u2014 work logs never replace evidence-story-NN.md</div>
    <div class="section"><h2>work log \u00b7 <code>${esc(body.data.path)}</code> (read-only, verbatim \u2014
      excluded paths were omitted at capture time and stay omitted here)</h2>
      <pre class="src">${esc(body.data.content)}</pre></div>`;
}

/* ── structured editor (WLA-5-06) ───────────────────────────────────
 * The editor constructs structured intent and POSTs it to
 * /api/mutations/preview. It never applies: the apply/diff workflow
 * is WLA-5-07. Client-side checks catch the obvious before the
 * server's authoritative refusals. */

const EDIT_ACTIONS = {
  create_phase: "create phase",
  create_story: "create story",
  update_story_status: "update story status",
  attach_evidence: "attach evidence",
  close_phase: "close phase",
};

const STATUS_VOCAB = ["backlog", "ready", "in-progress", "blocked", "done"];

function field(label, inner, err) {
  return `<label><b>${esc(label)}</b>${inner}
    <span class="fielderr" data-err="${esc(label)}">${err ? esc(err) : ""}</span></label>`;
}

function selectHtml(name, options, selected) {
  return `<select name="${name}">` + options.map((o) =>
    `<option value="${esc(o)}"${o === selected ? " selected" : ""}>${esc(o)}</option>`).join("") + "</select>";
}

async function viewEdit(action) {
  action = action || "create_story";
  setCrumbs([{ label: "overview", href: "#/" }, { label: "edit" }, { label: EDIT_ACTIONS[action] || action }]);
  const ctx = await api("/api/projects");
  const projects = ctx.data.projects;
  if (!projects.length) {
    app.innerHTML = stateHtml("No projects to edit.");
    return;
  }
  const proj = projects[0];
  const guarded = proj.issue_count > 0;
  const projDetail = await api(`/api/projects/${encodeURIComponent(proj.slug)}`);
  const phases = projDetail.data.phases;
  const phaseOpts = phases.map((ph) => String(ph.number));
  const stories = phases.flatMap((ph) => ph.stories.map((s) => s.story_id));

  const tabs = Object.keys(EDIT_ACTIONS).map((a) =>
    `<a href="#/edit/${a}" class="${a === action ? "active" : ""}">${esc(EDIT_ACTIONS[a])}</a>`).join("");

  let formFields = "";
  if (action === "create_phase") {
    formFields = [
      field("phase number", '<input type="number" name="number" min="0" step="1" required>'),
      field("title", '<input type="text" name="title" required>'),
      field("slug (optional)", '<input type="text" name="slug" pattern="[a-z0-9-]*" title="lowercase, digits, hyphens">'),
      field("goal (one line)", '<input type="text" name="goal">'),
    ].join("");
  } else if (action === "create_story") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("title", '<input type="text" name="title" required>'),
      field("initial status", selectHtml("status", STATUS_VOCAB.filter((s) => s !== "done"), "backlog")),
    ].join("");
  } else if (action === "update_story_status") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("story", selectHtml("story", stories)),
      field("new status", selectHtml("status", STATUS_VOCAB)),
      field("evidence body (required for done when no evidence exists)",
        '<textarea name="evidence_body" placeholder="- proof line…"></textarea>'),
      `<div class="checkline"><input type="checkbox" name="force" id="f-force">
        <label for="f-force">force: replace existing evidence</label></div>`,
    ].join("");
  } else if (action === "attach_evidence") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("story", selectHtml("story", stories)),
      field("evidence body", '<textarea name="body" placeholder="- proof line…"></textarea>'),
      `<div class="checkline"><input type="checkbox" name="force" id="f-force">
        <label for="f-force">force: replace existing evidence</label></div>`,
    ].join("");
  } else if (action === "close_phase") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("final summary body", '<textarea name="summary_body" placeholder="## Outcome vs exit criteria…"></textarea>'),
      `<div class="checkline"><input type="checkbox" name="force" id="f-force">
        <label for="f-force">force: close with open stories / replace an existing summary (core force semantics)</label></div>`,
    ].join("");
  }

  app.innerHTML = `
    <div class="tabs">${tabs}</div>
    ${guarded ? `<div class="guard">mutations guarded — <a href="#/health">${proj.issue_count} validation issue${proj.issue_count === 1 ? "" : "s"}</a>.
      Preview requires explicit acknowledgment below.</div>` : ""}
    <form class="edit" id="edit-form">
      ${field("project", selectHtml("project", projects.map((x) => x.slug), proj.slug))}
      ${formFields}
      ${guarded ? `<div class="checkline"><input type="checkbox" name="acknowledge_issues" id="f-ack">
        <label for="f-ack">I acknowledge the validation issues and still want a preview</label></div>` : ""}
      <button type="submit">preview — no files are written</button>
      <div class="hint">Preview shows exact diffs, projected validation, and a fingerprint;
        apply refuses stale previews and never commits — committing stays with you.</div>
    </form>
    <div id="preview-out"></div>`;

  const editForm = document.getElementById("edit-form");
  async function runEditPreview(form) {
    const out = document.getElementById("preview-out");
    const body = { kind: action };
    for (const el of form.elements) {
      if (!el.name) continue;
      if (el.type === "checkbox") body[el.name] = el.checked;
      else body[el.name] = el.value.trim();
    }
    // client-side refusals before the server's authoritative ones
    if (action === "update_story_status" && body.status === "done" && !body.evidence_body) {
      const st = phases.flatMap((ph) => ph.stories).find((s) => s.story_id === body.story);
      if (st && !st.evidence_exists) {
        out.innerHTML = `<div class="guard">refused client-side: marking ${esc(body.story)} done requires
          evidence — none exists and no evidence body was provided.</div>`;
        return;
      }
    }
    out.innerHTML = stateHtml("Previewing…");
    try {
      const { status, body: payload } = await postJson("/api/mutations/preview", body);
      if (status >= 400 || payload.ok === false) {
        const msg = (payload.data && payload.data.error) || (payload.issues && payload.issues[0]) || `error ${status}`;
        out.innerHTML = `<div class="guard">${esc(msg)}</div>` +
          (payload.data && payload.data.issues
            ? `<ul class="plain">${payload.data.issues.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul>` : "");
        return;
      }
      const d = payload.data;
      out.innerHTML = `
        <div class="section"><h2>Preview — ${esc(d.kind)} ${badge("nothing written yet", "ok")}
          ${d.no_op ? badge("no-op: repeating this mutation changes nothing", "warn") : ""}</h2>
          <div class="meta">
            ${Object.entries(d.summary).map(([k, v]) =>
              `<div class="kv"><div class="k">${esc(k)}</div><div class="v">${esc(String(v))}</div></div>`).join("")}
            <div class="kv"><div class="k">fingerprint</div><div class="v">${esc(d.fingerprint.slice(0, 24))}…</div></div>
          </div>
          ${d.issues_before && d.issues_before.length ? `<div class="section"><h2>Validation before write</h2>
            <ul class="plain">${d.issues_before.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul></div>` : ""}
          ${d.issues_after === null ? `<p class="hint">projected post-write validation unavailable</p>`
            : d.issues_after.length ? `<div class="section"><h2>Projected validation after write</h2>
            <ul class="plain">${d.issues_after.map((i) => `<li class="warn">${esc(i)}</li>`).join("")}</ul></div>`
            : `<p class="hint">projected post-write validation: clean</p>`}
          ${d.create_dirs.length ? `<p class="hint">creates directory: <code>${d.create_dirs.map(esc).join(", ")}</code></p>` : ""}
          ${d.files.map((f) => `
            <details class="filepreview" ${f.changed ? "open" : ""}>
              <summary>${badge(f.action === "create" ? "new file" : f.changed ? "changed" : "unchanged (owned)",
                  f.action === "create" ? "ok" : f.changed ? "in-progress" : "warn")}
                <code>${esc(f.path)}</code>
                <span class="hint">${f.bytes_before} → ${f.bytes_after} bytes</span></summary>
              ${f.action === "create"
                ? `<pre class="src">${esc(f.new_content || "")}</pre>`
                : f.diff ? `<pre class="diff">${diffHtml(f.diff)}</pre>` : `<pre class="src">${esc(f.new_content || "")}</pre>`}
            </details>`).join("")}
          <button type="button" class="applybtn" id="apply-btn">apply — writes the files above (no commit)</button>
        </div>`;
      document.getElementById("apply-btn").addEventListener("click", async () => {
        out.querySelector("#apply-btn").disabled = true;
        const { status: st, body: applied } = await postJson("/api/mutations/apply", { ...body, fingerprint: d.fingerprint });
        const resultBox = document.createElement("div");
        if (st === 409) {
          resultBox.innerHTML = `<div class="guard">stale preview refused — the source files changed after this
            preview was taken; nothing was written. Re-run the preview for a fresh fingerprint.</div>`;
        } else if (st >= 400 || applied.ok === false) {
          const msg = (applied.data && applied.data.error) || `apply failed (${st})`;
          resultBox.innerHTML = `<div class="guard">${esc(msg)}${applied.data && applied.data.rolled_back
            ? " — all writes were rolled back" : ""}</div>`;
        } else {
          const r = applied.data;
          resultBox.innerHTML = `
            <div class="guard ok">applied: ${r.changed.length} file${r.changed.length === 1 ? "" : "s"} written (no commit made)</div>
            <div class="section"><h2>Post-apply revalidation</h2>
              ${r.issues.length ? `<ul class="plain">${r.issues.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul>`
                : `<p class="hint">dw check: clean — <a href="#/p/${encodeURIComponent(body.project)}">view the refreshed project</a></p>`}
              <ul class="plain">${r.changed.map((c) => `<li><a href="#/f/${encodeURIComponent(c)}"><code>${esc(c)}</code></a></li>`).join("")}</ul>
            </div>`;
        }
        out.appendChild(resultBox);
      });
    } catch (err) {
      out.innerHTML = `<div class="guard">${esc(err.message)}</div>`;
    }
  }

  editForm.addEventListener("submit", (e) => {
    e.preventDefault();
    runEditPreview(e.target);
  });
  // Screenshot affordance: ?snapshot=1&autopreview=1 runs the preview
  // with the form defaults inside this synchronous load chain so
  // headless capture sees the rendered result. Not for interactive use.
  if (SNAPSHOT_MODE && new URLSearchParams(location.search).has("autopreview")) {
    await runEditPreview(editForm);
  }
}

/* ── router ─────────────────────────────────────────────────────────── */

async function route() {
  stopMcPoll(); // leaving mission control stops its poll
  app.innerHTML = stateHtml("Loading…");
  const hash = decodeURIComponent(location.hash.replace(/^#/, "")) || "/";
  const parts = hash.split("/").filter(Boolean);
  try {
    if (!parts.length) return await viewOverview();
    if (parts[0] === "p" && parts.length === 2) return await viewProject(parts[1]);
    if (parts[0] === "p" && parts[2] === "ph") return await viewPhase(parts[1], parts[3]);
    if (parts[0] === "p" && parts[2] === "s") return await viewStory(parts[1], parts[3]);
    if (parts[0] === "p" && parts[2] === "t") return await viewTrace(parts[1], parts[3]);
    if (parts[0] === "wl") return await viewWorklog(parts.slice(1).join("/"));
    if (parts[0] === "edit") return await viewEdit(parts[1]);
    if (parts[0] === "health") return await viewHealth();
    if (parts[0] === "mc") return await viewMissionControl();
    if (parts[0] === "f") return await viewFile(parts.slice(1).join("/"));
    app.innerHTML = stateHtml(`Unknown view: ${hash}`, true);
  } catch (err) {
    app.innerHTML = stateHtml(err.message, true);
  }
}

document.getElementById("refresh-btn").addEventListener("click", route);
window.addEventListener("hashchange", route);

api("/api/context").then((body) => {
  footRoot.textContent = body.data.root;
}).catch(() => {});
route();
