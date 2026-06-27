/*
 * DeskApp — the web Desk's Alpine controller for the Primitive Framework.
 *
 * LIVE against the desktop hub. Every lane reads real primitives from the hub
 * and authors back to it where a write route exists:
 *
 *   Notes   — GET/POST /api/notes              (LIVE read + author)
 *   Agents  — GET/POST /api/agents             (LIVE read + author)
 *   Meetings— GET /api/meetings                (LIVE read)
 *   Artifact— GET /api/sync/pull               (LIVE read)
 *   KB      — GET /api/sync/pull (kbs[])       (LIVE read · no create route yet)
 *   Chain   — GET /api/sync/pull (chains[])    (LIVE read · no create route yet)
 *   Workflow— GET /api/sync/pull (workflows[]) (LIVE read · no create route yet)
 *   Coder   — GET /api/companion/status        (LIVE presence, 4s poll)
 *
 * The sync-pull primitives arrive as `{meta:{id,kind,last_modified,deleted},
 * value:{...}}` change-set records; we drop tombstones (`deleted`) on read.
 *
 * Honesty model (no fake data):
 *   - reachable + has route → live cards (no badge).
 *   - reachable + no create route (kb/chain/workflow) → "read-only" badge.
 *   - hub unreachable for a lane → "hub unreachable" badge + empty lane.
 *
 * Wire is snake_case; mapped to the camelCase in lib/primitives.ts at the
 * boundary (fromWire*). The descriptor table lives in the page (DESK_META) so
 * the renderer is fully data-driven and type-legible.
 *
 * REMAINING hub gaps (flagged "read-only" in the UI, no local mock):
 *   POST /api/kbs        — KB create not on the hub yet (sync push only).
 *   POST /api/chains     — Chain create not on the hub yet.
 *   POST /api/workflows  — Workflow create not on the hub yet.
 */
function DeskApp() {
  return {
    loading: true,
    error: "",
    updatedAt: null,
    coderTimer: null,
    coderReady: false,
    coderBlockers: [],

    // ── the store, by kind ──
    items: {
      meeting: [],
      artifact: [],
      note: [],
      kb: [],
      agent: [],
      chain: [],
      workflow: [],
      coder: [],
    },
    // Per-kind status: "live" | "readonly" | "unreachable".
    status: {},

    // ── authoring ──
    creating: null, // "note" | "agent" | null
    busy: false,
    noteForm: { title: "", body: "", tags: "" },
    agentForm: {
      name: "",
      avatar: "🤖",
      role: "",
      systemPrompt: "",
      userTemplate: "",
      tools: "",
      kbId: "",
    },

    async init() {
      await this.loadAll();
      this.loading = false;
      this.refreshCoders();
      this.coderTimer = setInterval(() => this.refreshCoders(), 4000);
    },

    // ── totals + grouping helpers (data-driven by the page descriptor) ──
    count(kind) {
      return (this.items[kind] || []).length;
    },
    total() {
      return Object.values(this.items).reduce((n, l) => n + l.length, 0);
    },
    /** A kind reachable on the hub but with no create route → read-only. */
    isReadonly(kind) {
      return this.status[kind] === "readonly";
    },
    /** The hub could not be reached for this kind. */
    isUnreachable(kind) {
      return this.status[kind] === "unreachable";
    },

    updatedLabel() {
      if (!this.updatedAt) return "not loaded";
      const secs = Math.max(0, Math.round((Date.now() - this.updatedAt) / 1000));
      if (secs < 5) return "just now";
      if (secs < 60) return `${secs}s ago`;
      return `${Math.round(secs / 60)}m ago`;
    },

    async fetchJson(url, opts) {
      const res = await fetch(url, opts);
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.error || body.detail || `HTTP ${res.status}`);
      return body;
    },

    async loadAll() {
      await Promise.allSettled([
        this.loadMeetings(),
        this.loadSyncPrimitives(), // artifacts + kb/chain/workflow (one pull)
        this.loadNotes(),
        this.loadAgents(),
      ]);
      this.updatedAt = Date.now();
    },

    async refresh() {
      this.loading = true;
      this.error = "";
      await this.loadAll();
      await this.refreshCoders();
      this.loading = false;
    },

    // ── content: meetings (live) ──
    async loadMeetings() {
      try {
        const data = await this.fetchJson("/api/meetings?limit=24");
        this.items.meeting = (data.meetings || []).map((m) => ({
          kind: "meeting",
          id: m.id,
          title: m.title || "Untitled meeting",
          startedAt: m.started_at,
          endedAt: m.ended_at,
          segmentCount: m.segment_count,
          actionItemCount: m.action_item_count,
          durationSeconds: m.duration_seconds,
          tags: m.tags || [],
          intelStatus: m.intel_status,
        }));
        this.status.meeting = "live";
      } catch (e) {
        this.status.meeting = "unreachable";
        if (!this.error) this.error = `Meetings: ${e.message}`;
      }
    },

    // ── content/organization/capability: one sync pull ──
    // The hub serializes artifacts + kb/chain/workflow as {meta, value}
    // change-set records on the sync channel. KB/Chain/Workflow have no
    // dedicated REST list/create routes yet, so this read IS their live source.
    async loadSyncPrimitives() {
      let data;
      try {
        data = await this.fetchJson("/api/sync/pull?limit=50");
      } catch (e) {
        for (const k of ["artifact", "kb", "chain", "workflow"]) {
          this.status[k] = "unreachable";
        }
        if (!this.error) this.error = `Hub sync: ${e.message}`;
        return;
      }

      // Artifacts (live, read-only by nature — synthesized from meetings).
      const arts = this.liveValues(data.artifacts);
      this.items.artifact = arts.slice(0, 24).map((a) => ({
        kind: "artifact",
        id: a.id,
        meetingId: a.meeting_id,
        artifactType: a.artifact_type,
        title: a.title || a.artifact_type || "Artifact",
        bodyMarkdown: a.body_markdown || "",
        status: a.status,
        confidence: a.confidence,
        sources: a.sources || [],
      }));
      this.status.artifact = "live";

      // KB (live read; no create route → read-only on web).
      this.items.kb = this.liveValues(data.kbs).map((k) => ({
        kind: "kb",
        id: k.id,
        name: k.name,
        memberIds: k.member_ids || [],
        createdAt: k.created_at,
      }));
      this.status.kb = "readonly";

      // Chain (live read; no create route → read-only on web).
      this.items.chain = this.liveValues(data.chains).map((c) => ({
        kind: "chain",
        id: c.id,
        name: c.name,
        steps: c.steps || [],
      }));
      this.status.chain = "readonly";

      // Workflow (live read; no create route → read-only on web).
      this.items.workflow = this.liveValues(data.workflows).map((w) => ({
        kind: "workflow",
        id: w.id,
        name: w.name,
        prompt: w.prompt,
        graphJson: w.graph_json,
      }));
      this.status.workflow = "readonly";
    },

    /** Unwrap {meta,value} change-set records, dropping tombstones. */
    liveValues(records) {
      return (records || [])
        .filter((rec) => !(rec && rec.meta && rec.meta.deleted))
        .map((rec) => (rec && rec.value ? rec.value : rec))
        .filter(Boolean);
    },

    // ── content: notes (LIVE — GET/POST /api/notes) ──
    async loadNotes() {
      try {
        const data = await this.fetchJson("/api/notes");
        this.items.note = (data.notes || [])
          .filter((n) => !n.deleted)
          .map(this.fromWireNote);
        this.status.note = "live";
      } catch (e) {
        this.status.note = "unreachable";
        this.items.note = [];
        if (!this.error) this.error = `Notes: ${e.message}`;
      }
    },

    fromWireNote(n) {
      return {
        kind: "note",
        id: n.id,
        title: n.title,
        bodyMarkdown: n.body_markdown,
        tags: n.tags || [],
        createdAt: n.created_at,
      };
    },

    // ── capability: agents (LIVE — GET/POST /api/agents) ──
    async loadAgents() {
      try {
        const data = await this.fetchJson("/api/agents");
        this.items.agent = (data.agents || [])
          .filter((a) => !a.deleted)
          .map(this.fromWireAgent);
        this.status.agent = "live";
      } catch (e) {
        this.status.agent = "unreachable";
        this.items.agent = [];
        if (!this.error) this.error = `Agents: ${e.message}`;
      }
    },

    fromWireAgent(a) {
      return {
        kind: "agent",
        id: a.id,
        name: a.name,
        avatar: a.avatar || "🤖",
        role: a.role || "",
        systemPrompt: a.system_prompt || "",
        userTemplate: a.user_template || "",
        tools: a.tools || [],
        kbId: a.kb_id || null,
      };
    },

    // ── coder lane (live presence stream) ──
    // The hub nests waiting sessions at agent.sessions.items[] — each item is
    // {index, selected, pinned, stale, age_seconds, session, identity}, and the
    // session payload is AgentSession.to_dict(). The legacy data.sessions /
    // data.agent.sessions[] paths are kept as defensive fallbacks.
    async refreshCoders() {
      try {
        const data = await this.fetchJson("/api/companion/status");
        const items = this.coderSessionItems(data);
        this.items.coder = items.map((item, i) => {
          const s = item.session || item;
          const identity = item.identity || {};
          return {
            kind: "coder",
            agent: s.agent === "codex" ? "codex" : "claude",
            sessionId: s.session_id || `s${i}`,
            project: s.project || s.cwd || s.project_name || "",
            model: s.model || "",
            state:
              s.state ||
              (s.awaiting_response ? "waiting" : "running"),
            question:
              identity.question ||
              s.question ||
              s.last_question ||
              (s.awaiting_response ? identity.prompt || null : null),
            selected: Boolean(item.selected),
            pinned: Boolean(item.pinned ?? s.pinned),
            stale: Boolean(item.stale),
            events: s.events || [],
          };
        });
        this.coderReady = Boolean(data?.ready_for_agent_reply);
        this.coderBlockers = data?.blockers || [];
      } catch (_e) {
        // Companion may be off — leave the lane empty (honest at N=0).
        this.items.coder = [];
        this.coderReady = false;
      }
    },

    /** Resolve the session-items array from the real (nested) status shape. */
    coderSessionItems(data) {
      const nested = data?.agent?.sessions;
      if (nested && Array.isArray(nested.items)) return nested.items;
      if (Array.isArray(nested)) return nested; // legacy flat array
      if (Array.isArray(data?.sessions)) return data.sessions; // legacy top-level
      // Single-session fallback: the hub also exposes agent.session directly.
      const single = data?.agent?.session;
      if (single) {
        return [
          {
            session: single,
            identity: data?.agent?.identity || {},
            selected: true,
            pinned: Boolean(single.pinned),
            stale: false,
          },
        ];
      }
      return [];
    },

    async answerCoder(coder) {
      // Select this coder as the reply target on the hub (read→write parity
      // with the Companion surface). Voice capture happens on the device.
      try {
        await this.fetchJson("/api/companion/select", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ agent: coder.agent, session_id: coder.sessionId }),
        });
        await this.refreshCoders();
      } catch (e) {
        this.error = `Answer: ${e.message}`;
      }
    },

    // ── authoring: open / close ──
    openCreate(kind) {
      this.creating = kind;
      this.error = "";
    },
    closeCreate() {
      this.creating = null;
      this.busy = false;
    },

    // ── authoring: Note (LIVE POST /api/notes) ──
    async submitNote() {
      const f = this.noteForm;
      if (!f.title.trim() && !f.body.trim()) {
        this.error = "A note needs a title or a body.";
        return;
      }
      const payload = {
        title: f.title.trim() || "Untitled note",
        body_markdown: f.body,
        tags: f.tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      };
      this.busy = true;
      try {
        const data = await this.fetchJson("/api/notes", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
        });
        this.items.note.unshift(this.fromWireNote(data.note || data));
        this.status.note = "live";
        this.noteForm = { title: "", body: "", tags: "" };
        this.closeCreate();
      } catch (e) {
        // Live route failed — keep the form open and surface the error honestly.
        this.error = `Save note: ${e.message}`;
      } finally {
        this.busy = false;
      }
    },

    // ── authoring: Agent (LIVE POST /api/agents) ──
    async submitAgent() {
      const f = this.agentForm;
      if (!f.name.trim()) {
        this.error = "An agent needs a name.";
        return;
      }
      const payload = {
        name: f.name.trim(),
        avatar: f.avatar.trim() || "🤖",
        role: f.role.trim(),
        system_prompt: f.systemPrompt,
        user_template: f.userTemplate,
        tools: f.tools
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        kb_id: f.kbId.trim() || null,
      };
      this.busy = true;
      try {
        const data = await this.fetchJson("/api/agents", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
        });
        this.items.agent.unshift(this.fromWireAgent(data.agent || data));
        this.status.agent = "live";
        this.agentForm = {
          name: "",
          avatar: "🤖",
          role: "",
          systemPrompt: "",
          userTemplate: "",
          tools: "",
          kbId: "",
        };
        this.closeCreate();
      } catch (e) {
        this.error = `Save agent: ${e.message}`;
      } finally {
        this.busy = false;
      }
    },

    // ── small view helpers ──
    relTime(iso) {
      if (!iso) return "";
      const d = new Date(iso);
      if (isNaN(d)) return "";
      const secs = Math.round((Date.now() - d.getTime()) / 1000);
      if (secs < 60) return "just now";
      if (secs < 3600) return `${Math.round(secs / 60)}m ago`;
      if (secs < 86400) return `${Math.round(secs / 3600)}h ago`;
      return `${Math.round(secs / 86400)}d ago`;
    },
    coderTone(c) {
      if (c.selected) return "ready";
      if (c.stale) return "warn";
      if (c.question) return "warn";
      return "neutral";
    },
  };
}
