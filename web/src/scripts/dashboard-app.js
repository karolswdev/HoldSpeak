      function HoldSpeakDashboard() {
        const MAX_ENTRIES = 2000;

        const pad2 = (n) => String(n).padStart(2, "0");
        const formatSeconds = (seconds) => {
          const s = Math.max(0, Math.floor(Number(seconds) || 0));
          const h = Math.floor(s / 3600);
          const m = Math.floor((s % 3600) / 60);
          const ss = s % 60;
          return h ? `${pad2(h)}:${pad2(m)}:${pad2(ss)}` : `${pad2(m)}:${pad2(ss)}`;
        };

        const safeJsonParse = (text) => {
          try {
            return JSON.parse(text);
          } catch {
            return null;
          }
        };

        const copyText = async (text) => {
          try {
            await navigator.clipboard.writeText(text);
            return true;
          } catch {
            const ta = document.createElement("textarea");
            ta.value = text;
            ta.setAttribute("readonly", "true");
            ta.style.position = "fixed";
            ta.style.top = "-9999px";
            document.body.appendChild(ta);
            ta.select();
            try {
              return document.execCommand("copy");
            } catch {
              return false;
            } finally {
              document.body.removeChild(ta);
            }
          }
        };

        return {
          ws: null,
          pingTimer: null,
          reconnectTimer: null,
          reconnectAttempt: 0,
          reconnectAt: null,
          closedByUser: false,
          connectionState: "connecting",
          duration: "00:00",
          meetingActive: false,
          startInProgress: false,
          stopInProgress: false,
          intelStatus: {
            state: "unknown",
            detail: "Waiting for meeting status.",
            requested_at: null,
            completed_at: null,
          },
          intentControls: {
            enabled: false,
            profile: "balanced",
            available_profiles: [],
            supported_intents: [],
            override_intents: [],
            last_preview: null,
            threshold: 0.6,
          },
          intentProfile: "balanced",
          intentOverrideInput: "",
          routePreview: null,
          routePreviewLoading: false,
          intentControlSaving: false,
          entries: [],
          segments: [],
          intel: { topics: [], action_items: [], summary: "" },
          pluginJobs: [],
          pluginJobSummary: null,
          pluginJobStatusFilter: "all",
          pluginJobLimit: 20,
          loadingPluginJobs: false,
          processingPluginJobs: false,
          intelBuffer: "",
          intelStreaming: false,
          exportOpen: false,
          bookmarkModalOpen: false,
          bookmarkLabel: "",
          metadataModalOpen: false,
          editingTitle: "",
          editingTags: "",
          meetingTitle: "",
          meetingTags: [],
          notifications: [],

          init() {
            this.fetchRuntimeStatus();
            this.fetchIntentControls();
            this.loadPluginJobs();
            this.loadPluginJobSummary();
            this.connect();
            window.addEventListener("beforeunload", () => {
              this.closedByUser = true;
              this.cleanup();
            });
          },

          cleanup() {
            if (this.reconnectTimer) window.clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
            if (this.pingTimer) window.clearInterval(this.pingTimer);
            this.pingTimer = null;
            if (this.ws) {
              try {
                this.ws.close();
              } catch {}
            }
            this.ws = null;
          },

          wsUrl() {
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            return `${protocol}//${window.location.host}/ws`;
          },

          connectionLabel() {
            if (this.connectionState === "connected") return "Connected";
            if (this.connectionState === "connecting") return "Connecting...";
            if (this.connectionState === "reconnecting") {
              if (!this.reconnectAt) return "Reconnecting...";
              const remaining = Math.max(0, Math.ceil((this.reconnectAt - Date.now()) / 1000));
              return remaining ? `Reconnecting in ${remaining}s...` : "Reconnecting...";
            }
            return "Disconnected";
          },

          connectionTone() {
            return `status-${this.connectionState}`;
          },

          activeActionItems() {
            return this.intel.action_items.filter((item) => item.status !== "dismissed");
          },

          intelStatusTitle() {
            const state = String(this.intelStatus?.state || "").toLowerCase();
            if (state === "live") return "Live";
            if (state === "running") return "Processing";
            if (state === "queued") return "Queued";
            if (state === "ready") return "Ready";
            if (state === "error") return "Unavailable";
            if (state === "disabled") return "Disabled";
            return "Pending";
          },

          intelStatusCopy() {
            const detail = String(this.intelStatus?.detail || "").trim();
            if (detail) return detail;
            const state = String(this.intelStatus?.state || "").toLowerCase();
            if (state === "ready") return "Meeting intelligence is available for this session.";
            if (state === "queued") return "Meeting intelligence will run later when a compatible local model is available.";
            if (state === "running") return "Meeting intelligence is processing the latest transcript.";
            if (state === "live") return "Meeting intelligence will stream live while the meeting is active.";
            if (state === "disabled") return "Meeting intelligence is disabled in config.";
            return "Waiting for meeting intelligence status.";
          },

          dismissedCount() {
            return this.intel.action_items.filter((item) => item.status === "dismissed").length;
          },

          pluginQueueFailureRateLabel() {
            const total = Number(this.pluginJobSummary?.total_jobs || 0);
            if (total <= 0) return "0%";
            const failed = Number(this.pluginJobSummary?.failed_jobs || 0);
            return `${Math.round((failed / total) * 100)}%`;
          },

          pluginQueueNextRetryLabel() {
            const nextRetryAt = this.pluginJobSummary?.next_retry_at;
            if (!nextRetryAt) return "No deferred retries scheduled.";
            const rel = this.formatRelativeFromNow(nextRetryAt);
            if (!rel) return `Next retry ${this.formatDate(nextRetryAt)}`;
            return `Next retry ${this.formatDate(nextRetryAt)} (${rel})`;
          },

          pluginJobScheduleLabel(job) {
            const requested = job?.requested_at ? new Date(job.requested_at) : null;
            if (!requested || Number.isNaN(requested.getTime())) return "Retry scheduled";
            const rel = this.formatRelativeFromNow(job.requested_at);
            if (!rel) return `Retry ${this.formatDate(job.requested_at)}`;
            return `Retry ${this.formatDate(job.requested_at)} (${rel})`;
          },

          speakerTone(speaker) {
            const s = String(speaker || "").toLowerCase();
            if (s === "me" || s.includes("me")) return "me";
            if (s === "remote" || s.includes("remote")) return "remote";
            return "other";
          },

          speakerLabel(speaker) {
            return String(speaker || "Unknown").trim() || "Unknown";
          },

          statusClass(status) {
            const value = String(status || "pending").trim().toLowerCase();
            return `status-${value || "pending"}`;
          },

          statusLabel(status) {
            const value = String(status || "pending").trim().toLowerCase();
            if (value === "done") return "Done";
            if (value === "dismissed") return "Dismissed";
            return "Pending";
          },

          reviewStatusClass(reviewState) {
            const value = String(reviewState || "pending").trim().toLowerCase();
            return value === "accepted" ? "status-review-accepted" : "status-review-pending";
          },

          reviewStatusLabel(reviewState) {
            const value = String(reviewState || "pending").trim().toLowerCase();
            return value === "accepted" ? "Accepted" : "Needs review";
          },

          parseSeconds(value) {
            if (typeof value === "number") return Number.isFinite(value) ? value : 0;
            if (typeof value !== "string") return 0;
            const raw = value.trim();
            if (!raw) return 0;
            if (/^\d+(\.\d+)?$/.test(raw)) return Number(raw);
            const parts = raw.split(":").map((p) => Number.parseInt(p, 10));
            if (parts.some((p) => Number.isNaN(p))) return 0;
            if (parts.length === 2) return parts[0] * 60 + parts[1];
            if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
            return 0;
          },

          formatDate(iso) {
            if (!iso) return "";
            const date = new Date(iso);
            if (Number.isNaN(date.getTime())) return "";
            return (
              date.toLocaleDateString() +
              " " +
              date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            );
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
            if (deltaHours < 24) return deltaMs >= 0 ? `in ${deltaHours}h` : `${deltaHours}h ago`;
            const deltaDays = Math.round(deltaHours / 24);
            return deltaMs >= 0 ? `in ${deltaDays}d` : `${deltaDays}d ago`;
          },

          applyIntentControls(controls) {
            if (!controls || typeof controls !== "object") return;
            this.intentControls = {
              enabled: Boolean(controls.enabled),
              profile: String(controls.profile || "balanced"),
              available_profiles: Array.isArray(controls.available_profiles) ? controls.available_profiles : [],
              supported_intents: Array.isArray(controls.supported_intents) ? controls.supported_intents : [],
              override_intents: Array.isArray(controls.override_intents) ? controls.override_intents : [],
              last_preview: controls.last_preview && typeof controls.last_preview === "object" ? controls.last_preview : null,
              threshold: Number(controls.threshold || 0.6),
            };
            this.intentProfile = this.intentControls.profile || "balanced";
            this.intentOverrideInput = this.intentControls.override_intents.join(", ");
            if (this.intentControls.last_preview && typeof this.intentControls.last_preview === "object") {
              this.routePreview = this.intentControls.last_preview;
            }
          },

          applyState(state, { replaceTimeline = false } = {}) {
            if (!state || typeof state !== "object") return;

            if (typeof state?.meeting_active === "boolean") {
              this.meetingActive = state.meeting_active;
            } else {
              this.meetingActive = Boolean(state?.started_at) && !Boolean(state?.ended_at);
            }

            if (typeof state?.formatted_duration === "string" && state.formatted_duration) {
              this.duration = state.formatted_duration;
            } else if (typeof state?.duration === "number") {
              this.duration = formatSeconds(state.duration);
            }

            if (typeof state?.title === "string") {
              this.meetingTitle = state.title;
            }
            if (Array.isArray(state?.tags)) {
              this.meetingTags = state.tags;
            }
            if (state?.intel_status && typeof state.intel_status === "object") {
              this.intelStatus = state.intel_status;
            }
            if (state?.intel && typeof state.intel === "object") {
              this.updateIntel(state.intel);
            } else if (replaceTimeline) {
              this.intel = { topics: [], action_items: [], summary: "" };
            }
            if (state?.mir && typeof state.mir === "object") {
              this.applyIntentControls(state.mir);
            }

            if (!replaceTimeline) return;

            const segments = Array.isArray(state?.segments) ? state.segments : [];
            const bookmarks = Array.isArray(state?.bookmarks) ? state.bookmarks : [];

            const mappedSegments = segments
              .map((segment, idx) => ({
                kind: "segment",
                id: `state-segment-${idx}-${segment?.start_time ?? idx}`,
                speaker: segment?.speaker ?? "Unknown",
                start: this.timeLabel(segment?.start_time),
                end: this.timeLabel(segment?.end_time),
                text: String(segment?.text ?? "").trim(),
                sortTime: this.parseSeconds(segment?.start_time),
              }))
              .filter((segment) => segment.text);

            const mappedBookmarks = bookmarks.map((bookmark, idx) => ({
              kind: "bookmark",
              id: `state-bookmark-${idx}-${bookmark?.timestamp ?? idx}`,
              label: String(bookmark?.label ?? "Bookmark").trim() || "Bookmark",
              timestamp: this.timeLabel(bookmark?.timestamp),
              sortTime: this.parseSeconds(bookmark?.timestamp),
            }));

            const merged = [...mappedSegments, ...mappedBookmarks]
              .sort((a, b) => (a.sortTime || 0) - (b.sortTime || 0))
              .map(({ sortTime, ...entry }) => entry);

            this.segments = mappedSegments.map(({ sortTime, ...segment }) => segment);
            this.entries = merged;
          },

          async fetchRuntimeStatus() {
            try {
              const resp = await fetch("/api/runtime/status", { headers: { accept: "application/json" } });
              if (!resp.ok) {
                await this.fetchInitialState();
                return;
              }
              const payload = await resp.json();
              if (typeof payload?.meeting_active === "boolean") {
                this.meetingActive = payload.meeting_active;
              }
              if (payload?.mir && typeof payload.mir === "object") {
                this.applyIntentControls(payload.mir);
              }
              if (payload?.state && typeof payload.state === "object") {
                this.applyState(payload.state, { replaceTimeline: true });
                return;
              }
              await this.fetchInitialState();
            } catch {
              await this.fetchInitialState();
            }
          },

          async fetchInitialState() {
            try {
              const resp = await fetch("/api/state", { headers: { accept: "application/json" } });
              if (!resp.ok) return;
              const state = await resp.json();
              this.applyState(state, { replaceTimeline: true });
            } catch {}
          },

          async fetchIntentControls() {
            try {
              const resp = await fetch("/api/intents/control", { headers: { accept: "application/json" } });
              if (!resp.ok) return;
              const payload = await resp.json();
              this.applyIntentControls(payload);
            } catch {}
          },

          async loadPluginJobs() {
            this.loadingPluginJobs = true;
            try {
              const status = String(this.pluginJobStatusFilter || "all").trim().toLowerCase() || "all";
              const limit = Number.isFinite(this.pluginJobLimit) && this.pluginJobLimit > 0 ? this.pluginJobLimit : 20;
              const resp = await fetch(
                `/api/plugin-jobs?status=${encodeURIComponent(status)}&limit=${limit}`,
                { headers: { accept: "application/json" } }
              );
              if (!resp.ok) throw new Error("plugin_jobs_failed");
              const payload = await resp.json().catch(() => ({}));
              this.pluginJobs = Array.isArray(payload?.jobs) ? payload.jobs : [];
            } catch {
              this.pluginJobs = [];
              this.toast("Failed to load deferred plugin jobs.");
            } finally {
              this.loadingPluginJobs = false;
            }
          },

          async loadPluginJobSummary() {
            try {
              const resp = await fetch("/api/plugin-jobs/summary", { headers: { accept: "application/json" } });
              if (!resp.ok) throw new Error("plugin_jobs_summary_failed");
              const payload = await resp.json().catch(() => ({}));
              this.pluginJobSummary = payload && typeof payload === "object" ? payload : null;
            } catch {
              this.pluginJobSummary = null;
            }
          },

          async saveIntentProfile() {
            const profile = String(this.intentProfile || "").trim().toLowerCase();
            if (!profile) return;
            this.intentControlSaving = true;
            try {
              const resp = await fetch("/api/intents/profile", {
                method: "PUT",
                headers: { "content-type": "application/json", accept: "application/json" },
                body: JSON.stringify({ profile }),
              });
              const payload = await resp.json().catch(() => ({}));
              if (!resp.ok) throw new Error("intent_profile_failed");
              if (payload?.controls && typeof payload.controls === "object") {
                this.applyIntentControls(payload.controls);
              }
              this.toast("Routing profile updated.");
            } catch {
              this.toast("Failed to update routing profile.");
            } finally {
              this.intentControlSaving = false;
            }
          },

          async saveIntentOverride() {
            const intents = String(this.intentOverrideInput || "")
              .split(",")
              .map((value) => value.trim().toLowerCase())
              .filter((value) => value);
            this.intentControlSaving = true;
            try {
              const resp = await fetch("/api/intents/override", {
                method: "PUT",
                headers: { "content-type": "application/json", accept: "application/json" },
                body: JSON.stringify({ intents }),
              });
              const payload = await resp.json().catch(() => ({}));
              if (!resp.ok) throw new Error("intent_override_failed");
              if (payload?.controls && typeof payload.controls === "object") {
                this.applyIntentControls(payload.controls);
              }
              this.toast("Intent override updated.");
            } catch {
              this.toast("Failed to update intent override.");
            } finally {
              this.intentControlSaving = false;
            }
          },

          async previewIntentRoute() {
            this.routePreviewLoading = true;
            try {
              const resp = await fetch("/api/intents/preview", {
                method: "POST",
                headers: { "content-type": "application/json", accept: "application/json" },
                body: JSON.stringify({
                  profile: this.intentProfile,
                  override_intents: String(this.intentOverrideInput || "")
                    .split(",")
                    .map((value) => value.trim().toLowerCase())
                    .filter((value) => value),
                  transcript: this.transcriptPlainText(),
                  tags: this.meetingTags,
                }),
              });
              const payload = await resp.json().catch(() => ({}));
              if (!resp.ok) throw new Error("intent_preview_failed");
              if (payload?.route && typeof payload.route === "object") {
                this.routePreview = payload.route;
              }
            } catch {
              this.toast("Failed to preview route.");
            } finally {
              this.routePreviewLoading = false;
            }
          },

          connect() {
            if (this.closedByUser) return;
            if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return;

            this.connectionState = this.reconnectAttempt ? "reconnecting" : "connecting";
            this.reconnectAt = null;

            try {
              this.ws = new WebSocket(this.wsUrl());
            } catch {
              this.scheduleReconnect("ws_create_failed");
              return;
            }

            this.ws.onopen = () => {
              this.connectionState = "connected";
              this.reconnectAttempt = 0;
              this.reconnectAt = null;
              this.startPing();
              this.toast("Connected to meeting stream.");
            };

            this.ws.onmessage = (event) => {
              const msg = typeof event.data === "string" ? safeJsonParse(event.data) : null;
              if (!msg || typeof msg.type !== "string") return;
              this.handleMessage(msg);
            };

            this.ws.onerror = () => {};

            this.ws.onclose = () => {
              this.connectionState = "disconnected";
              this.stopPing();
              this.ws = null;
              if (!this.closedByUser) this.scheduleReconnect("ws_closed");
            };
          },

          startPing() {
            this.stopPing();
            this.pingTimer = window.setInterval(() => {
              if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
              try {
                this.ws.send("ping");
              } catch {}
            }, 15000);
          },

          stopPing() {
            if (this.pingTimer) window.clearInterval(this.pingTimer);
            this.pingTimer = null;
          },

          scheduleReconnect(reason) {
            if (this.closedByUser) return;
            if (this.reconnectTimer) return;

            this.reconnectAttempt = Math.min(this.reconnectAttempt + 1, 8);
            const base = 500 * Math.pow(2, this.reconnectAttempt - 1);
            const delay = Math.min(12000, base + Math.floor(Math.random() * 400));
            this.connectionState = "reconnecting";
            this.reconnectAt = Date.now() + delay;

            this.reconnectTimer = window.setTimeout(() => {
              this.reconnectTimer = null;
              this.connect();
            }, delay);

            if (reason) this.toast("Connection lost. Reconnecting...");
          },

          handleMessage(msg) {
            const { type, data } = msg;
            if (type === "duration") {
              if (typeof data === "string") this.duration = data;
              return;
            }
            if (type === "segment") {
              this.meetingActive = true;
              this.addSegment(data || {});
              return;
            }
            if (type === "intel") {
              this.updateIntel(data || {});
              return;
            }
            if (type === "intel_status") {
              if (data && typeof data === "object") this.intelStatus = data;
              return;
            }
            if (type === "intel_token") {
              if (!this.intelStreaming) {
                this.intelBuffer = "";
                this.intelStreaming = true;
              }
              this.intelBuffer += data;
              return;
            }
            if (type === "intel_complete") {
              this.updateIntel(data || {});
              this.intelBuffer = "";
              this.intelStreaming = false;
              return;
            }
            if (type === "bookmark") {
              this.addBookmark(data || {});
              return;
            }
            if (type === "action_item_updated") {
              this.updateActionItemInList(data || {});
              return;
            }
            if (type === "meeting_started") {
              this.meetingActive = true;
              this.startInProgress = false;
              if (data && typeof data === "object") {
                this.applyState(data, { replaceTimeline: true });
              } else {
                this.fetchInitialState();
              }
              this.toast("Meeting started.");
              return;
            }
            if (type === "stopped") {
              this.meetingActive = false;
              this.stopInProgress = false;
              if (data && typeof data === "object" && data.meeting && typeof data.meeting === "object") {
                this.applyState(data.meeting, { replaceTimeline: true });
              } else {
                this.fetchInitialState();
              }
              this.loadPluginJobs();
              this.loadPluginJobSummary();
              this.toast("Meeting stopped.");
              return;
            }
            if (type === "meeting_updated") {
              if (typeof data?.title !== "undefined") {
                this.meetingTitle = data.title || "";
              }
              if (Array.isArray(data?.tags)) {
                this.meetingTags = data.tags;
              }
              return;
            }
            if (type === "intent_controls_updated") {
              if (data && typeof data === "object") {
                this.applyIntentControls(data);
              }
              return;
            }
            if (type === "plugin_jobs_processed") {
              this.loadPluginJobs();
              this.loadPluginJobSummary();
            }
          },

          timeLabel(value) {
            if (typeof value === "number") return formatSeconds(value);
            if (typeof value === "string" && value.trim()) return value.trim();
            return "";
          },

          addSegment(data) {
            const speaker = data?.speaker ?? "Unknown";
            const start = this.timeLabel(data?.start_time);
            const end = this.timeLabel(data?.end_time);
            const text = String(data?.text ?? "").trim();
            if (!text) return;

            const segment = {
              kind: "segment",
              id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
              speaker,
              start,
              end,
              text,
              receivedAt: new Date().toISOString(),
            };

            this.segments.push(segment);
            this.entries.push(segment);
            if (this.entries.length > MAX_ENTRIES) this.entries.splice(0, this.entries.length - MAX_ENTRIES);
            this.$nextTick(() => this.scrollTranscriptToBottom());
          },

          addBookmark(data) {
            const timestamp = data?.timestamp ?? data?.time ?? "";
            const label = String(data?.label ?? "Bookmark").trim() || "Bookmark";
            const entry = {
              kind: "bookmark",
              id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
              label,
              timestamp: this.timeLabel(timestamp),
            };
            this.entries.push(entry);
            if (this.entries.length > MAX_ENTRIES) this.entries.splice(0, this.entries.length - MAX_ENTRIES);
            this.toast(`Saved bookmark: ${label}`);
            this.$nextTick(() => this.scrollTranscriptToBottom());
          },

          updateIntel(data) {
            const topics = Array.isArray(data?.topics) ? data.topics.filter((t) => typeof t === "string") : [];
            const action_items = Array.isArray(data?.action_items) ? data.action_items : [];
            const summary = typeof data?.summary === "string" ? data.summary : "";

            this.intel = {
              topics,
              action_items: action_items.map((item) => ({
                id: String(item?.id ?? "").trim(),
                task: String(item?.task ?? "").trim(),
                owner: String(item?.owner ?? "").trim(),
                due: String(item?.due ?? "").trim(),
                status: String(item?.status ?? "pending").trim().toLowerCase() || "pending",
                review_state: String(item?.review_state ?? "pending").trim().toLowerCase() || "pending",
                reviewed_at: String(item?.reviewed_at ?? "").trim(),
              })),
              summary,
            };
          },

          updateActionItemInList(updatedItem) {
            const idx = this.intel.action_items.findIndex((item) => item.id === updatedItem.id);
            if (idx >= 0) {
              this.intel.action_items[idx] = {
                id: String(updatedItem?.id ?? "").trim(),
                task: String(updatedItem?.task ?? "").trim(),
                owner: String(updatedItem?.owner ?? "").trim(),
                due: String(updatedItem?.due ?? "").trim(),
                status: String(updatedItem?.status ?? "pending").trim().toLowerCase() || "pending",
                review_state: String(updatedItem?.review_state ?? "pending").trim().toLowerCase() || "pending",
                reviewed_at: String(updatedItem?.reviewed_at ?? "").trim(),
              };
            }
          },

          async toggleActionItemStatus(item) {
            if (!item.id) return;
            const newStatus = item.status === "done" ? "pending" : "done";

            try {
              const resp = await fetch(`/api/action-items/${item.id}`, {
                method: "PATCH",
                headers: { "content-type": "application/json", accept: "application/json" },
                body: JSON.stringify({ status: newStatus }),
              });
              if (!resp.ok) throw new Error("update_failed");
            } catch {
              this.toast("Failed to update action item.");
            }
          },

          async dismissActionItem(item) {
            if (!item.id) return;

            try {
              const resp = await fetch(`/api/action-items/${item.id}`, {
                method: "PATCH",
                headers: { "content-type": "application/json", accept: "application/json" },
                body: JSON.stringify({ status: "dismissed" }),
              });
              if (!resp.ok) throw new Error("dismiss_failed");
            } catch {
              this.toast("Failed to dismiss action item.");
            }
          },

          async acceptActionItem(item) {
            if (!item.id) return;

            try {
              const resp = await fetch(`/api/action-items/${item.id}/review`, {
                method: "PATCH",
                headers: { "content-type": "application/json", accept: "application/json" },
                body: JSON.stringify({ review_state: "accepted" }),
              });
              if (!resp.ok) throw new Error("review_failed");
            } catch {
              this.toast("Failed to accept action item.");
            }
          },

          async retryPluginJob(jobId) {
            const id = Number(jobId);
            if (!Number.isInteger(id) || id <= 0) return;
            this.processingPluginJobs = true;
            try {
              const resp = await fetch(`/api/plugin-jobs/${id}/retry-now`, {
                method: "POST",
                headers: { accept: "application/json" },
              });
              if (!resp.ok) throw new Error("plugin_retry_failed");
              await Promise.all([this.loadPluginJobs(), this.loadPluginJobSummary()]);
              this.toast("Deferred plugin job queued for immediate retry.");
            } catch {
              this.toast("Failed to retry deferred plugin job.");
            } finally {
              this.processingPluginJobs = false;
            }
          },

          async cancelPluginJob(jobId) {
            const id = Number(jobId);
            if (!Number.isInteger(id) || id <= 0) return;
            this.processingPluginJobs = true;
            try {
              const resp = await fetch(`/api/plugin-jobs/${id}/cancel`, {
                method: "POST",
                headers: { accept: "application/json" },
              });
              if (!resp.ok) throw new Error("plugin_cancel_failed");
              await Promise.all([this.loadPluginJobs(), this.loadPluginJobSummary()]);
              this.toast("Deferred plugin job canceled.");
            } catch {
              this.toast("Failed to cancel deferred plugin job.");
            } finally {
              this.processingPluginJobs = false;
            }
          },

          async processPluginJobs(mode = "respect_backoff") {
            const normalizedMode = String(mode || "respect_backoff").trim().toLowerCase();
            const maxJobs = Number.isFinite(this.pluginJobLimit) && this.pluginJobLimit > 0 ? this.pluginJobLimit : 20;
            this.processingPluginJobs = true;
            try {
              const resp = await fetch("/api/plugin-jobs/process", {
                method: "POST",
                headers: { "content-type": "application/json", accept: "application/json" },
                body: JSON.stringify({ mode: normalizedMode, max_jobs: maxJobs }),
              });
              if (!resp.ok) throw new Error("plugin_process_failed");
              const payload = await resp.json().catch(() => ({}));
              await Promise.all([this.loadPluginJobs(), this.loadPluginJobSummary()]);
              const count = Number(payload?.processed || 0);
              if (payload?.skipped_active_meeting) {
                this.toast("Queue processing is paused while a meeting is active.");
              } else {
                this.toast(`Processed ${count} deferred plugin job${count === 1 ? "" : "s"}.`);
              }
            } catch {
              this.toast("Failed to process deferred plugin jobs.");
            } finally {
              this.processingPluginJobs = false;
            }
          },

          async editActionItem(item) {
            if (!item.id) return;
            const taskRaw = window.prompt("Edit task", item.task || "");
            if (taskRaw === null) return;
            const task = String(taskRaw).trim();
            if (!task) {
              this.toast("Task cannot be empty.");
              return;
            }

            const ownerRaw = window.prompt("Owner (blank clears)", item.owner || "");
            if (ownerRaw === null) return;
            const dueRaw = window.prompt("Due (blank clears)", item.due || "");
            if (dueRaw === null) return;

            try {
              const resp = await fetch(`/api/action-items/${item.id}/edit`, {
                method: "PATCH",
                headers: { "content-type": "application/json", accept: "application/json" },
                body: JSON.stringify({
                  task,
                  owner: String(ownerRaw).trim(),
                  due: String(dueRaw).trim(),
                }),
              });
              if (!resp.ok) throw new Error("edit_failed");
            } catch {
              this.toast("Failed to edit action item.");
            }
          },

          scrollTranscriptToBottom() {
            const el = this.$refs.transcriptScroll;
            if (!el) return;
            el.scrollTop = el.scrollHeight;
          },

          transcriptPlainText() {
            return this.segments
              .map((s) => {
                const t = s.start ? `[${s.start}${s.end ? `-${s.end}` : ""}] ` : "";
                const who = s.speaker ? `${s.speaker}: ` : "";
                return `${t}${who}${s.text}`;
              })
              .join("\n");
          },

          transcriptMarkdown() {
            const lines = [];
            const title = this.meetingTitle || "HoldSpeak Meeting";
            lines.push(`# ${title}`);
            lines.push("");
            lines.push(`- Duration: ${this.duration}`);
            if (this.meetingTags.length) lines.push(`- Tags: ${this.meetingTags.join(", ")}`);
            if (this.intel.topics.length) lines.push(`- Topics: ${this.intel.topics.join(", ")}`);
            lines.push("");

            if (this.intel.summary) {
              lines.push("## Summary");
              lines.push("");
              lines.push(this.intel.summary);
              lines.push("");
            }

            if (this.activeActionItems().length) {
              lines.push("## Action Items");
              lines.push("");
              this.activeActionItems().forEach((item) => {
                const parts = [item.task || "Action item"];
                if (item.owner) parts.push(`owner: ${item.owner}`);
                if (item.due) parts.push(`due: ${item.due}`);
                if (item.status) parts.push(`status: ${item.status}`);
                if (item.review_state) parts.push(`review: ${item.review_state}`);
                lines.push(`- ${parts.join(" | ")}`);
              });
              lines.push("");
            }

            lines.push("## Transcript");
            lines.push("");
            if (!this.segments.length) {
              lines.push("_No transcript yet._");
            } else {
              this.segments.forEach((segment) => {
                const timing = segment.start ? `[${segment.start}${segment.end ? `-${segment.end}` : ""}] ` : "";
                lines.push(`- ${timing}${segment.speaker}: ${segment.text}`);
              });
            }

            return lines.join("\n");
          },

          async copyAll() {
            const text = this.transcriptPlainText();
            if (!text.trim()) {
              this.toast("Nothing to copy yet.");
              return;
            }
            const copied = await copyText(text);
            this.toast(copied ? "Copied transcript to clipboard." : "Copy failed.");
          },

          async copySegment(segment) {
            const prefix = segment.start ? `[${segment.start}${segment.end ? `-${segment.end}` : ""}] ` : "";
            const text = `${prefix}${segment.speaker}: ${segment.text}`.trim();
            const copied = await copyText(text);
            this.toast(copied ? `Copied ${segment.speaker} segment.` : "Copy failed.");
          },

          download(filename, content, mime) {
            const blob = new Blob([content], { type: mime || "text/plain;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
          },

          exportAs(format) {
            const stamp = new Date().toISOString().replace(/[:.]/g, "-");
            if (format === "txt") {
              this.download(`holdspeak-meeting-${stamp}.txt`, this.transcriptPlainText(), "text/plain;charset=utf-8");
              this.exportOpen = false;
              return;
            }
            if (format === "md") {
              this.download(`holdspeak-meeting-${stamp}.md`, this.transcriptMarkdown(), "text/markdown;charset=utf-8");
              this.exportOpen = false;
              return;
            }
            if (format === "json") {
              const payload = {
                exported_at: new Date().toISOString(),
                duration: this.duration,
                transcript: this.segments,
                intelligence: this.intel,
              };
              this.download(
                `holdspeak-meeting-${stamp}.json`,
                JSON.stringify(payload, null, 2),
                "application/json;charset=utf-8"
              );
              this.exportOpen = false;
            }
          },

          openBookmarkModal() {
            this.bookmarkLabel = "";
            this.bookmarkModalOpen = true;
            this.$nextTick(() => this.$refs.bookmarkInput?.focus?.());
          },

          async submitBookmark() {
            const label = String(this.bookmarkLabel || "").trim();
            try {
              const resp = await fetch("/api/bookmark", {
                method: "POST",
                headers: { "content-type": "application/json", accept: "application/json" },
                body: JSON.stringify({ label }),
              });
              if (!resp.ok) throw new Error("bookmark_failed");
              this.toast("Bookmark requested.");
            } catch {
              this.toast("Bookmark failed.");
            } finally {
              this.bookmarkModalOpen = false;
              this.bookmarkLabel = "";
            }
          },

          openMetadataModal() {
            this.editingTitle = this.meetingTitle;
            this.editingTags = this.meetingTags.join(", ");
            this.metadataModalOpen = true;
            this.$nextTick(() => this.$refs.titleInput?.focus?.());
          },

          async saveMetadata() {
            const title = String(this.editingTitle || "").trim();
            const tagsStr = String(this.editingTags || "");
            const tags = tagsStr
              .split(",")
              .map((tag) => tag.trim().toLowerCase())
              .filter((tag) => tag);

            try {
              const resp = await fetch("/api/meeting", {
                method: "PATCH",
                headers: { "content-type": "application/json", accept: "application/json" },
                body: JSON.stringify({ title, tags }),
              });
              const payload = await resp.json().catch(() => ({}));
              if (!resp.ok) throw new Error("metadata_failed");
              if (payload?.meeting && typeof payload.meeting === "object") {
                this.applyState(payload.meeting);
              } else {
                await this.fetchInitialState();
              }
              this.toast("Meeting details saved.");
            } catch {
              this.toast("Failed to save meeting details.");
            } finally {
              this.metadataModalOpen = false;
            }
          },

          async startMeeting() {
            if (this.meetingActive || this.startInProgress) return;
            this.startInProgress = true;
            try {
              const resp = await fetch("/api/meeting/start", { method: "POST", headers: { accept: "application/json" } });
              if (!resp.ok) throw new Error("start_failed");
              const payload = await resp.json().catch(() => ({}));
              this.meetingActive = true;
              if (payload?.meeting && typeof payload.meeting === "object") {
                this.applyState(payload.meeting, { replaceTimeline: true });
              } else {
                await this.fetchInitialState();
              }
              this.toast("Meeting started.");
            } catch {
              this.toast("Start failed.");
            } finally {
              this.startInProgress = false;
            }
          },

          async stopMeeting() {
            if (!this.meetingActive || this.stopInProgress) return;
            const ok = window.confirm("Stop the meeting session?");
            if (!ok) return;
            this.stopInProgress = true;
            try {
              const resp = await fetch("/api/meeting/stop", { method: "POST", headers: { accept: "application/json" } });
              if (!resp.ok) throw new Error("stop_failed");
              const payload = await resp.json().catch(() => ({}));
              this.meetingActive = false;
              if (payload?.meeting && typeof payload.meeting === "object") {
                this.applyState(payload.meeting, { replaceTimeline: true });
              } else {
                await this.fetchInitialState();
              }
              if (typeof payload?.save_error === "string" && payload.save_error) {
                this.toast(`Stopped; save warning: ${payload.save_error}`);
              } else {
                this.toast("Meeting stopped.");
              }
              await Promise.all([this.loadPluginJobs(), this.loadPluginJobSummary()]);
            } catch {
              this.toast("Stop failed.");
            } finally {
              this.stopInProgress = false;
            }
          },

          toast(message) {
            const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
            this.notifications.push({ id, message });
            window.setTimeout(() => {
              const idx = this.notifications.findIndex((note) => note.id === id);
              if (idx >= 0) this.notifications.splice(idx, 1);
            }, 3500);
          },
        };
      }
