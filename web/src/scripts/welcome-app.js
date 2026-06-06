// HS-43-01: the full-screen first-run wizard state machine.
//
// Funnel / progressive disclosure — one decision per step, Step N of M, Skip +
// Back (user freedom), focus moves to the step heading on each transition,
// motion respects prefers-reduced-motion. Driven by the Phase-42 plumbing:
// GET /api/setup/status (permissions/model) + the runtime_activity websocket
// (the live first-dictation moment). No backend rewrite.
function welcomeApp() {
  const STEPS = [
    { id: "welcome", label: "Welcome", skippable: false },
    { id: "permissions", label: "Permissions", skippable: true },
    { id: "model", label: "Model", skippable: true },
    { id: "dictation", label: "First dictation", skippable: true },
    { id: "presence", label: "Presence", skippable: true },
    { id: "done", label: "You're set", skippable: false },
  ];

  return {
    steps: STEPS,
    i: 0,
    dir: "fwd",
    leaving: -1, // index currently animating out
    status: null,
    reduceMotion: false,

    // live first-dictation state (fed by the runtime_activity WS)
    activity: null,
    dictation: { ok: false, transcript: "" },

    // presence toggle (wired to the backend in HS-43-04)
    presenceOn: false,

    init() {
      try {
        this.reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      } catch (_e) {}
      this.loadStatus();
      this.connectActivity();
      this.focusHeading();
      // Esc is *not* a trap — let people leave to the dashboard.
    },

    get step() {
      return this.steps[this.i];
    },
    get atFirst() {
      return this.i === 0;
    },
    get atLast() {
      return this.i === this.steps.length - 1;
    },
    get progressPct() {
      return Math.round((this.i / (this.steps.length - 1)) * 100);
    },
    isActive(id) {
      return this.step.id === id;
    },
    isDone(idx) {
      return idx < this.i;
    },

    primaryLabel() {
      if (this.atLast) return "Open HoldSpeak";
      if (this.step.id === "welcome") return "Get started";
      return "Continue";
    },

    next() {
      if (this.atLast) {
        window.location.href = "/";
        return;
      }
      this.go(this.i + 1, "fwd");
    },
    back() {
      if (this.atFirst) return;
      this.go(this.i - 1, "back");
    },
    skip() {
      if (this.atLast) return;
      this.go(this.i + 1, "fwd");
    },
    go(target, dir) {
      if (target === this.i) return;
      this.dir = dir;
      this.leaving = this.i;
      this.i = target;
      // clear the leaving marker after the transition
      const clear = () => { this.leaving = -1; };
      if (this.reduceMotion) clear();
      else setTimeout(clear, 320);
      this.focusHeading();
    },

    focusHeading() {
      this.$nextTick(() => {
        const el = this.$refs[`heading_${this.step.id}`];
        if (el && el.focus) el.focus();
      });
    },

    // ── data ──
    async loadStatus() {
      try {
        const res = await fetch("/api/setup/status");
        if (res.ok) this.status = await res.json();
      } catch (_e) {}
    },
    // Read the OS dynamically — never hardcode "Mac".
    get osLabel() {
      const os = this.status?.presence?.os;
      return { macos: "Mac", linux: "Linux machine" }[os] || "system";
    },
    section(id) {
      return (this.status?.sections || []).find((s) => s.id === id) || null;
    },
    sectionStatus(id) {
      const s = this.section(id);
      return s ? s.status : "unknown";
    },

    // ── live first-dictation feedback ──
    connectActivity() {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      let ws;
      try {
        ws = new WebSocket(`${proto}//${window.location.host}/ws`);
      } catch (_e) {
        return;
      }
      ws.onmessage = (event) => {
        let msg;
        try { msg = JSON.parse(event.data); } catch (_e) { return; }
        if (msg && msg.type === "runtime_activity") this.onActivity(msg.data || {});
      };
      ws.onclose = () => setTimeout(() => this.connectActivity(), 2000);
    },
    async onActivity(data) {
      if (!data || data.source !== "dictation") return;
      this.activity = data;
      if (data.state === "complete" && ["dictation_typed", "dictation_delivered"].includes(data.last_event)) {
        await this.fetchTranscript();
        this.dictation.ok = true;
      }
    },
    async fetchTranscript() {
      try {
        const res = await fetch("/api/state");
        if (!res.ok) return;
        const s = await res.json();
        const t = (s.runtime && s.runtime.last_transcription) ||
          (s.runtime_status && s.runtime_status.last_transcription) || s.last_transcription;
        if (t) this.dictation.transcript = String(t);
      } catch (_e) {}
    },
    get liveLabel() {
      return {
        listening: "Listening",
        recording: "Recording",
        transcribing: "Transcribing",
        processing: "Processing",
        typing: "Typing it in",
      }[this.activity && this.activity.state] || "";
    },
  };
}
