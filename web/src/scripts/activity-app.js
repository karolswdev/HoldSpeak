    <script>
      const state = {
        status: null,
        activity: null,
        projects: [],
        rules: [],
        candidatePreviews: [],
        meetingCandidates: [],
        candidateStatusFilter: "",
        connectors: [],
      };
      const $ = (id) => document.getElementById(id);

      async function request(path, options = {}) {
        const response = await fetch(path, {
          headers: { "Content-Type": "application/json", ...(options.headers || {}) },
          ...options,
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || response.statusText);
        return payload;
      }

      function setMessage(text, isError = false) {
        $("message").textContent = isError ? "" : text;
        $("error").textContent = isError ? text : "";
      }

      function setPanelMessage(id, text, isError = false) {
        const el = $(id);
        el.textContent = text || "";
        el.classList.toggle("error", Boolean(isError));
      }

      async function withButtonBusy(button, action) {
        if (button) button.disabled = true;
        try {
          return await action();
        } finally {
          if (button) button.disabled = false;
        }
      }

      function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, (char) => ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        }[char]));
      }

      function renderStatus() {
        const status = state.status || {};
        const settings = status.settings || { enabled: true, retention_days: 30 };
        const pill = $("enabled-pill");
        pill.textContent = settings.enabled ? "Enabled" : "Paused";
        pill.classList.toggle("paused", !settings.enabled);
        $("toggle-enabled").textContent = settings.enabled ? "Pause" : "Resume";
        $("record-count").textContent = String(status.record_count || 0);
        $("retention-value").textContent = String(settings.retention_days || 30);
        $("retention-input").value = String(settings.retention_days || 30);

        const sources = status.sources || [];
        $("sources").innerHTML = sources.length
          ? sources.map((source) => `
              <div class="row">
                <span class="label">${escapeHtml(source.source_browser)} / ${escapeHtml(source.source_profile)}</span>
                <span class="value">${source.enabled ? "enabled" : "paused"}</span>
              </div>
            `).join("")
          : `<div class="empty">No readable browser sources found.</div>`;

        const rules = (status.domain_rules || []).filter((rule) => rule.action === "exclude");
        $("domains").innerHTML = rules.length
          ? rules.map((rule) => `
              <div class="row">
                <span class="label">${escapeHtml(rule.domain)}</span>
                <button type="button" data-remove-domain="${escapeHtml(rule.domain)}">Remove</button>
              </div>
            `).join("")
          : `<div class="empty"><strong>No excluded domains.</strong>Add a domain above to keep matching local activity out of the ledger.</div>`;
      }

      function renderProjects() {
        $("rule-project").innerHTML = state.projects.length
          ? state.projects.map((project) => `
              <option value="${escapeHtml(project.id)}">${escapeHtml(project.name)}</option>
            `).join("")
          : `<option value="">No projects</option>`;
      }

      function renderRules() {
        $("rules").innerHTML = state.rules.length
          ? state.rules.map((rule) => `
              <article class="rule-item">
                <div class="record-top">
                  <div>
                    <div class="record-title">${escapeHtml(rule.name || rule.pattern)}</div>
                    <div class="record-meta">
                      ${escapeHtml(rule.project_name || rule.project_id)} · ${escapeHtml(rule.match_type)} · ${escapeHtml(rule.pattern)}
                      ${rule.entity_type ? ` · ${escapeHtml(rule.entity_type)}` : ""}
                    </div>
                  </div>
                  <div class="tag">${rule.enabled ? "enabled" : "off"} · ${Number(rule.priority || 0)}</div>
                </div>
                <div class="rule-actions">
                  <button type="button" data-edit-rule="${escapeHtml(rule.id)}">Edit</button>
                  <button class="danger" type="button" data-delete-rule="${escapeHtml(rule.id)}">Delete</button>
                </div>
              </article>
            `).join("")
          : `<div class="empty"><strong>No project rules yet.</strong>Create a rule to attach matching local activity to a known project.</div>`;
      }

      function renderRecords() {
        const records = (state.activity && state.activity.records) || [];
        $("records").innerHTML = records.length
          ? records.map((record) => `
              <article class="record">
                <div class="record-top">
                  <div class="record-title">${escapeHtml(record.title || record.url)}</div>
                  <div class="tag">${escapeHtml(record.project_id || record.entity_type || "domain")}</div>
                </div>
                <div class="record-meta">
                  ${escapeHtml(record.entity_id || record.domain)} · ${escapeHtml(record.source_browser)} · visits ${Number(record.visit_count || 0)}
                  <br />
                  ${escapeHtml(record.last_seen_at || "no timestamp")} · ${escapeHtml(record.url)}
                </div>
              </article>
            `).join("")
          : `<div class="empty"><strong>No imported activity yet.</strong>Use Refresh after enabling a readable browser source, or keep ingestion paused if you do not want local activity imported.</div>`;
      }

      function renderCandidatePreviews() {
        const previews = state.candidatePreviews || [];
        $("candidate-preview").innerHTML = previews.length
          ? previews.map((candidate, index) => `
              <article class="rule-item candidate-preview-item">
                <div class="record-top">
                  <div>
                    <div class="record-title">${escapeHtml(candidate.title)}</div>
                    <div class="record-meta">
                      ${escapeHtml(candidate.source_connector_id)} · confidence ${Number(candidate.confidence || 0).toFixed(2)}
                      <br />
                      ${escapeHtml(candidate.meeting_url || "")}
                    </div>
                  </div>
                  <div class="tag">preview</div>
                </div>
                <div class="rule-actions">
                  <button type="button" data-save-candidate="${index}">Save</button>
                </div>
              </article>
            `).join("")
          : `<div class="empty"><strong>No preview loaded.</strong>Preview scans imported local calendar activity without saving or starting a recording.</div>`;
      }

      function renderMeetingCandidates() {
        const candidates = state.meetingCandidates || [];
        const filterLabel = state.candidateStatusFilter || "all";
        $("meeting-candidates").innerHTML = candidates.length
          ? candidates.map((candidate) => `
              <article class="rule-item candidate-saved-item">
                <div class="record-top">
                  <div>
                    <div class="record-title">${escapeHtml(candidate.title)}</div>
                    <div class="record-meta">
                      ${escapeHtml(candidate.source_connector_id)} · confidence ${Number(candidate.confidence || 0).toFixed(2)}
                      <br />
                      ${escapeHtml(candidate.meeting_url || "")}
                      ${candidate.started_meeting_id ? `<br />started meeting ${escapeHtml(candidate.started_meeting_id)}` : ""}
                    </div>
                  </div>
                  <div class="tag">${escapeHtml(candidate.status)}</div>
                </div>
                <div class="rule-actions">
                  <button class="primary" type="button" data-start-candidate="${escapeHtml(candidate.id)}" ${candidate.status === "started" ? "disabled" : ""}>Start</button>
                  <button type="button" data-candidate-status="armed" data-candidate-id="${escapeHtml(candidate.id)}" ${candidate.status === "armed" ? "disabled" : ""}>Arm</button>
                  <button type="button" data-candidate-status="dismissed" data-candidate-id="${escapeHtml(candidate.id)}" ${candidate.status === "dismissed" ? "disabled" : ""}>Dismiss</button>
                  <button type="button" data-candidate-status="candidate" data-candidate-id="${escapeHtml(candidate.id)}" ${candidate.status === "candidate" ? "disabled" : ""}>Reset</button>
                </div>
              </article>
            `).join("")
          : `<div class="empty"><strong>No ${escapeHtml(filterLabel)} saved candidates.</strong>Preview local calendar activity, save a candidate, then start it manually when you are ready to record.</div>`;
      }

      function resetRuleForm() {
        $("rule-id").value = "";
        $("rule-name").value = "";
        $("rule-pattern").value = "";
        $("rule-entity-type").value = "";
        $("rule-priority").value = "100";
        $("rule-enabled").checked = true;
        $("rule-match-type").value = "domain";
        $("rule-preview").innerHTML = "";
      }

      function rulePayload() {
        return {
          project_id: $("rule-project").value,
          name: $("rule-name").value.trim(),
          match_type: $("rule-match-type").value,
          pattern: $("rule-pattern").value.trim(),
          entity_type: $("rule-entity-type").value.trim() || null,
          priority: Number($("rule-priority").value || 100),
          enabled: $("rule-enabled").checked,
        };
      }

      function editRule(rule) {
        $("rule-id").value = rule.id;
        $("rule-project").value = rule.project_id;
        $("rule-name").value = rule.name || "";
        $("rule-match-type").value = rule.match_type;
        $("rule-pattern").value = rule.pattern;
        $("rule-entity-type").value = rule.entity_type || "";
        $("rule-priority").value = String(rule.priority || 100);
        $("rule-enabled").checked = Boolean(rule.enabled);
        $("rule-preview").innerHTML = "";
      }

      function renderPreview(matches) {
        $("rule-preview").innerHTML = matches.length
          ? matches.slice(0, 8).map((record) => `
              <article class="rule-item">
                <div class="record-title">${escapeHtml(record.title || record.url)}</div>
                <div class="record-meta">${escapeHtml(record.entity_id || record.domain)} · ${escapeHtml(record.url)}</div>
              </article>
            `).join("")
          : `<div class="empty">No matches.</div>`;
      }

      async function load() {
        try {
          const [status, activity, projects, rules, candidates, connectors] = await Promise.all([
            request("/api/activity/status"),
            request("/api/activity/records?limit=100"),
            request("/api/projects"),
            request("/api/activity/project-rules"),
            request(`/api/activity/meeting-candidates${state.candidateStatusFilter ? `?status=${encodeURIComponent(state.candidateStatusFilter)}` : ""}`),
            request("/api/activity/enrichment/connectors"),
          ]);
          state.status = status;
          state.activity = activity;
          state.projects = projects.projects || [];
          state.rules = rules.rules || [];
          state.meetingCandidates = candidates.candidates || [];
          state.connectors = connectors.connectors || [];
          renderStatus();
          renderProjects();
          renderRules();
          renderCandidatePreviews();
          renderMeetingCandidates();
          renderRecords();
          renderConnectors();
          setMessage("");
          setPanelMessage("rules-message", "");
          setPanelMessage("candidates-message", "");
          setPanelMessage("domains-message", "");
          setPanelMessage("connectors-message", "");
        } catch (error) {
          setMessage(error.message, true);
        }
      }

      function renderConnectors() {
        const list = $("connectors");
        const connectors = state.connectors || [];
        if (!connectors.length) {
          list.innerHTML = `<div class="empty">No connectors registered.</div>`;
          return;
        }
        list.innerHTML = connectors.map((c) => {
          const enabled = !!c.enabled;
          const requiresCli = c.requires_cli || null;
          const cliStatus = c.cli_status || null;
          const cliAvailable = cliStatus ? !!cliStatus.available : true;
          const cliPath = cliStatus && cliStatus.command_path ? cliStatus.command_path : "";
          const lastRun = c.last_run_at ? new Date(c.last_run_at).toLocaleString() : "never";
          const capabilities = (c.capabilities || []).join(", ") || "—";
          const cliPill = requiresCli
            ? `<span class="pill ${cliAvailable ? "pill--success" : "pill--warn"}"><span class="pill-dot"></span>${cliAvailable ? `${escapeHtml(requiresCli)} ready` : `${escapeHtml(requiresCli)} not found`}</span>`
            : "";
          const enabledPill = enabled
            ? `<span class="pill pill--info"><span class="pill-dot"></span>enabled</span>`
            : `<span class="pill pill--neutral"><span class="pill-dot"></span>disabled</span>`;
          const errorBlock = c.last_error
            ? `<p class="connector-error" role="alert">Last run: ${escapeHtml(c.last_error)}</p>`
            : "";
          const caps = c.capabilities || [];
          const actions = [];
          if (caps.includes("annotations")) {
            actions.push(`<button class="btn btn--ghost btn--sm danger" type="button" data-clear-annotations="${escapeHtml(c.id)}">Clear annotations</button>`);
          }
          if (caps.includes("candidates")) {
            actions.push(`<button class="btn btn--ghost btn--sm danger" type="button" data-clear-candidates="${escapeHtml(c.id)}">Clear candidates</button>`);
          }
          return `
            <article class="connector-card${enabled ? "" : " is-disabled"}${c.last_error ? " has-error" : ""}" data-connector-id="${escapeHtml(c.id)}">
              <div class="connector-head">
                <div class="connector-head-left">
                  <span class="connector-title">${escapeHtml(c.label || c.id)}</span>
                  <span class="connector-id">${escapeHtml(c.id)}</span>
                  ${enabledPill}
                  ${cliPill}
                </div>
                <div class="connector-actions">
                  <button class="btn ${enabled ? "btn--ghost" : "btn--secondary"} btn--sm" type="button" data-toggle-connector="${escapeHtml(c.id)}">${enabled ? "Disable" : "Enable"}</button>
                </div>
              </div>
              ${c.description ? `<p class="connector-body">${escapeHtml(c.description)}</p>` : ""}
              <p class="connector-meta">Capabilities: ${escapeHtml(capabilities)} · Last run: ${escapeHtml(lastRun)}${cliPath ? ` · CLI: <code>${escapeHtml(cliPath)}</code>` : ""}</p>
              ${errorBlock}
              ${actions.length ? `<div class="connector-actions">${actions.join("")}</div>` : ""}
            </article>
          `;
        }).join("");
      }


      $("toggle-enabled").addEventListener("click", async () => {
        const button = $("toggle-enabled");
        const enabled = !(state.status && state.status.settings && state.status.settings.enabled);
        await withButtonBusy(button, async () => {
          try {
            const payload = await request("/api/activity/settings", {
              method: "PUT",
              body: JSON.stringify({ enabled }),
            });
            state.status = payload.status;
            renderStatus();
            setMessage(enabled ? "Activity ingestion resumed." : "Activity ingestion paused.");
          } catch (error) {
            setMessage(error.message, true);
          }
        });
      });

      $("refresh").addEventListener("click", async () => {
        const button = $("refresh");
        await withButtonBusy(button, async () => {
          try {
            await request("/api/activity/refresh", { method: "POST", body: "{}" });
            setMessage("Activity refreshed.");
            await load();
          } catch (error) {
            setMessage(error.message, true);
          }
        });
      });

      $("clear").addEventListener("click", async () => {
        const ok = await window.holdspeakConfirm({
          title: "Delete imported activity records?",
          body: "This permanently removes the locally imported browser-history records HoldSpeak has indexed for the work-context ledger. The next refresh will re-import from your browser history.",
          scopeNote: "Only the local HoldSpeak ledger is affected. Your browser's own history is not touched.",
          confirmLabel: "Delete records",
        });
        if (!ok) return;
        const button = $("clear");
        await withButtonBusy(button, async () => {
          try {
            await request("/api/activity/records", { method: "DELETE" });
            setMessage("Imported activity cleared.");
            await load();
          } catch (error) {
            setMessage(error.message, true);
          }
        });
      });

      $("save-retention").addEventListener("click", async () => {
        const button = $("save-retention");
        await withButtonBusy(button, async () => {
          try {
            const retention_days = Number($("retention-input").value || 30);
            const payload = await request("/api/activity/settings", {
              method: "PUT",
              body: JSON.stringify({ retention_days }),
            });
            state.status = payload.status;
            renderStatus();
            setMessage("Retention saved.");
          } catch (error) {
            setMessage(error.message, true);
          }
        });
      });

      $("exclude-domain").addEventListener("click", async () => {
        const button = $("exclude-domain");
        const domain = $("domain-input").value.trim();
        if (!domain) return;
        await withButtonBusy(button, async () => {
          try {
            const payload = await request("/api/activity/domains", {
              method: "POST",
              body: JSON.stringify({ domain, action: "exclude" }),
            });
            state.status = payload.status;
            $("domain-input").value = "";
            renderStatus();
            setPanelMessage("domains-message", `${domain} excluded.`);
          } catch (error) {
            setPanelMessage("domains-message", error.message, true);
          }
        });
      });

      $("domains").addEventListener("click", async (event) => {
        const button = event.target.closest("[data-remove-domain]");
        if (!button) return;
        const domain = button.getAttribute("data-remove-domain");
        const ok = await window.holdspeakConfirm({
          title: `Remove ${domain} from the exclude list?`,
          body: `Future activity from ${domain} will be re-imported into the local ledger on the next refresh.`,
          confirmLabel: "Remove",
          danger: false,
        });
        if (!ok) return;
        await withButtonBusy(button, async () => {
          try {
            const payload = await request(`/api/activity/domains/${encodeURIComponent(domain)}`, { method: "DELETE" });
            state.status = payload.status;
            renderStatus();
            setPanelMessage("domains-message", `${domain} removed.`);
          } catch (error) {
            setPanelMessage("domains-message", error.message, true);
          }
        });
      });

      $("preview-rule").addEventListener("click", async () => {
        const button = $("preview-rule");
        await withButtonBusy(button, async () => {
          try {
            const payload = await request("/api/activity/project-rules/preview", {
              method: "POST",
              body: JSON.stringify(rulePayload()),
            });
            renderPreview(payload.matches || []);
            setPanelMessage("rules-message", `${payload.count || 0} matching records.`);
          } catch (error) {
            setPanelMessage("rules-message", error.message, true);
          }
        });
      });

      $("save-rule").addEventListener("click", async () => {
        const button = $("save-rule");
        await withButtonBusy(button, async () => {
          try {
            const id = $("rule-id").value;
            const payload = await request(
              id ? `/api/activity/project-rules/${encodeURIComponent(id)}` : "/api/activity/project-rules",
              {
                method: id ? "PUT" : "POST",
                body: JSON.stringify(rulePayload()),
              },
            );
            const saved = payload.rule;
            await load();
            editRule(saved);
            setPanelMessage("rules-message", "Project rule saved.");
          } catch (error) {
            setPanelMessage("rules-message", error.message, true);
          }
        });
      });

      $("reset-rule").addEventListener("click", () => {
        resetRuleForm();
        setMessage("");
      });

      $("apply-rules").addEventListener("click", async () => {
        const button = $("apply-rules");
        await withButtonBusy(button, async () => {
          try {
            const payload = await request("/api/activity/project-rules/apply", {
              method: "POST",
              body: "{}",
            });
            setPanelMessage("rules-message", `${payload.updated || 0} records updated.`);
            await load();
          } catch (error) {
            setPanelMessage("rules-message", error.message, true);
          }
        });
      });

      $("rules").addEventListener("click", async (event) => {
        const edit = event.target.closest("[data-edit-rule]");
        const remove = event.target.closest("[data-delete-rule]");
        if (edit) {
          const id = edit.getAttribute("data-edit-rule");
          const rule = state.rules.find((item) => item.id === id);
          if (rule) editRule(rule);
          return;
        }
        if (!remove) return;
        const id = remove.getAttribute("data-delete-rule");
        const ok = await window.holdspeakConfirm({
          title: `Delete project rule "${id}"?`,
          body: "The rule will no longer match incoming activity. Records previously matched by this rule keep the project they were already attached to.",
          scopeNote: "Only the local activity ledger is affected.",
          confirmLabel: "Delete rule",
        });
        if (!ok) return;
        await withButtonBusy(remove, async () => {
          try {
            await request(`/api/activity/project-rules/${encodeURIComponent(id)}`, { method: "DELETE" });
            resetRuleForm();
            setPanelMessage("rules-message", "Project rule deleted.");
            await load();
          } catch (error) {
            setPanelMessage("rules-message", error.message, true);
          }
        });
      });

      $("preview-candidates").addEventListener("click", async () => {
        const button = $("preview-candidates");
        await withButtonBusy(button, async () => {
          try {
            const payload = await request("/api/activity/meeting-candidates/preview");
            state.candidatePreviews = payload.candidates || [];
            renderCandidatePreviews();
            setPanelMessage("candidates-message", `${payload.count || 0} meeting candidates found.`);
          } catch (error) {
            setPanelMessage("candidates-message", error.message, true);
          }
        });
      });

      $("refresh-candidates").addEventListener("click", async () => {
        const button = $("refresh-candidates");
        await withButtonBusy(button, async () => {
          try {
            const path = `/api/activity/meeting-candidates${state.candidateStatusFilter ? `?status=${encodeURIComponent(state.candidateStatusFilter)}` : ""}`;
            const payload = await request(path);
            state.meetingCandidates = payload.candidates || [];
            renderMeetingCandidates();
            setPanelMessage("candidates-message", `${payload.count || 0} saved meeting candidates.`);
          } catch (error) {
            setPanelMessage("candidates-message", error.message, true);
          }
        });
      });

      $("candidate-status-filter").addEventListener("change", async () => {
        state.candidateStatusFilter = $("candidate-status-filter").value;
        setPanelMessage("candidates-message", "");
        await load();
      });

      $("candidate-preview").addEventListener("click", async (event) => {
        const button = event.target.closest("[data-save-candidate]");
        if (!button) return;
        const candidate = state.candidatePreviews[Number(button.getAttribute("data-save-candidate"))];
        if (!candidate) return;
        await withButtonBusy(button, async () => {
          try {
            await request("/api/activity/meeting-candidates", {
              method: "POST",
              body: JSON.stringify({
                source_connector_id: candidate.source_connector_id,
                source_activity_record_id: candidate.source_activity_record_id,
                title: candidate.title,
                starts_at: candidate.starts_at,
                ends_at: candidate.ends_at,
                meeting_url: candidate.meeting_url,
                confidence: candidate.confidence,
              }),
            });
            setPanelMessage("candidates-message", "Meeting candidate saved.");
            await load();
          } catch (error) {
            setPanelMessage("candidates-message", error.message, true);
          }
        });
      });

      $("meeting-candidates").addEventListener("click", async (event) => {
        const startButton = event.target.closest("[data-start-candidate]");
        if (startButton) {
          if (startButton.disabled) return;
          const id = startButton.getAttribute("data-start-candidate");
          await withButtonBusy(startButton, async () => {
            try {
              const payload = await request(`/api/activity/meeting-candidates/${encodeURIComponent(id)}/start`, {
                method: "POST",
              });
              const meetingId = payload.meeting && payload.meeting.id ? ` (${payload.meeting.id})` : "";
              setPanelMessage("candidates-message", `Meeting started from candidate${meetingId}.`);
              await load();
            } catch (error) {
              setPanelMessage("candidates-message", error.message, true);
            }
          });
          return;
        }

        const statusButton = event.target.closest("[data-candidate-status]");
        if (!statusButton) return;
        if (statusButton.disabled) return;
        const id = statusButton.getAttribute("data-candidate-id");
        const status = statusButton.getAttribute("data-candidate-status");
        await withButtonBusy(statusButton, async () => {
          try {
            await request(`/api/activity/meeting-candidates/${encodeURIComponent(id)}/status`, {
              method: "PUT",
              body: JSON.stringify({ status }),
            });
            setPanelMessage("candidates-message", `Meeting candidate marked ${status}.`);
            await load();
          } catch (error) {
            setPanelMessage("candidates-message", error.message, true);
          }
        });
      });

      $("clear-dismissed-candidates").addEventListener("click", async () => {
        const ok = await window.holdspeakConfirm({
          title: "Clear dismissed meeting candidates?",
          body: "Permanently removes every previously dismissed meeting candidate from the local activity ledger. The connectors that produced them are not affected — re-running them may re-surface candidates from the same source data.",
          scopeNote: "Only HoldSpeak's local candidate list is affected. The underlying connector data and any source systems (GitHub, Jira, etc.) are not touched.",
          confirmLabel: "Clear dismissed",
        });
        if (!ok) return;
        const button = $("clear-dismissed-candidates");
        await withButtonBusy(button, async () => {
          try {
            const payload = await request("/api/activity/meeting-candidates?status=dismissed", { method: "DELETE" });
            setPanelMessage("candidates-message", `${payload.deleted || 0} dismissed candidates cleared.`);
            await load();
          } catch (error) {
            setPanelMessage("candidates-message", error.message, true);
          }
        });
      });

      $("connectors").addEventListener("click", async (event) => {
        const toggle = event.target.closest("[data-toggle-connector]");
        const clearAnn = event.target.closest("[data-clear-annotations]");
        const clearCand = event.target.closest("[data-clear-candidates]");

        if (toggle) {
          const id = toggle.getAttribute("data-toggle-connector");
          const connector = (state.connectors || []).find((c) => c.id === id);
          if (!connector) return;
          const nextEnabled = !connector.enabled;
          await withButtonBusy(toggle, async () => {
            try {
              await request(`/api/activity/enrichment/connectors/${encodeURIComponent(id)}`, {
                method: "PUT",
                body: JSON.stringify({ enabled: nextEnabled }),
              });
              setPanelMessage("connectors-message", `${connector.label || id} ${nextEnabled ? "enabled" : "disabled"}.`);
              await load();
            } catch (error) {
              setPanelMessage("connectors-message", error.message, true);
            }
          });
          return;
        }

        if (clearAnn) {
          const id = clearAnn.getAttribute("data-clear-annotations");
          const connector = (state.connectors || []).find((c) => c.id === id);
          const label = (connector && connector.label) || id;
          const ok = await window.holdspeakConfirm({
            title: `Clear local ${label} annotations?`,
            body: `Permanently removes every locally stored annotation produced by the ${label} connector. Source data on the underlying system is not touched.`,
            scopeNote: `Only HoldSpeak's local annotations from ${label} are affected. ${id === "gh" ? "Issues and PRs on GitHub are unchanged." : id === "jira" ? "Tickets in Jira are unchanged." : "External source systems are unchanged."}`,
            confirmLabel: "Clear annotations",
          });
          if (!ok) return;
          await withButtonBusy(clearAnn, async () => {
            try {
              const payload = await request(
                `/api/activity/enrichment/connectors/${encodeURIComponent(id)}/annotations`,
                { method: "DELETE" },
              );
              setPanelMessage("connectors-message", `${payload.deleted || 0} ${label} annotations cleared.`);
              await load();
            } catch (error) {
              setPanelMessage("connectors-message", error.message, true);
            }
          });
          return;
        }

        if (clearCand) {
          const id = clearCand.getAttribute("data-clear-candidates");
          const connector = (state.connectors || []).find((c) => c.id === id);
          const label = (connector && connector.label) || id;
          const ok = await window.holdspeakConfirm({
            title: `Clear local ${label} candidates?`,
            body: `Permanently removes every meeting candidate that was produced by the ${label} connector. Re-running the connector may re-surface candidates from the same source activity.`,
            scopeNote: "Only HoldSpeak's local candidate list is affected.",
            confirmLabel: "Clear candidates",
          });
          if (!ok) return;
          await withButtonBusy(clearCand, async () => {
            try {
              const payload = await request(
                `/api/activity/enrichment/connectors/${encodeURIComponent(id)}/candidates`,
                { method: "DELETE" },
              );
              setPanelMessage("connectors-message", `${payload.deleted || 0} ${label} candidates cleared.`);
              await load();
            } catch (error) {
              setPanelMessage("connectors-message", error.message, true);
            }
          });
          return;
        }
      });

      load();
