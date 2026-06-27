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
    workflowForm: { name: "", prompt: "" },

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
        graphJson: graph,
      };
    },

    // ── resolve an agent name from an id (for chain step legibility) ──
    agentName(id) {
      const a = (this.items.agent || []).find((x) => x.id === id);
      return a ? a.name : id;
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

    // ── authoring: Workflow (LIVE POST /api/workflows) ──
    async submitWorkflow() {
      const f = this.workflowForm;
      if (!f.name.trim()) {
        this.error = "A workflow needs a name.";
        return;
      }
      const payload = {
        name: f.name.trim(),
        prompt: f.prompt,
        // graph authoring lives in the Workbench; the web form ships a prompt.
        graph_json: {},
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
        this.workflowForm = { name: "", prompt: "" };
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
    //   workflow → POST /api/workflows/{id}/run   → { workflow_id, output, provider }
    openRun(target, kind = "agent") {
      this.running = target;
      this.runningKind = kind;
      this.runInput = "";
      this.runError = "";
      this.runResult = null;
      this.chainSteps = null;
      this.runBusy = false;
    },
    closeRun() {
      this.running = null;
      this.runningKind = null;
      this.runBusy = false;
      this.chainSteps = null;
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
        }));
        this.runResult = {
          output: data.output || "",
          provider: data.provider || "",
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
      try {
        const data = await this.fetchJson(`/api/workflows/${this.running.id}/run`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ input }),
        });
        this.runResult = {
          output: data.output || "",
          provider: data.provider || "",
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
