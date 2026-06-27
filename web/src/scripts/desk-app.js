/*
 * DeskApp — the web Desk's Alpine controller for the Primitive Framework.
 *
 * LIVE against the desktop hub. Every lane reads real primitives from the hub
 * and authors back to it through the canonical REST routes:
 *
 *   Notes    — GET/POST /api/notes               (LIVE read + author)
 *   Agents   — GET/POST /api/agents              (LIVE read + author)
 *   Agent run— POST /api/agents/{id}/run         (LIVE — runs the persona)
 *   KBs      — GET/POST /api/kbs                 (LIVE read + author)
 *   Dirs     — GET/POST /api/directories         (LIVE read + author)
 *   Filing   — PUT/DELETE /api/directories/{id}/members/{primitive_id}
 *   Chains   — GET/POST /api/chains              (LIVE read + author)
 *   Workflows— GET/POST /api/workflows           (LIVE read + author)
 *   Meetings — GET /api/meetings                 (LIVE read)
 *   Artifacts— GET /api/sync/pull                (LIVE read — synthesized)
 *   Coder    — GET /api/companion/status         (LIVE presence, 4s poll)
 *
 * Honesty model (no fake data):
 *   - reachable + has route → live cards (no badge).
 *   - reachable, content-derived only (artifact/meeting) → no author button.
 *   - hub unreachable for a lane → "hub unreachable" badge + empty lane.
 *
 * Hub connection: each lane reports its own reachability; the header rolls
 * those up into one connected / partial / unreachable indicator plus a
 * last-synced stamp, so the surface is honest about whether the hub answered.
 *
 * Wire is snake_case; mapped to camelCase (lib/primitives.ts) at the boundary
 * (fromWire*). `graph_json` is a JSON OBJECT on the wire (not a string).
 */
function DeskApp() {
  return {
    loading: true,
    error: "",
    updatedAt: null,
    coderTimer: null,
    coderReady: false,
    coderBlockers: [],

    // ── ambient trust (HS-21-04) — the canonical egress posture + readiness,
    // both sourced from GET /api/setup/status. `setup` is the raw status block
    // (or null when the adapter is unreachable — the chips simply hide).
    setup: null,
    setupLoaded: false,

    // ── the store, by kind ──
    items: {
      meeting: [],
      artifact: [],
      note: [],
      directory: [],
      kb: [],
      agent: [],
      chain: [],
      workflow: [],
      coder: [],
    },
    // Per-kind reachability: "live" | "unreachable" (undefined until loaded).
    status: {},

    // ── authoring ──
    creating: null, // "note" | "agent" | "kb" | "chain" | "workflow" | null
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
    kbForm: { name: "", memberIds: "" },
    directoryForm: { name: "", parentId: "" },
    chainForm: { name: "", steps: "" },
    // A workflow is authored either as a saved prompt OR as a minimal LINEAR
    // chain of steps (entry → … → output). `nodes` holds the ordered model-op
    // steps the chain builder emits; `mode` toggles which the form ships.
    workflowForm: { name: "", prompt: "", mode: "prompt", nodes: [] },

    // ── filing (membership picker) ──
    filing: null, // the primitive being filed: { kind, id, title } | null
    filingBusy: "", // directory id currently mutating membership | ""
    filingError: "",

    // ── agent run ──
    running: null, // the agent currently being run (drawer target) | null
    runInput: "",
    runBusy: false,
    runError: "",
    runResult: null, // { output, provider } | null

    // ── chain / workflow run (capability execution, mirrors the agent run) ──
    runningKind: null, // "agent" | "chain" | "workflow" | null — which drawer
    chainSteps: null, // [{ agentId, agentName, output }] | null (crew result)
    // Honest signals the hub lands on a workflow run:
    //   `warning` (a graph it refused to guess an order for) and `steps`
    //   (the per-node execution trail of a linearized graph). Both surfaced.
    runWarning: "", // hub `data.warning` for the active run, or ""
    workflowSteps: null, // [{ nodeId, kind, output, provider }] | null (graph trail)

    async init() {
      await this.loadAll();
      this.loading = false;
      this.loadSetup();
      this.refreshCoders();
      this.coderTimer = setInterval(() => this.refreshCoders(), 4000);
    },

    // ── ambient trust + readiness (HS-21-04) ─────────────────────────────────
    // Read the live posture from the same adapter the /setup surface uses
    // (GET /api/setup/status). Failures are silent: the chips stay hidden so we
    // never assert a posture we couldn't confirm.
    async loadSetup() {
      try {
        const res = await fetch("/api/setup/status");
        if (!res.ok) return;
        this.setup = await res.json();
        this.setupLoaded = true;
      } catch (_e) {
        /* adapter unreachable — leave the ambient chips hidden (honest). */
      }
    },

    /**
     * The canonical egress badge for the live posture: `{scope, text, title}`.
     * `scope` is the structured value the shared `.egress-badge` CSS keys on
     * (local | mixed | cloud) — the ONE structured badge that replaces privacy
     * prose (POSITIONING canon). The glyph + fallback word mirror the shared
     * `EGRESS_SCOPES` map in egress-badge.js; this is a placement port, not a
     * new visual language (desk-app.js is eval'd via ?raw, so no ES import).
     */
    egressBadge() {
      const t = (this.setup && this.setup.trust) || {};
      // Off-loopback bind with no auth token, or actuators on → external writes
      // are possible: local + cloud.
      const bind = t.web_bind;
      const offLoopback = bind && bind !== "127.0.0.1" && bind !== "localhost" && bind !== "::1";
      if (t.actuators_enabled || (offLoopback && !t.auth_token_set)) {
        return { scope: "mixed", text: "⌂+☁ Local + cloud", title: "Local plus a configured cloud reach. Writes still need your approval." };
      }
      // A transcript can be sent to a configured endpoint → cloud.
      if (t.transcript_egress && t.transcript_egress !== "none") {
        const ep = (t.configured_endpoints && t.configured_endpoints[0]) || "";
        const label = ep ? `Cloud · ${ep}` : "Configured endpoint";
        return { scope: "cloud", text: `☁ ${label}`, title: "A transcript can be sent to a configured endpoint." };
      }
      // Nothing leaves the machine → local.
      return { scope: "local", text: "⌂ Local only", title: "Everything stays on this machine." };
    },

    /** The /api/setup/status overall verdict: "ready" | "blocked" | other. */
    setupOverall() {
      return (this.setup && this.setup.overall) || "unknown";
    },

    /** The readiness chip tone class. */
    readyTone() {
      const o = this.setupOverall();
      if (o === "ready") return "ready";
      if (o === "blocked") return "blocked";
      return "warn";
    },

    /** A one-line readiness indicator, e.g. "Ready · 6/6 checks". */
    readyLine() {
      const s = this.setup;
      if (!s) return "";
      const sections = s.sections || [];
      const pass = sections.filter((x) => x.status === "pass").length;
      const total = sections.length;
      const counts = total ? ` · ${pass}/${total} checks` : "";
      const o = this.setupOverall();
      if (o === "ready") return `Ready${counts}`;
      if (o === "blocked") {
        const fails = sections.filter((x) => x.status === "fail").length;
        return `${fails || 1} blocking${counts}`;
      }
      const advisory = sections.filter((x) => x.status === "warn").length;
      return advisory ? `${advisory} to review${counts}` : `Almost ready${counts}`;
    },

    /** Hover title for the readiness chip — points at /setup for the detail. */
    readyTitle() {
      return `${this.readyLine()}. Open Setup for the full checklist.`;
    },

    // ── totals + grouping helpers (data-driven by the page descriptor) ──
    count(kind) {
      return (this.items[kind] || []).length;
    },
    total() {
      return Object.values(this.items).reduce((n, l) => n + l.length, 0);
    },
    /** The hub could not be reached for this kind. */
    isUnreachable(kind) {
      return this.status[kind] === "unreachable";
    },
    /** This kind reads live but the web cannot author it (content-derived). */
    isReadonly(kind) {
      return kind === "meeting" || kind === "artifact";
    },
    /** Any primitive kind (not a directory itself) can be filed into a directory. */
    isFilable(kind) {
      return kind !== "directory";
    },

    // ── hub connection rollup (header indicator) ───────────────────────────
    /** "connected" (all answered) | "partial" (some down) | "unreachable". */
    hubState() {
      const vals = Object.values(this.status);
      if (vals.length === 0) return "connecting";
      const down = vals.filter((v) => v === "unreachable").length;
      if (down === 0) return "connected";
      if (down >= vals.length) return "unreachable";
      return "partial";
    },
    hubLabel() {
      switch (this.hubState()) {
        case "connected": return "Hub connected";
        case "partial": return "Hub partially reachable";
        case "unreachable": return "Hub unreachable";
        default: return "Connecting…";
      }
    },

    updatedLabel() {
      if (!this.updatedAt) return "not synced";
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
        this.loadArtifacts(), // artifacts via sync pull
        this.loadNotes(),
        this.loadAgents(),
        this.loadKbs(),
        this.loadDirectories(),
        this.loadChains(),
        this.loadWorkflows(),
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

    // ── content: artifacts (live, synthesized — via the sync channel) ──
    async loadArtifacts() {
      try {
        const data = await this.fetchJson("/api/sync/pull?limit=50");
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
      } catch (e) {
        this.status.artifact = "unreachable";
        if (!this.error) this.error = `Artifacts: ${e.message}`;
      }
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

    // ── organization: KBs (LIVE — GET/POST /api/kbs) ──
    async loadKbs() {
      try {
        const data = await this.fetchJson("/api/kbs");
        this.items.kb = (data.kbs || [])
          .filter((k) => !k.deleted)
          .map(this.fromWireKb);
        this.status.kb = "live";
      } catch (e) {
        this.status.kb = "unreachable";
        this.items.kb = [];
        if (!this.error) this.error = `KBs: ${e.message}`;
      }
    },

    fromWireKb(k) {
      return {
        kind: "kb",
        id: k.id,
        name: k.name,
        memberIds: k.member_ids || [],
        createdAt: k.created_at,
      };
    },

    // ── organization: Directories (LIVE — GET/POST /api/directories) ──
    // Identity + membership sync; geometry/paint is per-device, never canonical.
    async loadDirectories() {
      try {
        const data = await this.fetchJson("/api/directories");
        // Tolerate either {directories:[…]} or a bare change-set list.
        const raw = data.directories || this.liveValues(data);
        this.items.directory = (raw || [])
          .filter((d) => !d.deleted)
          .map(this.fromWireDirectory);
        this.status.directory = "live";
      } catch (e) {
        this.status.directory = "unreachable";
        this.items.directory = [];
        if (!this.error) this.error = `Directories: ${e.message}`;
      }
    },

    fromWireDirectory(d) {
      return {
        kind: "directory",
        id: d.id,
        name: d.name,
        parentId: d.parent_id || null,
        // Membership rides /api/sync/pull + the directory record; accept either
        // an inline member_ids list or a members map keyed by primitive id.
        memberIds: d.member_ids || (d.members ? Object.keys(d.members) : []),
        createdAt: d.created_at,
      };
    },

    // ── filing helpers (membership = which directory a primitive lives in) ──
    /** Directories this primitive id is filed in. */
    directoriesFor(primitiveId) {
      return (this.items.directory || []).filter((d) =>
        (d.memberIds || []).includes(primitiveId),
      );
    },
    /** True when this primitive is filed in the given directory. */
    isFiledIn(primitiveId, dirId) {
      const d = (this.items.directory || []).find((x) => x.id === dirId);
      return Boolean(d && (d.memberIds || []).includes(primitiveId));
    },
    /** A short title for the move-picker header, by primitive identity. */
    primitiveTitle(p) {
      if (!p) return "";
      return p.title || p.name || p.id;
    },

    // ── filing: open / close the "Move to…" picker ──
    openFile(kind, item) {
      this.filing = {
        kind,
        id: item.id,
        title: this.primitiveTitle(item),
      };
      this.filingError = "";
      this.filingBusy = "";
    },
    closeFile() {
      this.filing = null;
      this.filingBusy = "";
      this.filingError = "";
    },

    /** Toggle membership of the filing primitive in a directory. */
    async toggleFile(dir) {
      if (!this.filing) return;
      const pid = this.filing.id;
      const dirId = dir.id;
      const already = this.isFiledIn(pid, dirId);
      this.filingBusy = dirId;
      this.filingError = "";
      const url = `/api/directories/${encodeURIComponent(dirId)}/members/${encodeURIComponent(pid)}`;
      try {
        await this.fetchJson(url, {
          method: already ? "DELETE" : "PUT",
          headers: { "content-type": "application/json" },
        });
        // Optimistic local membership update (the hub is the truth on reload).
        const d = this.items.directory.find((x) => x.id === dirId);
        if (d) {
          d.memberIds = already
            ? d.memberIds.filter((m) => m !== pid)
            : [...d.memberIds, pid];
        }
      } catch (e) {
        this.filingError = `${already ? "Unfile" : "File"}: ${e.message}`;
      } finally {
        this.filingBusy = "";
      }
    },

    /** Resolve a filed primitive (any kind) to a card-legible summary. */
    memberOf(primitiveId) {
      for (const kind of ["meeting", "artifact", "note", "kb", "agent", "chain", "workflow"]) {
        const hit = (this.items[kind] || []).find((x) => x.id === primitiveId);
        if (hit) {
          return {
            kind,
            id: primitiveId,
            label: this.primitiveTitle(hit),
          };
        }
      }
      // Filed but not loaded on this surface (synced elsewhere) — show the id.
      return { kind: "unknown", id: primitiveId, label: primitiveId };
    },

    // ── capability: chains (LIVE — GET/POST /api/chains) ──
    async loadChains() {
      try {
        const data = await this.fetchJson("/api/chains");
        this.items.chain = (data.chains || [])
          .filter((c) => !c.deleted)
          .map(this.fromWireChain);
        this.status.chain = "live";
      } catch (e) {
        this.status.chain = "unreachable";
        this.items.chain = [];
        if (!this.error) this.error = `Chains: ${e.message}`;
      }
    },

    fromWireChain(c) {
      return {
        kind: "chain",
        id: c.id,
        name: c.name,
        steps: c.steps || [],
      };
    },

    // ── capability: workflows (LIVE — GET/POST /api/workflows) ──
    async loadWorkflows() {
      try {
        const data = await this.fetchJson("/api/workflows");
        this.items.workflow = (data.workflows || [])
          .filter((w) => !w.deleted)
          .map(this.fromWireWorkflow);
        this.status.workflow = "live";
      } catch (e) {
        this.status.workflow = "unreachable";
        this.items.workflow = [];
        if (!this.error) this.error = `Workflows: ${e.message}`;
      }
    },

    fromWireWorkflow(w) {
      const graph = w.graph_json;
      const hasGraph = graph && typeof graph === "object" && Object.keys(graph).length > 0;
      return {
        kind: "workflow",
        id: w.id,
        name: w.name,
        prompt: w.prompt || "",
        hasGraph: Boolean(hasGraph),
        // `graph_json` is a JSON OBJECT on the wire (Record<string, unknown> or
        // null), never a string; kept as the object the graph editor reads.
        graphJson: graph,
      };
    },

    // ── resolve an agent name from an id (for chain step legibility) ──
    agentName(id) {
      const a = (this.items.agent || []).find((x) => x.id === id);
      return a ? a.name : id;
    },

    // ── provenance / lineage ────────────────────────────────────────────────
    // Artifacts (and run results) carry `sources: [{source_type, source_ref}]`.
    // We resolve a source_ref to a loaded primitive's title when we have it,
    // and fall back to the raw id. The hub lands `sources` in parallel this
    // wave, so everything here degrades gracefully when it's absent.

    /** Resolve any primitive id (any kind, incl. directories) to a label. */
    resolveRef(ref) {
      if (!ref) return "";
      for (const kind of [
        "meeting", "artifact", "note", "directory", "kb",
        "agent", "chain", "workflow",
      ]) {
        const hit = (this.items[kind] || []).find((x) => x.id === ref);
        if (hit) return { kind, label: this.primitiveTitle(hit), resolved: true };
      }
      // Not loaded on this surface (synced elsewhere) — show the id honestly.
      return { kind: "", label: ref, resolved: false };
    },

    /**
     * Normalize a raw `sources` array into render-ready lineage entries.
     * Tolerates `{source_type, source_ref}` (canonical), bare strings, and
     * `{type, ref}` / `{source}` drift. Splits into the body sources (where it
     * came FROM) and the via-capability (the agent/chain/workflow that ran it).
     */
    lineage(sources) {
      const list = Array.isArray(sources) ? sources : [];
      const from = [];
      let via = null;
      for (const s of list) {
        if (!s) continue;
        const type = (typeof s === "string"
          ? "" : (s.source_type || s.type || "")).toLowerCase();
        const ref = typeof s === "string"
          ? s
          : (s.source_ref || s.ref || s.source || s.id || "");
        if (!ref) continue;
        const r = this.resolveRef(ref);
        const entry = { type, ref, kind: r.kind, label: r.label, resolved: r.resolved };
        // a capability that produced this is the "via"; everything else is "from"
        if (["agent", "chain", "workflow"].includes(type) ||
            ["agent", "chain", "workflow"].includes(r.kind)) {
          if (!via) via = entry;
          else from.push(entry);
        } else {
          from.push(entry);
        }
      }
      return { from, via, any: from.length > 0 || via != null };
    },

    /** True when a primitive (or result) has any usable lineage. */
    hasLineage(sources) {
      return this.lineage(sources).any;
    },

    // ── coder lane (live presence stream) ──
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
            tokensUsed: s.tokens_used ?? s.tokens ?? null,
            events: s.events || [],
          };
        });
        this.coderReady = Boolean(data?.ready_for_agent_reply);
        this.coderBlockers = data?.blockers || [];
        this.status.coder = "live";
      } catch (_e) {
        // Companion may be off — leave the lane empty (honest at N=0).
        this.items.coder = [];
        this.coderReady = false;
        // Don't mark the whole hub unreachable for a missing companion.
      }
    },

    /** Resolve the session-items array from the real (nested) status shape. */
    coderSessionItems(data) {
      const nested = data?.agent?.sessions;
      if (nested && Array.isArray(nested.items)) return nested.items;
      if (Array.isArray(nested)) return nested; // legacy flat array
      if (Array.isArray(data?.sessions)) return data.sessions; // legacy top-level
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
        tags: this.splitList(f.tags),
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
        tools: this.splitList(f.tools),
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
          name: "", avatar: "🤖", role: "", systemPrompt: "",
          userTemplate: "", tools: "", kbId: "",
        };
        this.closeCreate();
      } catch (e) {
        this.error = `Save agent: ${e.message}`;
      } finally {
        this.busy = false;
      }
    },

    // ── authoring: KB (LIVE POST /api/kbs) ──
    async submitKb() {
      const f = this.kbForm;
      if (!f.name.trim()) {
        this.error = "A knowledge base needs a name.";
        return;
      }
      const payload = {
        name: f.name.trim(),
        member_ids: this.splitList(f.memberIds),
      };
      this.busy = true;
      try {
        const data = await this.fetchJson("/api/kbs", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
        });
        this.items.kb.unshift(this.fromWireKb(data.kb || data));
        this.status.kb = "live";
        this.kbForm = { name: "", memberIds: "" };
        this.closeCreate();
      } catch (e) {
        this.error = `Save KB: ${e.message}`;
      } finally {
        this.busy = false;
      }
    },

    // ── authoring: Directory (LIVE POST /api/directories) ──
    async submitDirectory() {
      const f = this.directoryForm;
      if (!f.name.trim()) {
        this.error = "A directory needs a name.";
        return;
      }
      const payload = {
        name: f.name.trim(),
        parent_id: f.parentId.trim() || null,
      };
      this.busy = true;
      try {
        const data = await this.fetchJson("/api/directories", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
        });
        this.items.directory.unshift(
          this.fromWireDirectory(data.directory || data),
        );
        this.status.directory = "live";
        this.directoryForm = { name: "", parentId: "" };
        this.closeCreate();
      } catch (e) {
        this.error = `Save directory: ${e.message}`;
      } finally {
        this.busy = false;
      }
    },

    // ── authoring: Chain (LIVE POST /api/chains) ──
    async submitChain() {
      const f = this.chainForm;
      if (!f.name.trim()) {
        this.error = "A chain needs a name.";
        return;
      }
      const payload = {
        name: f.name.trim(),
        steps: this.splitList(f.steps),
      };
      this.busy = true;
      try {
        const data = await this.fetchJson("/api/chains", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
        });
        this.items.chain.unshift(this.fromWireChain(data.chain || data));
        this.status.chain = "live";
        this.chainForm = { name: "", steps: "" };
        this.closeCreate();
      } catch (e) {
        this.error = `Save chain: ${e.message}`;
      } finally {
        this.busy = false;
      }
    },

    // ── authoring: the linear chain builder ──
    //
    // The web Desk authors a MINIMAL LINEAR workflow: entry → step → … → output.
    // The kinds offered are the chain-safe ones the hub's `workflow_graph.linearize`
    // accepts and the iPad Blueprint produces (no branch/loop/fan-out). Each step
    // is one model op; `buildGraphJson` lowers them to the canonical snake_case
    // `graph_json` wire (nodes with id + a single-key `kind` tag, ordered `exec_edges`
    // on the "then" exec-out, and the `entry` id) — byte-shaped like the iPad's and
    // accepted as-is by the hub linearizer.

    /** The step kinds the linear builder offers (chain-safe model ops). */
    workflowStepKinds: [
      { kind: "llm", label: "Prompt", hint: "Your own instruction; {input} is the prior step's text." },
      { kind: "summarize", label: "Summarize", hint: "Tighten the input into a faithful summary." },
      { kind: "rewrite", label: "Rewrite", hint: "Restate the input in a tone you set." },
      { kind: "extract", label: "Extract", hint: "Pull one artifact (decisions, actions…) out of the input." },
    ],

    /** Append a fresh step to the linear chain. */
    addWorkflowStep(kind = "llm") {
      this.workflowForm.nodes.push({
        kind,
        prompt: "",       // llm
        tone: "concise",  // rewrite
        artifactType: "decisions", // extract
      });
    },
    /** Drop the step at `i` from the chain. */
    removeWorkflowStep(i) {
      this.workflowForm.nodes.splice(i, 1);
    },
    /** Move a step one slot toward the start (`dir=-1`) or end (`dir=+1`). */
    moveWorkflowStep(i, dir) {
      const j = i + dir;
      const n = this.workflowForm.nodes;
      if (j < 0 || j >= n.length) return;
      [n[i], n[j]] = [n[j], n[i]];
    },

    /**
     * Lower the ordered builder steps into the canonical snake_case `graph_json`.
     *
     * Shape (matches the iPad Blueprint + the hub `workflow_graph.linearize`):
     *   nodes: [{ id, kind }]   kind is a single-key tag —
     *     entry/summarize/output → {"entry":{}}, {"summarize":{}}, {"output":{}}
     *     llm     → {"llm": {"name": .., "prompt": ..}}
     *     rewrite → {"rewrite": {"tone": ..}}
     *     extract → {"extract": "decisions"}   (bare-string payload)
     *   exec_edges: [{ from: { node, name: "then" }, to }]  in chain order
     *   entry: <entry node id>
     *
     * Web ships LINEAR-only by construction; it labels itself so (no control flow).
     */
    buildGraphJson(steps) {
      const nodes = [{ id: "entry", kind: { entry: {} } }];
      steps.forEach((s, i) => {
        const id = `n${i + 1}`;
        let kind;
        if (s.kind === "llm") {
          kind = { llm: { name: "Prompt", prompt: s.prompt || "" } };
        } else if (s.kind === "rewrite") {
          kind = { rewrite: { tone: s.tone || "concise" } };
        } else if (s.kind === "extract") {
          kind = { extract: s.artifactType || "decisions" };
        } else {
          kind = { summarize: {} };
        }
        nodes.push({ id, kind });
      });
      nodes.push({ id: "output", kind: { output: {} } });

      // Wire one straight chain along the "then" exec-out, in node order.
      const execEdges = [];
      for (let i = 0; i < nodes.length - 1; i++) {
        execEdges.push({
          from: { node: nodes[i].id, name: "then" },
          to: nodes[i + 1].id,
        });
      }
      return { entry: "entry", nodes, exec_edges: execEdges, linear: true };
    },

    // ── authoring: Workflow (LIVE POST /api/workflows) ──
    async submitWorkflow() {
      const f = this.workflowForm;
      if (!f.name.trim()) {
        this.error = "A workflow needs a name.";
        return;
      }
      const graphing = f.mode === "graph";
      if (graphing && !f.nodes.length) {
        this.error = "Add at least one step, or switch to a prompt.";
        return;
      }
      if (!graphing && !f.prompt.trim()) {
        this.error = "A prompt workflow needs a prompt, or switch to a chain.";
        return;
      }
      const payload = {
        name: f.name.trim(),
        // A graph workflow carries an empty prompt; the chain IS the run.
        prompt: graphing ? "" : f.prompt,
        // Prompt workflows ship no graph; chain workflows ship the linear graph_json
        // the hub linearizer + the iPad both speak.
        graph_json: graphing ? this.buildGraphJson(f.nodes) : {},
      };
      this.busy = true;
      try {
        const data = await this.fetchJson("/api/workflows", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
        });
        this.items.workflow.unshift(this.fromWireWorkflow(data.workflow || data));
        this.status.workflow = "live";
        this.workflowForm = { name: "", prompt: "", mode: "prompt", nodes: [] };
        this.closeCreate();
      } catch (e) {
        this.error = `Save workflow: ${e.message}`;
      } finally {
        this.busy = false;
      }
    },

    // ── capability run — one drawer, three kinds ──
    //   agent    → POST /api/agents/{id}/run     → { output, provider }
    //   chain    → POST /api/chains/{id}/run      → { chain_id, steps:[{agent_id, output}], output }
    //   workflow → POST /api/workflows/{id}/run   → { workflow_id, output, provider[, steps][, warning] }
    openRun(target, kind = "agent") {
      this.running = target;
      this.runningKind = kind;
      this.runInput = "";
      this.runError = "";
      this.runResult = null;
      this.chainSteps = null;
      this.workflowSteps = null;
      this.runWarning = "";
      this.runBusy = false;
    },
    closeRun() {
      this.running = null;
      this.runningKind = null;
      this.runBusy = false;
      this.chainSteps = null;
      this.workflowSteps = null;
      this.runWarning = "";
    },
    /** The verb + display name for the active run drawer. */
    runTitle() {
      if (!this.running) return "";
      return this.running.name || "Run";
    },
    async submitRun() {
      if (!this.running) return;
      if (this.runningKind === "chain") return this.submitChainRun();
      if (this.runningKind === "workflow") return this.submitWorkflowRun();
      return this.submitAgentRun();
    },
    async submitAgentRun() {
      const input = this.runInput.trim();
      if (!input && !(this.running.userTemplate || "").trim()) {
        this.runError = "Give the agent something to work on.";
        return;
      }
      this.runBusy = true;
      this.runError = "";
      this.runResult = null;
      try {
        const data = await this.fetchJson(`/api/agents/${this.running.id}/run`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ input }),
        });
        this.runResult = {
          output: data.output || "",
          provider: data.provider || "",
          sources: data.sources || [],
        };
      } catch (e) {
        this.runError = e.message;
      } finally {
        this.runBusy = false;
      }
    },

    // ── chain run (LIVE POST /api/chains/{id}/run) ──
    async submitChainRun() {
      const input = this.runInput.trim();
      if (!input) {
        this.runError = "Give the crew something to work on.";
        return;
      }
      this.runBusy = true;
      this.runError = "";
      this.runResult = null;
      this.chainSteps = null;
      try {
        const data = await this.fetchJson(`/api/chains/${this.running.id}/run`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ input }),
        });
        this.chainSteps = (data.steps || []).map((s) => ({
          agentId: s.agent_id || "",
          agentName: this.agentName(s.agent_id),
          output: s.output || "",
          // a step may carry its own provider (per-step display is kept)
          provider: s.provider || "",
        }));
        this.runResult = {
          output: data.output || "",
          // the hub now lands a TOP-LEVEL provider on the chain response this
          // wave; fall back to the last step's provider if it's not there yet.
          provider:
            data.provider ||
            (this.chainSteps.length
              ? this.chainSteps[this.chainSteps.length - 1].provider
              : "") ||
            "",
          sources: data.sources || [],
        };
      } catch (e) {
        this.runError = e.message;
      } finally {
        this.runBusy = false;
      }
    },

    // ── workflow run (LIVE POST /api/workflows/{id}/run) ──
    async submitWorkflowRun() {
      const input = this.runInput.trim();
      const w = this.running;
      // A graph workflow can run on its own wiring; a prompt-only one needs input.
      if (!input && !w.hasGraph && !(w.prompt || "").trim()) {
        this.runError = "Give the workflow something to work on.";
        return;
      }
      this.runBusy = true;
      this.runError = "";
      this.runResult = null;
      this.workflowSteps = null;
      this.runWarning = "";
      try {
        const data = await this.fetchJson(`/api/workflows/${this.running.id}/run`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ input }),
        });
        // The hub is honest about a graph it would not guess an order for: it
        // runs the prompt fallback and lands a `warning`. Surface it verbatim.
        this.runWarning = data.warning || "";
        // A linearized graph lands its per-node execution trail in `steps`
        // ({node_id, kind, output, provider}); render it under the output.
        this.workflowSteps = (data.steps || []).map((s) => ({
          nodeId: s.node_id || "",
          kind: s.kind || "",
          output: s.output || "",
          provider: s.provider || "",
        }));
        if (!this.workflowSteps.length) this.workflowSteps = null;
        this.runResult = {
          output: data.output || "",
          provider: data.provider || "",
          sources: data.sources || [],
        };
      } catch (e) {
        this.runError = e.message;
      } finally {
        this.runBusy = false;
      }
    },
    async copyRun() {
      if (!this.runResult) return;
      try {
        await navigator.clipboard.writeText(this.runResult.output || "");
        this.runCopied = true;
        setTimeout(() => { this.runCopied = false; }, 1400);
      } catch (_e) {
        /* clipboard blocked — no-op */
      }
    },
    runCopied: false,

    /**
     * "Produced by <name>" for the active run result. Prefers a capability
     * named in the result's own `sources` (hub-supplied, authoritative), and
     * falls back to the primitive we ran (always known on this surface).
     */
    runProducedBy() {
      const lin = this.lineage(this.runResult?.sources);
      if (lin.via && lin.via.label) {
        return { label: lin.via.label, kind: lin.via.kind || this.runningKind || "" };
      }
      if (this.running) {
        return {
          label: this.running.name || this.runTitle(),
          kind: this.runningKind || "",
        };
      }
      return null;
    },

    /** The non-capability lineage of the run result (what it was fed). */
    runFrom() {
      return this.lineage(this.runResult?.sources).from;
    },

    /** Egress scope for an agent run — local provider vs a cloud endpoint. */
    runEgress() {
      const p = (this.runResult?.provider || "").toLowerCase();
      if (!p) return { scope: "unknown", label: "provider unknown" };
      if (p.includes("local") || p.includes("llama") || p.includes("mlx") || p.includes("ondevice") || p.includes("device")) {
        return { scope: "local", label: "ran on-device" };
      }
      if (p.includes("endpoint") || p.includes("openai") || p.includes("http") || p.includes("api")) {
        return { scope: "cloud", label: `via ${this.runResult.provider}` };
      }
      return { scope: "cloud", label: `via ${this.runResult.provider}` };
    },

    // ── small helpers ──
    splitList(s) {
      return String(s || "")
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
    },
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
