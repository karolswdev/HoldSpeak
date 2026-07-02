// HS-69-12: the Companion Agent Desk — the web /companion becomes the same desk
// surface as the iPad (HSM-15-08), not a plainer control panel. A living desk of
// the real agents + the live companion link (awaiting coding sessions), Signal-
// crafted, fed by the existing HTTP API (no backend change):
//   • /api/agents              — the agent personas (desk cards)
//   • /api/coders/status    — the device link + the coders awaiting you
//
// Framework-free where it can be; this is the page's Alpine factory (the desk
// is read-and-arrange, like /desk). Exposed on window for x-data.

// Loaded via `?raw` + `new Function` (the repo's Alpine-factory pattern), so
// this is a plain declaration — no ES `export`.
function companionDesk() {
  return {
    agents: [],
    status: null,
    loading: true,
    _poll: null,

    async init() {
      await Promise.all([this.loadAgents(), this.loadStatus()]);
      this.loading = false;
      this._poll = window.setInterval(() => this.loadStatus(), 5000);
    },
    destroy() {
      if (this._poll) window.clearInterval(this._poll);
    },

    async loadAgents() {
      try {
        const r = await fetch("/api/agents");
        const d = await r.json();
        this.agents = (d && d.agents) || [];
      } catch (_e) {
        this.agents = [];
      }
    },
    async loadStatus() {
      try {
        const r = await fetch("/api/coders/status");
        this.status = await r.json();
      } catch (_e) {
        this.status = null;
      }
    },

    get sessions() {
      return (this.status && this.status.agent_sessions) || [];
    },
    get awaiting() {
      return this.sessions.filter((s) => s && s.awaiting_response);
    },
    get connected() {
      return !!(this.status && (this.status.device_connected || this.sessions.length));
    },
    get linkLabel() {
      if (!this.status) return "Checking link…";
      if (this.awaiting.length) return `${this.awaiting.length} need you`;
      if (this.connected) return "Companion linked";
      return "No companion linked";
    },
    get linkScope() {
      if (this.awaiting.length) return "needs";
      return this.connected ? "ok" : "idle";
    },

    agentTools(agent) {
      return (agent && agent.tools) || [];
    },
    sessionLabel(s) {
      return (s && (s.agent || s.session_id)) || "session";
    },
  };
}
