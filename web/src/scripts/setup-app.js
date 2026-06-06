// HS-42-03: the welcome / setup surface app.
//
// Driven entirely by GET /api/setup/status (the HS-42-01 adapter over the
// doctor + readiness + egress + presence). It shows one primary action, a
// status-grouped checklist (so every doctor FAIL surfaces), and a trust/presence
// summary — no nag for a healthy returning user (the / dashboard guard yields).
function setupApp() {
  return {
    status: null,
    loading: true,
    error: "",

    async init() {
      await this.load();
    },

    async load() {
      this.loading = true;
      this.error = "";
      try {
        const res = await fetch("/api/setup/status");
        if (!res.ok) throw new Error(`Request failed (${res.status})`);
        this.status = await res.json();
      } catch (e) {
        this.error = e.message || "Could not load setup status.";
        this.status = null;
      }
      this.loading = false;
    },

    get sections() {
      return this.status?.sections || [];
    },
    get unmet() {
      return this.sections.filter((s) => s.status === "fail" || s.status === "warn");
    },
    get ready() {
      return this.sections.filter((s) => s.status === "pass");
    },
    get unknown() {
      return this.sections.filter((s) => s.status === "unknown");
    },
    get passCount() {
      return this.ready.length;
    },
    get total() {
      return this.sections.length;
    },
    get overall() {
      return this.status?.overall || "unknown";
    },
    get headline() {
      if (this.overall === "ready") {
        return this.status?.first_run ? "You're ready — try your first dictation" : "Everything's ready";
      }
      const fails = this.sections.filter((s) => s.status === "fail").length;
      const warns = this.sections.filter((s) => s.status === "warn").length;
      const n = fails + warns;
      if (fails > 0) return `${n} thing${n === 1 ? "" : "s"} need${n === 1 ? "s" : ""} attention`;
      return `Almost there — ${n} optional item${n === 1 ? "" : "s"} to review`;
    },
    get subhead() {
      if (this.overall === "ready") {
        return "Hold your hotkey in any app, speak, release — text appears. Nothing leaves this machine.";
      }
      if (this.overall === "blocked") {
        return "One core check is failing. Fix it below and voice typing will be ready.";
      }
      return "Voice typing already works — these are optional or advisory.";
    },
    get progressPct() {
      if (!this.total) return 0;
      return Math.round((this.passCount / this.total) * 100);
    },

    statusGlyph(status) {
      return { pass: "✓", warn: "!", fail: "✕", unknown: "?" }[status] || "?";
    },

    egressLabel() {
      const t = this.status?.trust?.transcript_egress;
      return { none: "Local only", configured: "Configured endpoint", possible: "Cloud-capable" }[t] || "Local only";
    },
    presenceLabel() {
      const p = this.status?.presence;
      if (!p) return "—";
      if (!p.available) return "Not available on this platform";
      if (p.enabled) return `On · ${p.tier}`;
      return `Available · ${p.tier} (off)`;
    },
  };
}
