function historyApp() {
  return {
    tab: "meetings",
    loading: true,
    loadingActions: true,
    loadingSpeakers: true,
    loadingSpeakerDetail: false,
    loadingIntel: true,
    loadingPluginJobs: true,
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
    selectedMeetingProposals: [],
    selectedMeetingAftercare: null,
    highlightedSegmentIndex: null,
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
    savingSpeaker: false,
    processingIntel: false,
    processingPluginJobs: false,
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

    // HS-13-09: project briefing timeline state.
    projectBriefings: [],
    loadingBriefingTimeline: false,
    briefingExpanded: {},
    briefingRunInProgress: false,
    briefingTimelineError: "",

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
        this.selectedMeetingProposals = [];
        this.selectedMeetingAftercare = null;
        this.selectedMeeting = await this.apiJson(`/api/meetings/${id}`);
        // HS-49-01: the aftercare digest (open / decided / changed). Read-only;
        // stays quiet (is_empty) when there's nothing to act on.
        try {
          const aftercare = await this.apiJson(`/api/meetings/${id}/aftercare`);
          this.selectedMeetingAftercare = aftercare && !aftercare.is_empty ? aftercare : null;
        } catch (aftercareError) {
          console.error("Failed to load meeting aftercare:", aftercareError);
          this.selectedMeetingAftercare = null;
        }
        try {
          const artifacts = await this.apiJson(`/api/meetings/${id}/artifacts`);
          this.selectedMeetingArtifacts = artifacts.artifacts || [];
        } catch (artifactError) {
          console.error("Failed to load meeting artifacts:", artifactError);
          this.selectedMeetingArtifacts = [];
        }
        // HS-37-03: load actuator proposals (read-only — viewing never acts).
        try {
          const proposals = await this.apiJson(`/api/meetings/${id}/proposals`);
          this.selectedMeetingProposals = proposals.proposals || [];
        } catch (proposalError) {
          console.error("Failed to load meeting proposals:", proposalError);
          this.selectedMeetingProposals = [];
        }
      } catch (error) {
        console.error("Failed to load meeting:", error);
        this.flash(`Meeting detail failed: ${error.message}`, true);
      }
    },

    // HS-49-02: "show me the moment". Reveal + briefly flash the transcript
    // segment that justifies a result. Focus-safe — it scrolls the segment into
    // view but never calls .focus(), so it can't steal keyboard focus from a
    // live dictation/presence surface sharing the bundle.
    jumpToSegment(index) {
      if (index === null || index === undefined || index < 0) return;
      this.highlightedSegmentIndex = index;
      this.$nextTick(() => {
        const el = document.getElementById(`seg-${index}`);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
      });
      // Clear the flash so a later jump re-triggers the animation.
      window.setTimeout(() => {
        if (this.highlightedSegmentIndex === index) this.highlightedSegmentIndex = null;
      }, 2200);
    },

    // Resolve a raw provenance timestamp to its segment client-side (mirrors the
    // backend resolve_provenance_segment), for surfaces that carry only the raw
    // source_timestamp (e.g. the intel action-item cards).
    jumpToMoment(ts) {
      if (ts === null || ts === undefined) return;
      const segments = this.selectedMeeting?.segments || [];
      if (!segments.length) return;
      let target = 0;
      for (let i = 0; i < segments.length; i++) {
        if (segments[i].start_time <= ts) target = i;
        else break;
      }
      this.jumpToSegment(target);
    },

    hasMoment(ts) {
      return (
        ts !== null &&
        ts !== undefined &&
        (this.selectedMeeting?.segments || []).length > 0
      );
    },

    // HS-37-03: approve/reject an actuator proposal. Approving only flips DB
    // state (records the decision + an audit entry) — it performs NO side
    // effect; execution is HS-37-04. The decided row is updated in place.
    async decideProposal(proposal, decision) {
      if (!this.selectedMeeting?.id || !proposal?.id) return;
      try {
        const res = await this.apiJson(
          `/api/meetings/${this.selectedMeeting.id}/proposals/${proposal.id}/decision`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ decision }),
          },
        );
        const updated = res.proposal;
        if (updated) {
          this.selectedMeetingProposals = this.selectedMeetingProposals.map((p) =>
            p.id === updated.id ? updated : p,
          );
        }
        this.flash(
          decision === "approved"
            ? "Proposal approved — recorded; nothing runs without it."
            : "Proposal rejected.",
        );
      } catch (error) {
        console.error("Failed to decide proposal:", error);
        this.flash(`Decision failed: ${error.message}`, true);
      }
    },

    proposalStatusLabel(status) {
      return (
        {
          proposed: "Awaiting approval",
          approved: "Approved — pending execution",
          executed: "Executed",
          rejected: "Rejected",
          failed: "Failed",
        }[status] || String(status || "")
      );
    },

    proposalAccent(proposal) {
      return (
        {
          proposed: "warn",
          approved: "info",
          executed: "ok",
          rejected: "default",
          failed: "danger",
        }[proposal?.status] || "default"
      );
    },

    proposalIcon(proposal) {
      const target = String(proposal?.target || "").toLowerCase();
      return { github: "🐙", jira: "🧩", slack: "💬", webhook: "🔗" }[target] || "⚡";
    },

    // The reviewable preview: action → target, the human preview, then the
    // exact machine payload — the source of truth a reviewer is approving.
    proposalPreviewText(proposal) {
      const lines = [`${proposal.action} → ${proposal.target}`];
      if (proposal.preview) lines.push("", proposal.preview);
      const payload = proposal.payload || {};
      if (payload && Object.keys(payload).length) {
        lines.push("", JSON.stringify(payload, null, 2));
      }
      return lines.join("\n");
    },

    async copyProposal(proposal) {
      return await this.copyMarkdown(this.proposalPreviewText(proposal));
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
        this.projectBriefings = [];
        this.briefingExpanded = {};
        this.briefingTimelineError = "";
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
        // HS-13-09: load the project briefing timeline alongside.
        this.loadProjectBriefings();
      } catch (error) {
        this.flash(`Failed to load project: ${error.message}`, true);
      }
    },

    async loadProjectBriefings() {
      if (!this.selectedProject) return;
      this.loadingBriefingTimeline = true;
      try {
        const data = await this.apiJson(
          `/api/projects/${this.selectedProject.id}/briefings`
        );
        this.projectBriefings = data.briefings || [];
      } catch (error) {
        this.briefingTimelineError = error.message;
      } finally {
        this.loadingBriefingTimeline = false;
      }
    },

    toggleBriefing(briefingId) {
      this.briefingExpanded = {
        ...this.briefingExpanded,
        [briefingId]: !this.briefingExpanded[briefingId],
      };
    },

    briefingFirstLineFor(briefing) {
      const md = (briefing && briefing.value && briefing.value.markdown) || "";
      // briefingFirstLine is concatenated in by history.astro's
      // <script> loader (HS-13-09 shared util).
      return briefingFirstLine(md);
    },

    briefingHtmlFor(briefing) {
      const md = (briefing && briefing.value && briefing.value.markdown) || "";
      return renderBriefingMarkdown(md);
    },

    // HS-27-02: structured renderers for artifact bodies so the detail view
    // shows a real diagram / checklist instead of dumping raw markdown text.
    isDiagram(artifact) {
      return artifact?.artifact_type === "diagram" && !!artifact?.structured_json?.mermaid;
    },

    actionItemsFor(artifact) {
      if (artifact?.artifact_type !== "action_items") return [];
      const items = artifact?.structured_json?.action_items;
      return Array.isArray(items) ? items : [];
    },

    actionGapLabel(gap) {
      return (
        {
          missing_owner: "No owner",
          missing_due: "No due date",
          missing_both: "No owner or due date",
        }[gap] || ""
      );
    },

    decisionsFor(artifact) {
      if (artifact?.artifact_type !== "decisions") return [];
      const items = artifact?.structured_json?.decisions;
      return Array.isArray(items) ? items : [];
    },

    openQuestionsFor(artifact) {
      if (artifact?.artifact_type !== "decisions") return [];
      const items = artifact?.structured_json?.open_questions;
      return Array.isArray(items) ? items : [];
    },

    hasDecisions(artifact) {
      return this.decisionsFor(artifact).length > 0 || this.openQuestionsFor(artifact).length > 0;
    },

    // HS-27-04: requirements render, classified by type.
    requirementsFor(artifact) {
      if (artifact?.artifact_type !== "requirements") return [];
      const items = artifact?.structured_json?.requirements;
      return Array.isArray(items) ? items : [];
    },

    requirementTypeLabel(type) {
      return (
        {
          functional: "Functional",
          non_functional: "Non-functional",
          constraint: "Constraint",
          acceptance: "Acceptance",
        }[type] || "Requirement"
      );
    },

    // HS-28-02: Architecture Decision Records render.
    adrsFor(artifact) {
      if (artifact?.artifact_type !== "adr") return [];
      const items = artifact?.structured_json?.adrs;
      return Array.isArray(items) ? items : [];
    },

    // HS-28-03: milestone plan render.
    milestonesFor(artifact) {
      if (artifact?.artifact_type !== "milestone_plan") return [];
      const items = artifact?.structured_json?.milestones;
      return Array.isArray(items) ? items : [];
    },

    // HS-28-04: risk register render.
    risksFor(artifact) {
      if (artifact?.artifact_type !== "risk_register") return [];
      const items = artifact?.structured_json?.risks;
      return Array.isArray(items) ? items : [];
    },

    // HS-29-01: dependency map / scope review / customer signals.
    dependenciesFor(artifact) {
      if (artifact?.artifact_type !== "dependency_map") return [];
      const items = artifact?.structured_json?.dependencies;
      return Array.isArray(items) ? items : [];
    },

    scopeFindingsFor(artifact) {
      if (artifact?.artifact_type !== "scope_review") return [];
      const items = artifact?.structured_json?.findings;
      return Array.isArray(items) ? items : [];
    },

    scopeVerdictLabel(verdict) {
      return (
        { in_scope: "In scope", out_of_scope: "Out of scope", scope_creep: "Scope creep" }[verdict] ||
        "In scope"
      );
    },

    customerSignalsFor(artifact) {
      if (artifact?.artifact_type !== "customer_signals") return [];
      const items = artifact?.structured_json?.signals;
      return Array.isArray(items) ? items : [];
    },

    // HS-29-02: incident timeline / runbook delta.
    incidentEventsFor(artifact) {
      if (artifact?.artifact_type !== "incident_timeline") return [];
      const items = artifact?.structured_json?.events;
      return Array.isArray(items) ? items : [];
    },

    runbookChangesFor(artifact) {
      if (artifact?.artifact_type !== "runbook_delta") return [];
      const items = artifact?.structured_json?.changes;
      return Array.isArray(items) ? items : [];
    },

    // HS-29-03: stakeholder update / decision announcements.
    stakeholderUpdateFor(artifact) {
      if (artifact?.artifact_type !== "stakeholder_update") return null;
      const u = artifact?.structured_json?.update;
      return u && typeof u === "object" ? u : null;
    },

    stakeholderSections(artifact) {
      const u = this.stakeholderUpdateFor(artifact);
      if (!u) return [];
      return [
        { label: "Highlights", items: u.highlights || [] },
        { label: "Risks", items: u.risks || [] },
        { label: "Next steps", items: u.next_steps || [] },
      ].filter((s) => Array.isArray(s.items) && s.items.length > 0);
    },

    announcementsFor(artifact) {
      if (artifact?.artifact_type !== "decision_announcement") return [];
      const items = artifact?.structured_json?.announcements;
      return Array.isArray(items) ? items : [];
    },

    // True when any structured renderer applies — used to suppress the raw
    // body_markdown fallback. Grows as artifact types are added.
    hasStructuredRender(artifact) {
      return (
        this.isDiagram(artifact) ||
        this.actionItemsFor(artifact).length > 0 ||
        this.hasDecisions(artifact) ||
        this.requirementsFor(artifact).length > 0 ||
        this.adrsFor(artifact).length > 0 ||
        this.milestonesFor(artifact).length > 0 ||
        this.risksFor(artifact).length > 0 ||
        this.dependenciesFor(artifact).length > 0 ||
        this.scopeFindingsFor(artifact).length > 0 ||
        this.customerSignalsFor(artifact).length > 0 ||
        this.incidentEventsFor(artifact).length > 0 ||
        this.runbookChangesFor(artifact).length > 0 ||
        !!this.stakeholderUpdateFor(artifact) ||
        this.announcementsFor(artifact).length > 0
      );
    },

    // HS-36-01: per-artifact-type presentation helpers for the elevated card —
    // a glyph + a Signal accent group (drives the card's colored edge/chip) +
    // a human label. Unknown types fall back to a neutral default.
    artifactIcon(artifact) {
      const map = {
        incident_timeline: "🔥",
        risk_register: "⚠️",
        runbook_delta: "🧯",
        decision_announcement: "📢",
        stakeholder_update: "📣",
        decisions: "🎯",
        action_items: "✅",
        requirements: "🧩",
        adr: "🏛️",
        milestone_plan: "🗓️",
        dependency_map: "🔗",
        scope_review: "🔎",
        customer_signals: "💬",
        diagram: "🗺️",
      };
      return map[artifact?.artifact_type] || "◆";
    },
    artifactAccent(artifact) {
      const map = {
        incident_timeline: "danger",
        risk_register: "warn",
        runbook_delta: "warn",
        decision_announcement: "accent",
        stakeholder_update: "accent",
        decisions: "accent",
        action_items: "ok",
        requirements: "info",
        adr: "info",
        milestone_plan: "info",
        dependency_map: "info",
        scope_review: "info",
        customer_signals: "ok",
        diagram: "info",
      };
      return map[artifact?.artifact_type] || "default";
    },
    artifactTypeLabel(artifact) {
      return String(artifact?.artifact_type || "").replace(/_/g, " ");
    },

    // HS-36-02: serialize one artifact's structured_json to clean Markdown,
    // driven by the same per-type accessors the card renders from (so a
    // collapsed card still copies). Pure: artifact -> string. Tabular types
    // (risk register) become Markdown tables with escaped cells; timelines
    // become ordered lists; sectioned types get headings.
    artifactMarkdown(artifact) {
      // collapse newlines + escape table-breaking pipes for inline text
      const inline = (s) =>
        String(s ?? "").replace(/\r?\n+/g, " ").trim();
      const cell = (s) => {
        const v = inline(s).replace(/\|/g, "\\|");
        return v.length ? v : "—";
      };
      const md = [];
      const title = inline(artifact?.title) || this.artifactTypeLabel(artifact) || "Artifact";
      md.push(`## ${title}`, "");
      const typeLabel = this.artifactTypeLabel(artifact);
      if (typeLabel) md.push(`**Type:** ${typeLabel}`, "");

      if (this.isDiagram(artifact)) {
        md.push("```mermaid", String(artifact.structured_json.mermaid || "").trim(), "```", "");
      }

      const ais = this.actionItemsFor(artifact);
      if (ais.length) {
        for (const ai of ais) {
          const meta = [`owner: ${inline(ai.owner) || "—"}`, `due: ${inline(ai.due) || "—"}`];
          const gap = this.actionGapLabel(ai.gap);
          if (gap) meta.push(gap);
          md.push(`- ${inline(ai.task)} _(${meta.join(", ")})_`);
        }
        md.push("");
      }

      if (this.hasDecisions(artifact)) {
        const ds = this.decisionsFor(artifact);
        if (ds.length) {
          md.push("### Decisions");
          for (const d of ds) {
            md.push(`- ${inline(d.decision)}${d.rationale ? ` — ${inline(d.rationale)}` : ""}`);
          }
          md.push("");
        }
        const qs = this.openQuestionsFor(artifact);
        if (qs.length) {
          md.push("### Open questions");
          for (const q of qs) md.push(`- ${inline(q)}`);
          md.push("");
        }
      }

      const reqs = this.requirementsFor(artifact);
      if (reqs.length) {
        for (const r of reqs) {
          md.push(`- **${this.requirementTypeLabel(r.type)}** — ${inline(r.text)}`);
        }
        md.push("");
      }

      const adrs = this.adrsFor(artifact);
      if (adrs.length) {
        for (const adr of adrs) {
          md.push(`### ${inline(adr.title)}${adr.status ? ` _(${inline(adr.status)})_` : ""}`);
          if (adr.context) md.push(`- **Context:** ${inline(adr.context)}`);
          if (adr.decision) md.push(`- **Decision:** ${inline(adr.decision)}`);
          if (adr.consequences) md.push(`- **Consequences:** ${inline(adr.consequences)}`);
          md.push("");
        }
      }

      const milestones = this.milestonesFor(artifact);
      if (milestones.length) {
        for (const m of milestones) {
          md.push(`### ${inline(m.name)}${m.target ? ` — ${inline(m.target)}` : ""}`);
          if (Array.isArray(m.deliverables) && m.deliverables.length) {
            md.push(`- **Deliverables:** ${m.deliverables.map(inline).join(", ")}`);
          }
          if (Array.isArray(m.dependencies) && m.dependencies.length) {
            md.push(`- **Dependencies:** ${m.dependencies.map(inline).join(", ")}`);
          }
          md.push("");
        }
      }

      const risks = this.risksFor(artifact);
      if (risks.length) {
        md.push("| Risk | Impact | Likelihood | Mitigation | Owner |");
        md.push("| --- | --- | --- | --- | --- |");
        for (const r of risks) {
          md.push(
            `| ${cell(r.risk)} | ${cell(r.impact)} | ${cell(r.likelihood)} | ${cell(r.mitigation)} | ${cell(r.owner)} |`,
          );
        }
        md.push("");
      }

      const deps = this.dependenciesFor(artifact);
      if (deps.length) {
        for (const d of deps) {
          md.push(`- ${inline(d.from)} → ${inline(d.to)}${d.note ? ` — ${inline(d.note)}` : ""}`);
        }
        md.push("");
      }

      const findings = this.scopeFindingsFor(artifact);
      if (findings.length) {
        for (const f of findings) {
          md.push(
            `- **${this.scopeVerdictLabel(f.verdict)}** — ${inline(f.item)}${f.rationale ? ` — ${inline(f.rationale)}` : ""}`,
          );
        }
        md.push("");
      }

      const signals = this.customerSignalsFor(artifact);
      if (signals.length) {
        for (const s of signals) {
          const kind = inline(s.type).replace(/_/g, " ");
          md.push(
            `- ${kind ? `**${kind}** — ` : ""}${inline(s.signal)}${s.quote ? ` — “${inline(s.quote)}”` : ""}`,
          );
        }
        md.push("");
      }

      const events = this.incidentEventsFor(artifact);
      if (events.length) {
        events.forEach((e, i) => {
          md.push(`${i + 1}. ${e.time ? `**${inline(e.time)}** — ` : ""}${inline(e.event)}`);
        });
        md.push("");
      }

      const changes = this.runbookChangesFor(artifact);
      if (changes.length) {
        for (const c of changes) {
          md.push(
            `- **${inline(c.type)}** — ${inline(c.change)}${c.detail ? ` — ${inline(c.detail)}` : ""}`,
          );
        }
        md.push("");
      }

      const update = this.stakeholderUpdateFor(artifact);
      if (update) {
        if (update.headline) md.push(`**${inline(update.headline)}**`, "");
        for (const sec of this.stakeholderSections(artifact)) {
          md.push(`### ${sec.label}`);
          for (const it of sec.items) md.push(`- ${inline(it)}`);
          md.push("");
        }
      }

      const anns = this.announcementsFor(artifact);
      if (anns.length) {
        for (const a of anns) {
          md.push(`### ${inline(a.title)}${a.audience ? ` _(${inline(a.audience)})_` : ""}`);
          if (a.message) md.push(inline(a.message));
          md.push("");
        }
      }

      // Fallback: no structured renderer matched — use the raw body markdown.
      if (!this.hasStructuredRender(artifact) && artifact?.body_markdown) {
        md.push(String(artifact.body_markdown).trim(), "");
      }

      return md.join("\n").replace(/\n{3,}/g, "\n\n").trim() + "\n";
    },

    // HS-36-02: concatenate every artifact in the open meeting under a single
    // meeting heading, for the "Copy all" affordance.
    allArtifactsMarkdown() {
      const title = this.selectedMeeting?.title || "Meeting";
      const parts = [`# ${title} — Artifacts`, ""];
      for (const a of this.selectedMeetingArtifacts || []) {
        parts.push(this.artifactMarkdown(a), "");
      }
      return parts.join("\n").replace(/\n{3,}/g, "\n\n").trim() + "\n";
    },

    // HS-36-02: write text to the clipboard, mirroring CommandPreview's
    // pattern (async writeText + graceful failure). Returns true on success,
    // false when the clipboard is blocked so the caller can hint "Press ⌘C".
    async copyMarkdown(text) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch {
        return false;
      }
    },

    // HS-16-04: render a diagram artifact's Mermaid (from structured_json) as
    // inline SVG. mermaid.js is loaded lazily via window.__loadMermaid (a code
    // -split chunk wired in history.astro), so non-diagram views never pay the
    // bundle cost. On any render failure we fall back to the raw source plus a
    // small warning rather than throwing or blanking the card. securityLevel
    // 'strict' (mermaid 11 default) disables HTML in labels.
    async renderMermaid(el, code) {
      if (!el || !code || typeof window.__loadMermaid !== "function") return;
      try {
        const mermaid = await window.__loadMermaid();
        if (!window.__mermaidInited) {
          // suppressErrorRendering: don't let mermaid inject its "syntax error"
          // bomb SVG into the DOM on failure — we own the fallback below.
          mermaid.initialize({
            startOnLoad: false,
            securityLevel: "strict",
            suppressErrorRendering: true,
            theme: "dark",
          });
          window.__mermaidInited = true;
        }
        this._mermaidSeq = (this._mermaidSeq || 0) + 1;
        const { svg } = await mermaid.render(`hs-mermaid-${this._mermaidSeq}`, code);
        el.innerHTML = svg;
      } catch (err) {
        console.error("Mermaid render failed:", err);
        el.replaceChildren();
        const warn = document.createElement("div");
        warn.className = "mermaid-render-error";
        warn.textContent = "Diagram could not be rendered — showing source.";
        const pre = document.createElement("pre");
        pre.className = "mermaid-source";
        pre.textContent = code;
        el.append(warn, pre);
      }
    },

    async runProjectBriefing() {
      if (!this.selectedProject) return;
      if (this.briefingRunInProgress) return;
      this.briefingRunInProgress = true;
      this.briefingTimelineError = "";
      try {
        const response = await fetch(
          "/api/activity/enrichment/pipelines/meeting_context/run",
          { method: "POST" }
        );
        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
          this.briefingTimelineError = body.error || `HTTP ${response.status}`;
        } else if (body.result && body.result.succeeded === false) {
          const failed = (body.result.steps || []).find(
            (s) => s.status === "failed" || s.status === "missing_runner"
          );
          this.briefingTimelineError = failed
            ? `${failed.pack_id}: ${failed.error || failed.status}`
            : "Pipeline reported failure.";
        }
      } catch (error) {
        this.briefingTimelineError = String(error);
      } finally {
        await this.loadProjectBriefings();
        this.briefingRunInProgress = false;
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
      const projectName = this.selectedProject.name || `project ${this.selectedProject.id}`;
      const ok = await window.holdspeakConfirm({
        title: `Archive project "${projectName}"?`,
        body: "Archived projects no longer appear in the active list. Existing meetings, transcripts, and artifacts associated with this project are kept locally.",
        scopeNote: "Only the local project record is archived. No source data is touched.",
        confirmLabel: "Archive project",
      });
      if (!ok) return;
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

    // HS-42-02: settings moved to the global /settings route. History keeps a
    // read-only load so the intel-queue alert thresholds (which read
    // `settings.meeting.*`) stay populated; editing + validation now live in
    // src/scripts/settings-app.js.
    async loadSettings() {
      try {
        this.settings = await this.apiJson("/api/settings");
      } catch (error) {
        console.error("Failed to load settings:", error);
        this.settings = null;
      }
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
