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
    // Live first-dictation tracking (HS-42-04), fed by the runtime_activity WS.
    activity: null,
    dictation: { ok: false, transcript: "" },
    // Model setup assistant (HS-42-06).
    runtimeTest: { state: "idle", ok: false, detail: "" },
    runtimeChoices: [
      { id: "basic", label: "Basic voice typing only", extra: null,
        needs: "Nothing — Whisper transcription only.", affects: "Dictation (no LLM rewrite)." },
      { id: "mlx", label: "Local Apple Silicon (MLX)", extra: "uv pip install -e '.[dictation-mlx]'",
        needs: "An MLX model under ~/Models/mlx/…", affects: "Dictation + meeting intel." },
      { id: "llama_cpp", label: "Local GGUF (llama.cpp)", extra: "uv pip install -e '.[dictation-llama]'",
        needs: "A GGUF model under ~/Models/gguf/…", affects: "Dictation + meeting intel." },
      { id: "openai_compatible", label: "OpenAI-compatible endpoint", extra: "uv pip install -e '.[dictation-openai]'",
        needs: "A base URL (LAN, Ollama, vLLM, or hosted).", affects: "Dictation + meeting intel." },
    ],
    copied: "",

    async testRuntime() {
      this.runtimeTest = { state: "testing", ok: false, detail: "" };
      try {
        const res = await fetch("/api/setup/runtime-test", { method: "POST" });
        const data = await res.json();
        this.runtimeTest = { state: "done", ok: !!data.ok, detail: data.detail || "" };
      } catch (e) {
        this.runtimeTest = { state: "done", ok: false, detail: e.message || "Test failed." };
      }
    },

    async copy(text) {
      try {
        await navigator.clipboard.writeText(text);
        this.copied = text;
        setTimeout(() => { if (this.copied === text) this.copied = ""; }, 1500);
      } catch (_e) { /* clipboard blocked; the command is visible to copy by hand */ }
    },

    async init() {
      await this.load();
      this.connectActivity();
    },

    // ── Live dictation feedback over the runtime_activity websocket ──────
    connectActivity() {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      let ws;
      try {
        ws = new WebSocket(`${proto}//${window.location.host}/ws`);
      } catch (_e) {
        return; // no live feedback; the page still works from /api/setup/status
      }
      ws.onmessage = (event) => {
        let msg;
        try {
          msg = JSON.parse(event.data);
        } catch (_e) {
          return;
        }
        if (msg && msg.type === "runtime_activity") this.onActivity(msg.data || {});
      };
      ws.onclose = () => setTimeout(() => this.connectActivity(), 2000);
    },

    async onActivity(data) {
      if (!data || data.source !== "dictation") return;
      this.activity = data;
      const success = data.state === "complete" &&
        ["dictation_typed", "dictation_delivered"].includes(data.last_event);
      if (success) {
        this.dictation.ok = true;
        await this.fetchTranscript();
        await this.load(); // refresh first_run (the milestone is now set)
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
      } catch (_e) {
        /* the success banner stands without the exact transcript */
      }
    },

    get liveLabel() {
      const st = this.activity && this.activity.state;
      return {
        listening: "Listening…",
        recording: "Recording…",
        transcribing: "Transcribing…",
        processing: "Processing…",
        typing: "Typing it into your app…",
      }[st] || "";
    },
    get firstDone() {
      return this.status ? this.status.first_run === false : false;
    },
    sectionById(id) {
      return this.sections.find((s) => s.id === id) || null;
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
    get presence() {
      return this.status?.presence || {};
    },
    get presenceTier() {
      const p = this.presence;
      if (p.os === "macos") return "A floating HUD of the Signal card + a menu-bar glyph.";
      if (p.os === "linux") {
        return p.tier === "hud"
          ? "A floating HUD (X11/wlroots) + a tray glyph + an in-place notification."
          : "A tray glyph + an in-place notification (your Wayland compositor blocks floating overlays).";
      }
      return "Not available on this platform.";
    },
    get presenceInstall() {
      const p = this.presence;
      const lines = [
        "HOLDSPEAK_DESKTOP_PRESENCE=1 holdspeak",
        "uv pip install -e '.[presence]'",
      ];
      if (p.os === "linux") {
        lines.push("sudo apt-get install gir1.2-notify-0.7 gir1.2-ayatanaappindicator3-0.1");
      }
      return lines;
    },
  };
}
