// HS-42-02: the global Settings surface app.
//
// The "History → Settings" content lifted out of the History page into a real,
// shell-level /settings route (completing the HS-30-08 move). It owns the full
// global config form — Appearance, Core, Cloud intel — backed by GET/PUT
// /api/settings, with the same validation the old tab used (ported verbatim).
function settingsApp() {
  return {
    settings: null,
    loading: true,
    saving: false,
    errors: [],
    message: "",
    isError: false,
    _timer: null,

    // HS-43-05: sectioned + searchable + progressive.
    sections: [
      { id: "appearance", label: "Appearance" },
      { id: "voice", label: "Voice typing" },
      { id: "presence", label: "Desktop presence" },
      { id: "meetings", label: "Meetings & intel" },
      { id: "cloud", label: "Cloud & advanced" },
    ],
    active: "appearance",
    query: "",
    showAdvanced: false,

    get searching() {
      return this.query.trim().length > 0;
    },
    // A field is visible if it matches the search, or it's in the active section
    // (and either common, or advanced-disclosure is on). `keywords` lets search
    // find a field by more than its label.
    fieldVisible(section, tier, keywords) {
      if (this.searching) {
        return String(keywords || "").toLowerCase().includes(this.query.trim().toLowerCase());
      }
      return section === this.active && (tier !== "advanced" || this.showAdvanced);
    },
    sectionVisible(section) {
      if (this.searching) return false; // search flattens; section chrome hides
      return section === this.active;
    },
    sectionHasAdvanced(_section) {
      return true; // cloud/meetings carry advanced fields; the toggle is harmless elsewhere
    },

    async init() {
      await this.load();
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
      this.message = String(message || "").trim();
      this.isError = Boolean(isError);
      if (this._timer) clearTimeout(this._timer);
      if (!this.message) return;
      this._timer = setTimeout(() => {
        this.message = "";
      }, isError ? 8000 : 4000);
    },

    async load() {
      this.loading = true;
      try {
        this.settings = await this.apiJson("/api/settings");
        this.errors = [];
      } catch (error) {
        console.error("Failed to load settings:", error);
        this.settings = null;
        this.flash(`Could not load settings: ${error.message}`, true);
      }
      this.loading = false;
    },

    async save() {
      if (!this.settings) return;
      this.saving = true;
      this.errors = [];
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

        const validationErrors = this.validate(payload);
        if (validationErrors.length > 0) {
          this.errors = validationErrors;
          this.flash(validationErrors[0], true);
          this.saving = false;
          return;
        }

        const data = await this.apiJson("/api/settings", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        this.settings = data.settings || payload;
        this.errors = [];
        this.flash("Settings saved. Runtime configuration updated.");
      } catch (error) {
        console.error("Failed to save settings:", error);
        this.flash(`Settings save failed: ${error.message}`, true);
      }
      this.saving = false;
    },

    validate(payload) {
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
  };
}
