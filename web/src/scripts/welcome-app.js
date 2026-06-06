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

    // presence toggle (config-backed — HS-43-04; no env var)
    presenceOn: false,
    presenceSaving: false,
    presenceNote: "",

    hotkeyKey: "",

    init() {
      try {
        this.reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      } catch (_e) {}
      this.loadStatus();
      this.loadHotkey();
      this.connectActivity();
      this.focusHeading();
      // Esc is *not* a trap — let people leave to the dashboard.
    },

    settings: null,
    async loadHotkey() {
      try {
        const res = await fetch("/api/settings");
        if (res.ok) {
          this.settings = await res.json();
          this.hotkeyKey = (this.settings.hotkey && this.settings.hotkey.key) || "";
        }
      } catch (_e) {}
    },

    // ── Model picker (HS-43-02) ──
    modelChoices: [
      { id: "basic", label: "Basic voice typing", backend: "none", extra: null,
        blurb: "Just Whisper transcription. Works out of the box — nothing to install.", affects: "Dictation" },
      { id: "mlx", label: "Local · Apple Silicon", backend: "mlx", extra: "uv pip install -e '.[dictation-mlx]'",
        blurb: "Fast, private MLX inference on your Mac's GPU. Needs an MLX model.", affects: "Dictation + meetings" },
      { id: "llama_cpp", label: "Local · GGUF", backend: "llama_cpp", extra: "uv pip install -e '.[dictation-llama]'",
        blurb: "Any GGUF model via llama.cpp, on any machine.", affects: "Dictation + meetings" },
      { id: "openai_compatible", label: "OpenAI-compatible", backend: "openai_compatible", extra: "uv pip install -e '.[dictation-openai]'",
        blurb: "Point at a LAN, Ollama, vLLM, or hosted /v1 endpoint.", affects: "Dictation + meetings" },
    ],
    modelTest: { state: "idle", ok: false, detail: "" },
    modelSaving: false,
    copied: "",

    get selectedModel() {
      const d = this.settings && this.settings.dictation;
      if (!d || !d.pipeline || !d.pipeline.enabled) return "basic";
      const backend = (d.runtime && d.runtime.backend) || "auto";
      return ["mlx", "llama_cpp", "openai_compatible"].includes(backend) ? backend : "basic";
    },
    async selectModel(choice) {
      this.modelSaving = true;
      this.modelTest = { state: "idle", ok: false, detail: "" };
      const payload = choice.id === "basic"
        ? { dictation: { pipeline: { enabled: false } } }
        : { dictation: { pipeline: { enabled: true }, runtime: { backend: choice.backend } } };
      try {
        const res = await fetch("/api/settings", {
          method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
        });
        if (res.ok) {
          const data = await res.json();
          this.settings = data.settings || this.settings;
        }
      } catch (_e) {}
      this.modelSaving = false;
    },
    async testModel() {
      this.modelTest = { state: "testing", ok: false, detail: "" };
      try {
        const res = await fetch("/api/setup/runtime-test", { method: "POST" });
        const d = await res.json();
        this.modelTest = { state: "done", ok: !!d.ok, detail: d.detail || "" };
      } catch (e) {
        this.modelTest = { state: "done", ok: false, detail: e.message || "Test failed." };
      }
    },
    async copy(text) {
      try { await navigator.clipboard.writeText(text); this.copied = text; setTimeout(() => { if (this.copied === text) this.copied = ""; }, 1500); } catch (_e) {}
    },
    get hotkeyLabel() {
      const map = {
        alt_r: "Right ⌥ / Alt", alt_l: "Left ⌥ / Alt",
        ctrl_r: "Right Ctrl", ctrl_l: "Left Ctrl",
        cmd_r: "Right ⌘", cmd_l: "Left ⌘",
        shift_r: "Right Shift", shift_l: "Left Shift",
        caps_lock: "Caps Lock", fn: "Fn",
      };
      if (!this.hotkeyKey) return "your hotkey";
      if (map[this.hotkeyKey]) return map[this.hotkeyKey];
      return this.hotkeyKey.toUpperCase().replace("_", " ");
    },
    get dictating() {
      const st = this.activity && this.activity.state;
      return ["listening", "recording", "transcribing", "processing", "typing"].includes(st);
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
        if (res.ok) {
          this.status = await res.json();
          this.presenceOn = !!(this.status.presence && this.status.presence.enabled);
        }
      } catch (_e) {}
    },
    get presenceAvailable() {
      return !!(this.status && this.status.presence && this.status.presence.available);
    },
    // HS-43-04: flip the config-backed presence toggle — no env var, no relaunch.
    async togglePresence() {
      const next = !this.presenceOn;
      this.presenceSaving = true;
      this.presenceNote = "";
      try {
        const res = await fetch("/api/settings", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ presence: { enabled: next } }),
        });
        if (!res.ok) throw new Error(`Request failed (${res.status})`);
        this.presenceOn = next;
        this.presenceNote = next
          ? (this.presenceAvailable ? "On — the HUD appears the next time you dictate." : "Saved — install the presence extra to see it (below).")
          : "Off.";
      } catch (e) {
        this.presenceNote = `Couldn't save: ${e.message}`;
      }
      this.presenceSaving = false;
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
        // a11y: move focus to the celebration heading when it replaces the prompt.
        if (this.isActive("dictation")) {
          this.$nextTick(() => {
            const el = this.$refs.heading_dictation_win;
            if (el && el.focus) el.focus();
          });
        }
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
