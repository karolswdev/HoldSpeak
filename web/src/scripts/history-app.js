function historyApp() {
  return {
    tab: "meetings",
    loading: true,
    loadingActions: true,
    loadingSpeakers: true,
    loadingSpeakerDetail: false,
    loadingIntel: true,
    loadingPluginJobs: true,
    loadingSettings: true,
    meetings: [],
    actionItems: [],
    speakers: [],
    intelJobs: [],
    intelSummary: null,
    pluginJobs: [],
    settings: null,
    searchQuery: "",
    showCompleted: false,
    actionStatusFilter: "pending",
    actionReviewFilter: "pending",
    speakerSearch: "",
    selectedMeeting: null,
    selectedMeetingArtifacts: [],
    selectedSpeakerId: "",
    selectedSpeaker: null,
    speakerDraft: { name: "", avatar: "" },
    intelStatusFilter: "all",
    intelProcessMode: "respect_backoff",
    intelLimit: 20,
    intelMaxJobs: 5,
    pluginJobStatusFilter: "all",
    pluginJobLimit: 20,
    uiMessage: "",
    uiError: false,
    savingSettings: false,
    savingSpeaker: false,
    processingIntel: false,
    processingPluginJobs: false,
    settingsValidationErrors: [],
    clockTick: Date.now(),
    intelFailureAboveSinceMs: null,
    _messageTimer: null,
    _clockTimer: null,

    // Project state
    projects: [],
    loadingProjects: true,
    selectedProject: null,
    showNewProjectForm: false,
    projectDraft: { name: "", description: "", keywords: "", team_members: "", detection_threshold: 0.4 },
    projectSummary: null,
    projectMeetings: [],
    projectActionItems: [],
    projectArtifacts: [],

    async init() {
      await Promise.all([
        this.loadMeetings(),
        this.loadActionItems(),
        this.loadSpeakers(),
        this.loadIntelJobs(),
        this.loadIntelSummary(),
        this.loadPluginJobs(),
        this.loadSettings(),
      ]);
      if (!this._clockTimer) {
        this._clockTimer = setInterval(() => {
          this.clockTick = Date.now();
        }, 1000);
      }
    },

    async apiJson(url, options = {}) {
      const response = await fetch(url, options);
      let data = {};
      try {
        data = await response.json();
      } catch (_error) {
        data = {};
      }
      if (!response.ok) {
        const message = data.error || data.detail || `Request failed (${response.status})`;
        throw new Error(message);
      }
      return data;
    },

    flash(message, isError = false) {
      this.uiMessage = String(message || "").trim();
      this.uiError = Boolean(isError);
      if (this._messageTimer) {
        clearTimeout(this._messageTimer);
      }
      if (!this.uiMessage) return;
      this._messageTimer = setTimeout(() => {
        this.uiMessage = "";
        this.uiError = false;
        this._messageTimer = null;
      }, 3200);
    },

    setTab(name) {
      this.tab = name;
      if (name === "actions") this.loadActionItems();
      if (name === "speakers" && this.speakers.length === 0) this.loadSpeakers();
      if (name === "intel") {
        this.loadIntelJobs();
        this.loadIntelSummary();
        this.loadPluginJobs();
      }
      if (name === "settings" && !this.settings) this.loadSettings();
      if (name === "projects") this.loadProjects();
    },

    intelStatusLabel(state) {
      const value = String(state || "disabled").toLowerCase();
      if (value === "ready") return "Ready";
      if (value === "live") return "Live";
      if (value === "running") return "Running";
      if (value === "queued") return "Queued";
      if (value === "error") return "Unavailable";
      if (value === "disabled") return "Disabled";
      return "Pending";
    },

    reviewStateValue(state) {
      return String(state || "pending").trim().toLowerCase() === "accepted" ? "accepted" : "pending";
    },

    reviewStateLabel(state) {
      return this.reviewStateValue(state) === "accepted" ? "Accepted" : "Needs review";
    },

    intelQueueScheduleLabel(job) {
      // Touch the clock ticker so labels naturally refresh each second.
      void this.clockTick;
      const requested = job?.requested_at ? new Date(job.requested_at) : null;
      if (!requested || Number.isNaN(requested.getTime())) return "Requested --";
      const now = new Date();
      const hasFailure = Boolean(job?.last_error);
      if (String(job?.status || "").toLowerCase() === "queued" && hasFailure && requested > now) {
        const rel = this.formatRelativeFromNow(job.requested_at);
        return rel ? `Retry ${this.formatDate(job.requested_at)} (${rel})` : `Retry ${this.formatDate(job.requested_at)}`;
      }
      return `Requested ${this.formatDate(job.requested_at)}`;
    },

    pluginJobScheduleLabel(job) {
      // Touch the clock ticker so labels naturally refresh each second.
      void this.clockTick;
      const requested = job?.requested_at ? new Date(job.requested_at) : null;
      if (!requested || Number.isNaN(requested.getTime())) return "Retry scheduled";
      const rel = this.formatRelativeFromNow(job.requested_at);
      if (!rel) return `Retry ${this.formatDate(job.requested_at)}`;
      return `Retry ${this.formatDate(job.requested_at)} (${rel})`;
    },

    intelFailureRateLabel() {
      const total = Number(this.intelSummary?.total_jobs || 0);
      if (total <= 0) return "0%";
      const failed = Number(this.intelSummary?.failed_jobs || 0);
      return `${Math.round((failed / total) * 100)}%`;
    },

    intelFailurePercentValue() {
      const total = Number(this.intelSummary?.total_jobs || 0);
      if (total <= 0) return 0;
      const failed = Number(this.intelSummary?.failed_jobs || 0);
      return (failed / total) * 100;
    },

    intelFailureAlertThreshold() {
      const configured = Number(this.settings?.meeting?.intel_retry_failure_alert_percent);
      if (Number.isFinite(configured) && configured >= 0) return configured;
      return 50;
    },

    intelFailureAlertHysteresisMinutes() {
      const configured = Number(this.settings?.meeting?.intel_retry_failure_hysteresis_minutes);
      if (Number.isFinite(configured) && configured >= 0) return configured;
      return 5;
    },

    intelFailureAlertActive() {
      // Touch the clock ticker so alert hysteresis refreshes each second.
      void this.clockTick;
      if (!this.intelSummary) return false;
      if (Number(this.intelSummary.total_jobs || 0) <= 0) {
        this.intelFailureAboveSinceMs = null;
        return false;
      }
      if (this.intelFailurePercentValue() < this.intelFailureAlertThreshold()) {
        this.intelFailureAboveSinceMs = null;
        return false;
      }
      const nowMs = Date.now();
      if (!Number.isFinite(this.intelFailureAboveSinceMs)) {
        this.intelFailureAboveSinceMs = nowMs;
        return false;
      }
      const requiredMs = this.intelFailureAlertHysteresisMinutes() * 60 * 1000;
      return nowMs - Number(this.intelFailureAboveSinceMs) >= requiredMs;
    },

    intelFailureAlertMessage() {
      const threshold = this.intelFailureAlertThreshold();
      const current = this.intelFailurePercentValue().toFixed(1);
      const hysteresis = this.intelFailureAlertHysteresisMinutes();
      return `Intel queue failure rate is ${current}% (threshold ${threshold.toFixed(1)}%, hysteresis ${hysteresis.toFixed(1)}m).`;
    },

    intelNextRetryLabel() {
      const nextRetryAt = this.intelSummary?.next_retry_at;
      if (!nextRetryAt) return "No scheduled retry currently pending.";
      const rel = this.formatRelativeFromNow(nextRetryAt);
      if (!rel) return `Next retry ${this.formatDate(nextRetryAt)}`;
      return `Next retry ${this.formatDate(nextRetryAt)} (${rel}).`;
    },

    intelAttemptOutcomeLabel(event) {
      const value = String(event?.outcome || "").toLowerCase();
      if (value === "scheduled_retry") return "scheduled retry";
      if (value === "terminal_failure") return "terminal failure";
      if (value === "success") return "success";
      return value || "unknown";
    },

    async loadMeetings() {
      this.loading = true;
      try {
        const data = await this.apiJson("/api/meetings");
        this.meetings = data.meetings || [];
      } catch (error) {
        console.error("Failed to load meetings:", error);
        this.meetings = [];
        this.flash(`Meeting list failed: ${error.message}`, true);
      }
      this.loading = false;
    },

    async searchMeetings() {
      if (!this.searchQuery.trim()) {
        return this.loadMeetings();
      }
      this.loading = true;
      try {
        const data = await this.apiJson(`/api/meetings?search=${encodeURIComponent(this.searchQuery)}`);
        this.meetings = data.meetings || [];
      } catch (error) {
        console.error("Failed to search meetings:", error);
        this.meetings = [];
        this.flash(`Search failed: ${error.message}`, true);
      }
      this.loading = false;
    },

    clearSearch() {
      this.searchQuery = "";
      this.loadMeetings();
    },

    async loadActionItems() {
      this.loadingActions = true;
      try {
        const includeCompleted = this.showCompleted || this.actionStatusFilter !== "pending";
        const data = await this.apiJson(`/api/all-action-items?include_completed=${includeCompleted}`);
        let items = data.action_items || [];
        items = this.actionStatusFilter === "all"
          ? items
          : items.filter((item) => item.status === this.actionStatusFilter);
        this.actionItems = this.actionReviewFilter === "all"
          ? items
          : items.filter((item) => this.reviewStateValue(item.review_state) === this.actionReviewFilter);
      } catch (error) {
        console.error("Failed to load action items:", error);
        this.actionItems = [];
        this.flash(`Action list failed: ${error.message}`, true);
      }
      this.loadingActions = false;
    },

    async showOpenActionWork() {
      this.showCompleted = false;
      this.actionStatusFilter = "pending";
      this.actionReviewFilter = "pending";
      await this.loadActionItems();
    },

    actionItemsEmptyMessage() {
      if (this.actionStatusFilter === "pending" && this.actionReviewFilter === "pending") {
        return "No pending action items need review.";
      }
      if (this.actionReviewFilter === "pending") {
        return "No action items need review for these filters.";
      }
      return "No action items found for these filters.";
    },

    async toggleActionStatus(item) {
      const newStatus = item.status === "done" ? "pending" : "done";
      try {
        await this.apiJson(`/api/all-action-items/${item.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: newStatus }),
        });
        await this.loadActionItems();
        this.flash(`Action item marked ${newStatus}.`);
      } catch (error) {
        console.error("Failed to update action item:", error);
        this.flash(`Action update failed: ${error.message}`, true);
      }
    },

    async setActionReviewState(item, reviewState) {
      const normalized = this.reviewStateValue(reviewState);
      try {
        await this.apiJson(`/api/all-action-items/${item.id}/review`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ review_state: normalized }),
        });
        await this.loadActionItems();
        if (this.selectedMeeting && this.selectedMeeting.id === item.meeting_id) {
          await this.openMeeting(item.meeting_id);
        }
        if (this.selectedProject) {
          await this.refreshProjectActionItems();
        }
        this.flash(normalized === "accepted" ? "Action item accepted." : "Action item marked needs review.");
      } catch (error) {
        console.error("Failed to update action item review state:", error);
        this.flash(`Review update failed: ${error.message}`, true);
      }
    },

    async acceptActionItem(item) {
      return this.setActionReviewState(item, "accepted");
    },

    async editActionItem(item) {
      const initialTask = String(item.task || "");
      const task = window.prompt("Edit task", initialTask);
      if (task === null) return;
      const cleanTask = task.trim();
      if (!cleanTask) {
        this.flash("Task cannot be empty.", true);
        return;
      }

      const owner = window.prompt("Owner (leave blank to clear)", item.owner || "");
      if (owner === null) return;
      const due = window.prompt("Due (leave blank to clear)", item.due || "");
      if (due === null) return;

      try {
        await this.apiJson(`/api/all-action-items/${item.id}/edit`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            task: cleanTask,
            owner: owner.trim(),
            due: due.trim(),
          }),
        });
        await this.loadActionItems();
        if (this.selectedMeeting && this.selectedMeeting.id === item.meeting_id) {
          await this.openMeeting(item.meeting_id);
        }
        if (this.selectedProject) {
          await this.refreshProjectActionItems();
        }
        this.flash("Action item edited and accepted.");
      } catch (error) {
        console.error("Failed to edit action item:", error);
        this.flash(`Edit failed: ${error.message}`, true);
      }
    },

    async openMeeting(id) {
      try {
        this.tab = "meetings";
        this.selectedMeetingArtifacts = [];
        this.selectedMeeting = await this.apiJson(`/api/meetings/${id}`);
        try {
          const artifacts = await this.apiJson(`/api/meetings/${id}/artifacts`);
          this.selectedMeetingArtifacts = artifacts.artifacts || [];
        } catch (artifactError) {
          console.error("Failed to load meeting artifacts:", artifactError);
          this.selectedMeetingArtifacts = [];
        }
      } catch (error) {
        console.error("Failed to load meeting:", error);
        this.flash(`Meeting detail failed: ${error.message}`, true);
      }
    },

    downloadSelectedMeetingExport(format) {
      if (!this.selectedMeeting?.id) return;
      const normalized = format === "json" ? "json" : "markdown";
      const extension = normalized === "json" ? "json" : "md";
      const meetingId = String(this.selectedMeeting.id);
      const link = document.createElement("a");
      link.href = `/api/meetings/${encodeURIComponent(meetingId)}/export?format=${normalized}`;
      link.download = `holdspeak-meeting-${meetingId}.${extension}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      this.flash(`Local ${normalized} handoff export started.`);
    },

    async loadSpeakers() {
      this.loadingSpeakers = true;
      try {
        const data = await this.apiJson("/api/speakers");
        this.speakers = data.speakers || [];
      } catch (error) {
        console.error("Failed to load speakers:", error);
        this.speakers = [];
        this.flash(`Speaker list failed: ${error.message}`, true);
      }
      this.loadingSpeakers = false;
    },

    filteredSpeakers() {
      const needle = this.speakerSearch.trim().toLowerCase();
      if (!needle) return this.speakers;
      return this.speakers.filter((speaker) => {
        const candidate = `${speaker.name || ""} ${speaker.avatar || ""}`.toLowerCase();
        return candidate.includes(needle);
      });
    },

    async openSpeaker(speakerId) {
      this.selectedSpeakerId = speakerId;
      this.loadingSpeakerDetail = true;
      try {
        this.selectedSpeaker = await this.apiJson(`/api/speakers/${speakerId}`);
        this.speakerDraft.name = this.selectedSpeaker.speaker?.name || "";
        this.speakerDraft.avatar = this.selectedSpeaker.speaker?.avatar || "";
      } catch (error) {
        console.error("Failed to load speaker:", error);
        this.selectedSpeaker = null;
        this.flash(`Speaker load failed: ${error.message}`, true);
      }
      this.loadingSpeakerDetail = false;
    },

    async saveSpeaker() {
      if (!this.selectedSpeakerId) return;
      this.savingSpeaker = true;
      try {
        await this.apiJson(`/api/speakers/${this.selectedSpeakerId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: this.speakerDraft.name,
            avatar: this.speakerDraft.avatar,
          }),
        });
        await this.loadSpeakers();
        await this.openSpeaker(this.selectedSpeakerId);
        this.flash("Speaker profile saved.");
      } catch (error) {
        console.error("Failed to save speaker:", error);
        this.flash(`Speaker save failed: ${error.message}`, true);
      }
      this.savingSpeaker = false;
    },

    async loadIntelJobs() {
      this.loadingIntel = true;
      try {
        const limit = Number.isFinite(this.intelLimit) && this.intelLimit > 0 ? this.intelLimit : 20;
        const data = await this.apiJson(`/api/intel/jobs?status=${encodeURIComponent(this.intelStatusFilter)}&limit=${limit}&history_limit=5`);
        this.intelJobs = data.jobs || [];
      } catch (error) {
        console.error("Failed to load intel jobs:", error);
        this.intelJobs = [];
        this.flash(`Intel queue load failed: ${error.message}`, true);
      }
      this.loadingIntel = false;
    },

    async loadIntelSummary() {
      try {
        this.intelSummary = await this.apiJson("/api/intel/summary");
      } catch (error) {
        console.error("Failed to load intel summary:", error);
        this.intelSummary = null;
      }
    },

    async loadPluginJobs() {
      this.loadingPluginJobs = true;
      try {
        const limit = Number.isFinite(this.pluginJobLimit) && this.pluginJobLimit > 0 ? this.pluginJobLimit : 20;
        const status = String(this.pluginJobStatusFilter || "all").trim().toLowerCase() || "all";
        const data = await this.apiJson(`/api/plugin-jobs?status=${encodeURIComponent(status)}&limit=${limit}`);
        this.pluginJobs = data.jobs || [];
      } catch (error) {
        console.error("Failed to load plugin jobs:", error);
        this.pluginJobs = [];
        this.flash(`Plugin queue load failed: ${error.message}`, true);
      }
      this.loadingPluginJobs = false;
    },

    async processIntelJobs() {
      this.processingIntel = true;
      try {
        const maxJobs = Number.isFinite(this.intelMaxJobs) && this.intelMaxJobs > 0 ? this.intelMaxJobs : null;
        const data = await this.apiJson("/api/intel/process", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ max_jobs: maxJobs, mode: this.intelProcessMode }),
        });
        await Promise.all([this.loadIntelJobs(), this.loadIntelSummary(), this.loadMeetings()]);
        const modeLabel = data.mode === "retry_now" ? "retry-now" : "respect-backoff";
        this.flash(`Processed ${data.processed || 0} intel job(s) [${modeLabel}].`);
      } catch (error) {
        console.error("Failed to process intel jobs:", error);
        this.flash(`Intel processing failed: ${error.message}`, true);
      }
      this.processingIntel = false;
    },

    async retryIntelJob(meetingId) {
      this.processingIntel = true;
      try {
        await this.apiJson(`/api/intel/retry/${meetingId}`, { method: "POST" });
        await Promise.all([this.loadIntelJobs(), this.loadIntelSummary(), this.loadMeetings()]);
        this.flash("Meeting intelligence requeued.");
      } catch (error) {
        console.error("Failed to retry intel job:", error);
        this.flash(`Retry failed: ${error.message}`, true);
      }
      this.processingIntel = false;
    },

    async retryPluginJob(jobId) {
      this.processingPluginJobs = true;
      try {
        await this.apiJson(`/api/plugin-jobs/${jobId}/retry-now`, { method: "POST" });
        await this.loadPluginJobs();
        this.flash("Plugin job requeued for immediate retry.");
      } catch (error) {
        console.error("Failed to retry plugin job:", error);
        this.flash(`Plugin retry failed: ${error.message}`, true);
      }
      this.processingPluginJobs = false;
    },

    async cancelPluginJob(jobId) {
      this.processingPluginJobs = true;
      try {
        await this.apiJson(`/api/plugin-jobs/${jobId}/cancel`, { method: "POST" });
        await this.loadPluginJobs();
        this.flash("Plugin job canceled.");
      } catch (error) {
        console.error("Failed to cancel plugin job:", error);
        this.flash(`Plugin cancel failed: ${error.message}`, true);
      }
      this.processingPluginJobs = false;
    },

    validateSettingsPayload(payload) {
      const errors = [];
      const hotkey = String(payload?.hotkey?.key || "");
      const model = String(payload?.model?.name || "");
      const ui = payload?.ui || {};
      const meeting = payload?.meeting || {};
      const provider = String(meeting.intel_provider || "").toLowerCase();
      const exportFormat = String(meeting.export_format || "");
      const theme = String(ui.theme || "").toLowerCase();
      const historyLines = Number(ui.history_lines);
      const mirProfile = String(meeting.mir_profile || "").toLowerCase();
      const pollSeconds = Number(meeting.intel_queue_poll_seconds);
      const retryBase = Number(meeting.intel_retry_base_seconds);
      const retryMax = Number(meeting.intel_retry_max_seconds);
      const retryAttempts = Number(meeting.intel_retry_max_attempts);
      const failureAlertPercent = Number(meeting.intel_retry_failure_alert_percent);
      const failureHysteresisMinutes = Number(meeting.intel_retry_failure_hysteresis_minutes);
      const similarity = Number(meeting.similarity_threshold);
      const cloudModel = String(meeting.intel_cloud_model || "").trim();
      const cloudApiEnv = String(meeting.intel_cloud_api_key_env || "").trim();
      const cloudBaseUrl = String(meeting.intel_cloud_base_url || "").trim();
      const failureWebhookUrl = String(meeting.intel_retry_failure_webhook_url || "").trim();
      const failureWebhookHeaderName = String(meeting.intel_retry_failure_webhook_header_name || "").trim();
      const failureWebhookHeaderValue = String(meeting.intel_retry_failure_webhook_header_value || "").trim();

      if (!hotkey) errors.push("Hotkey is required.");
      if (!["tiny", "base", "small", "medium", "large"].includes(model)) {
        errors.push("Model must be one of: tiny, base, small, medium, large.");
      }
      if (!["txt", "markdown", "json", "srt"].includes(exportFormat)) {
        errors.push("Export format must be txt, markdown, json, or srt.");
      }
      if (!["local", "cloud", "auto"].includes(provider)) {
        errors.push("Intel provider must be local, cloud, or auto.");
      }
      if (!["dark", "light", "dracula", "monokai"].includes(theme)) {
        errors.push("Theme must be dark, light, dracula, or monokai.");
      }
      if (!Number.isInteger(historyLines) || historyLines < 1 || historyLines > 100) {
        errors.push("History lines must be an integer between 1 and 100.");
      }
      if (!["balanced", "architect", "delivery", "product", "incident"].includes(mirProfile)) {
        errors.push("MIR profile must be balanced, architect, delivery, product, or incident.");
      }
      if (!Number.isInteger(pollSeconds) || pollSeconds < 5) {
        errors.push("Intel queue poll seconds must be an integer >= 5.");
      }
      if (!Number.isInteger(retryBase) || retryBase < 1) {
        errors.push("Retry base delay must be an integer >= 1 second.");
      }
      if (!Number.isInteger(retryMax) || retryMax < retryBase) {
        errors.push("Retry max delay must be an integer >= retry base delay.");
      }
      if (!Number.isInteger(retryAttempts) || retryAttempts < 1) {
        errors.push("Retry max attempts must be an integer >= 1.");
      }
      if (!Number.isFinite(failureAlertPercent) || failureAlertPercent < 0 || failureAlertPercent > 100) {
        errors.push("Failure alert threshold must be between 0 and 100.");
      }
      if (!Number.isFinite(failureHysteresisMinutes) || failureHysteresisMinutes < 0) {
        errors.push("Failure alert hysteresis must be >= 0 minutes.");
      }
      if (!Number.isFinite(similarity) || similarity < 0 || similarity > 1) {
        errors.push("Speaker similarity threshold must be between 0 and 1.");
      }
      if (provider === "cloud" && !cloudModel) {
        errors.push("Cloud model is required when intel provider is cloud.");
      }
      if (!cloudApiEnv) {
        errors.push("Cloud API key env var cannot be empty.");
      }
      if (cloudBaseUrl) {
        try {
          const parsed = new URL(cloudBaseUrl);
          if (!["http:", "https:"].includes(parsed.protocol)) {
            errors.push("Cloud base URL must use http:// or https://");
          }
        } catch (_error) {
          errors.push("Cloud base URL must be a valid URL.");
        }
      }
      if (failureWebhookUrl) {
        try {
          const parsed = new URL(failureWebhookUrl);
          if (!["http:", "https:"].includes(parsed.protocol)) {
            errors.push("Failure alert webhook URL must use http:// or https://");
          }
        } catch (_error) {
          errors.push("Failure alert webhook URL must be a valid URL.");
        }
      }
      if ((failureWebhookHeaderName && !failureWebhookHeaderValue) || (!failureWebhookHeaderName && failureWebhookHeaderValue)) {
        errors.push("Webhook header name and value must both be set or both be empty.");
      }
      if (failureWebhookHeaderName && !/^[A-Za-z0-9-]+$/.test(failureWebhookHeaderName)) {
        errors.push("Webhook header name may only contain letters, digits, and hyphens.");
      }
      return errors;
    },

    // ── Project methods ──────────────────────────────────

    async loadProjects() {
      this.loadingProjects = true;
      try {
        const data = await this.apiJson("/api/projects");
        this.projects = data.projects || [];
      } catch (error) {
        console.error("Failed to load projects:", error);
        this.projects = [];
        this.flash(`Projects load failed: ${error.message}`, true);
      }
      this.loadingProjects = false;
    },

    openNewProjectForm() {
      this.showNewProjectForm = true;
      this.projectDraft = { name: "", description: "", keywords: "", team_members: "", detection_threshold: 0.4 };
    },

    async createProject() {
      const draft = this.projectDraft;
      if (!draft.name.trim()) return;
      try {
        const payload = {
          name: draft.name.trim(),
          description: draft.description.trim(),
          keywords: draft.keywords,
          team_members: draft.team_members,
          detection_threshold: draft.detection_threshold,
        };
        const data = await this.apiJson("/api/projects", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (data.success) {
          this.flash("Project created.");
          this.showNewProjectForm = false;
          await this.loadProjects();
        } else {
          this.flash(data.error || "Failed to create project.", true);
        }
      } catch (error) {
        this.flash(`Create project failed: ${error.message}`, true);
      }
    },

    async openProject(projectId) {
      try {
        const project = await this.apiJson(`/api/projects/${projectId}`);
        this.selectedProject = project;
        this.projectSummary = null;
        this.projectMeetings = [];
        this.projectActionItems = [];
        this.projectArtifacts = [];
        // Load sub-data in parallel
        const [summary, meetings, actionItems, artifacts] = await Promise.all([
          this.apiJson(`/api/projects/${projectId}/summary`),
          this.apiJson(`/api/projects/${projectId}/meetings`),
          this.apiJson(`/api/projects/${projectId}/action-items`),
          this.apiJson(`/api/projects/${projectId}/artifacts`),
        ]);
        this.projectSummary = summary;
        this.projectMeetings = meetings.meetings || [];
        this.projectActionItems = actionItems.action_items || [];
        this.projectArtifacts = artifacts.artifacts || [];
      } catch (error) {
        this.flash(`Failed to load project: ${error.message}`, true);
      }
    },

    async refreshProjectActionItems() {
      if (!this.selectedProject) return;
      const data = await this.apiJson(`/api/projects/${this.selectedProject.id}/action-items`);
      this.projectActionItems = data.action_items || [];
    },

    async patchProject(field, value) {
      if (!this.selectedProject) return;
      try {
        const payload = {};
        payload[field] = value;
        const data = await this.apiJson(`/api/projects/${this.selectedProject.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (data.success && data.project) {
          this.selectedProject = data.project;
          this.flash("Project updated.");
          await this.loadProjects();
        } else {
          this.flash(data.error || "Failed to update project.", true);
        }
      } catch (error) {
        this.flash(`Update failed: ${error.message}`, true);
      }
    },

    async archiveProject() {
      if (!this.selectedProject) return;
      try {
        const data = await this.apiJson(`/api/projects/${this.selectedProject.id}`, {
          method: "DELETE",
        });
        if (data.success) {
          this.flash("Project archived.");
          this.selectedProject = null;
          await this.loadProjects();
        } else {
          this.flash(data.error || "Failed to archive.", true);
        }
      } catch (error) {
        this.flash(`Archive failed: ${error.message}`, true);
      }
    },

    async loadSettings() {
      this.loadingSettings = true;
      try {
        this.settings = await this.apiJson("/api/settings");
        this.settingsValidationErrors = [];
      } catch (error) {
        console.error("Failed to load settings:", error);
        this.settings = null;
        this.flash(`Settings load failed: ${error.message}`, true);
      }
      this.loadingSettings = false;
    },

    async saveSettings() {
      if (!this.settings) return;
      this.savingSettings = true;
      this.settingsValidationErrors = [];
      try {
        const payload = JSON.parse(JSON.stringify(this.settings));
        payload.meeting.intel_queue_poll_seconds = Number(payload.meeting.intel_queue_poll_seconds);
        payload.meeting.intel_retry_base_seconds = Number(payload.meeting.intel_retry_base_seconds);
        payload.meeting.intel_retry_max_seconds = Number(payload.meeting.intel_retry_max_seconds);
        payload.meeting.intel_retry_max_attempts = Number(payload.meeting.intel_retry_max_attempts);
        payload.meeting.intel_retry_failure_alert_percent = Number(payload.meeting.intel_retry_failure_alert_percent);
        payload.meeting.intel_retry_failure_hysteresis_minutes = Number(payload.meeting.intel_retry_failure_hysteresis_minutes);
        payload.meeting.similarity_threshold = Number(payload.meeting.similarity_threshold);
        payload.meeting.intel_cloud_base_url = String(payload.meeting.intel_cloud_base_url || "").trim() || null;
        payload.meeting.intel_retry_failure_webhook_url = String(payload.meeting.intel_retry_failure_webhook_url || "").trim() || null;
        payload.meeting.intel_retry_failure_webhook_header_name = String(payload.meeting.intel_retry_failure_webhook_header_name || "").trim() || null;
        payload.meeting.intel_retry_failure_webhook_header_value = String(payload.meeting.intel_retry_failure_webhook_header_value || "").trim() || null;
        payload.meeting.intel_cloud_api_key_env = String(payload.meeting.intel_cloud_api_key_env || "").trim();
        payload.meeting.intel_cloud_model = String(payload.meeting.intel_cloud_model || "").trim();
        payload.meeting.intel_provider = String(payload.meeting.intel_provider || "").toLowerCase();
        payload.meeting.intel_summary_model = String(payload.meeting.intel_summary_model || "").trim() || null;
        payload.meeting.intel_cloud_reasoning_effort = String(payload.meeting.intel_cloud_reasoning_effort || "").trim() || null;
        payload.meeting.mic_device = String(payload.meeting.mic_device || "").trim() || null;
        payload.meeting.system_audio_device = String(payload.meeting.system_audio_device || "").trim() || null;
        payload.meeting.mir_profile = String(payload.meeting.mir_profile || "").toLowerCase();
        payload.ui.history_lines = Number(payload.ui.history_lines);
        payload.ui.theme = String(payload.ui.theme || "").toLowerCase();

        const validationErrors = this.validateSettingsPayload(payload);
        if (validationErrors.length > 0) {
          this.settingsValidationErrors = validationErrors;
          this.flash(validationErrors[0], true);
          this.savingSettings = false;
          return;
        }

        const data = await this.apiJson("/api/settings", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        this.settings = data.settings || payload;
        this.settingsValidationErrors = [];
        this.flash("Settings saved. Runtime configuration updated.");
        await this.loadMeetings();
      } catch (error) {
        console.error("Failed to save settings:", error);
        this.flash(`Settings save failed: ${error.message}`, true);
      }
      this.savingSettings = false;
    },

    formatDate(iso) {
      if (!iso) return "";
      const date = new Date(iso);
      return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    },

    formatRelativeFromNow(iso) {
      if (!iso) return "";
      const target = new Date(iso);
      if (Number.isNaN(target.getTime())) return "";
      const deltaMs = target.getTime() - Date.now();
      const deltaSeconds = Math.round(Math.abs(deltaMs) / 1000);
      if (deltaSeconds < 60) return deltaMs >= 0 ? "in <1m" : "<1m ago";
      const deltaMinutes = Math.round(deltaSeconds / 60);
      if (deltaMinutes < 60) return deltaMs >= 0 ? `in ${deltaMinutes}m` : `${deltaMinutes}m ago`;
      const deltaHours = Math.round(deltaMinutes / 60);
      return deltaMs >= 0 ? `in ${deltaHours}h` : `${deltaHours}h ago`;
    },

    formatDuration(seconds) {
      if (!seconds) return "--:--";
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      if (mins >= 60) {
        const hrs = Math.floor(mins / 60);
        const rem = mins % 60;
        return `${hrs}:${String(rem).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
      }
      return `${mins}:${String(secs).padStart(2, "0")}`;
    },

    formatTimestamp(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `[${mins}:${String(secs).padStart(2, "0")}]`;
    },
  };
}
