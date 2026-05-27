function CompanionApp() {
  return {
    loading: true,
    error: "",
    status: null,
    updatedAt: null,
    refreshTimer: null,

    init() {
      this.refresh();
      this.refreshTimer = setInterval(() => this.refresh(), 3000);
    },

    async refresh() {
      try {
        const response = await fetch("/api/companion/status", {
          headers: { accept: "application/json" },
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.error || payload.detail || `HTTP ${response.status}`);
        }
        this.status = payload;
        this.error = "";
        this.updatedAt = new Date();
      } catch (err) {
        this.error = err instanceof Error ? err.message : String(err || "Refresh failed");
      } finally {
        this.loading = false;
      }
    },

    sessions() {
      const items = this.status?.agent?.sessions?.items;
      return Array.isArray(items) ? items : [];
    },

    selectedSession() {
      return this.sessions().find((item) => item?.selected) || null;
    },

    readinessTone() {
      if (!this.status) return "neutral";
      if (this.status.ready_for_agent_reply) return "ready";
      const blockers = this.status.blockers || [];
      if (blockers.includes("text_injection_unavailable")) return "blocked";
      if (blockers.includes("no_agent_waiting")) return "idle";
      return "warn";
    },

    readinessLabel() {
      const tone = this.readinessTone();
      if (tone === "ready") return "Reply ready";
      if (tone === "blocked") return "No reply target";
      if (tone === "idle") return "No waiting agent";
      if (tone === "warn") return "Needs attention";
      return "Loading";
    },

    confidenceTone(identity) {
      const confidence = String(identity?.target_confidence || "").toLowerCase();
      if (confidence === "high") return "ready";
      if (confidence === "medium") return "warn";
      if (confidence === "low") return "blocked";
      return "neutral";
    },

    confidenceLabel(identity) {
      const confidence = identity?.target_confidence || "unknown";
      const transport = identity?.target_transport || "unknown";
      return `${confidence} / ${transport}`;
    },

    compactLabel(item) {
      return item?.identity?.compact_label || item?.session?.agent || "Unknown session";
    },

    question(item) {
      return item?.session?.last_assistant_text || "No assistant question captured.";
    },

    sessionAge(item) {
      const stamp = item?.session?.updated_at || item?.session?.last_assistant_text_at;
      if (!stamp) return "unknown age";
      const parsed = Date.parse(stamp);
      if (Number.isNaN(parsed)) return "unknown age";
      const seconds = Math.max(0, Math.round((Date.now() - parsed) / 1000));
      if (seconds < 60) return `${seconds}s ago`;
      const minutes = Math.round(seconds / 60);
      if (minutes < 60) return `${minutes}m ago`;
      const hours = Math.round(minutes / 60);
      return `${hours}h ago`;
    },

    updatedLabel() {
      if (!this.updatedAt) return "not refreshed";
      return this.updatedAt.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    },

    blockerLabel(blocker) {
      const labels = {
        no_device_connected: "No AI PI connected",
        no_agent_waiting: "No agent waiting",
        dictation_pipeline_disabled: "Dictation pipeline disabled",
        text_injection_unavailable: "Text injection unavailable",
        text_injection_status_unknown: "Text injection status unknown",
        agent_status_unavailable: "Agent status unavailable",
        dictation_config_unavailable: "Dictation config unavailable",
        runtime_status_unavailable: "Runtime status unavailable",
      };
      return labels[blocker] || String(blocker || "unknown blocker");
    },
  };
}
