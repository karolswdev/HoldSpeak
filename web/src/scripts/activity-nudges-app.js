// Phase 18-05 (web): the /activity pre-briefing nudge board.
//
// A small Alpine island that renders source-cited, dismissible nudge cards
// from GET /api/activity/nudges. Each card carries its citation chips (the
// records the nudge was computed from — verifiable right here on /activity)
// and a "Dictate with this" action that POSTs
// /api/activity/nudges/select to park the originating ActivityRecord id so
// the next dictation grounds its rewrite in that record.
//
// Honesty: nudges are a PURE reader over the local activity ledger — recency
// + entity-type + project-match heuristics, never an LLM. So every card's
// egress is the canonical structured {scope: "local"} badge (POSITIONING
// canon: ONE badge, never a privacy sentence). The badge text + class come
// straight from the shared egress-badge helpers concatenated ahead of this
// factory (egressBadgeText / EGRESS_SCOPES).
//
// Null-read guard: server payloads are defended with optional chaining and
// fallbacks throughout (a nudge may have zero citations; a citation may have
// null entity/title/last_seen_at). No x-text/x-show reads obj.prop where obj
// can be null without a `?.`.

export function HoldSpeakActivityNudges() {
  return {
    nudges: [],
    loading: true,
    error: "",
    activityEnabled: false,
    // The record id currently parked for the next dictation (HS-53-07).
    selectedRecordId: null,
    // Per-key transient busy flag so a card's buttons disable mid-request.
    busyKey: "",
    // The canonical egress for a nudge: everything stays on the machine.
    egressBadge: { scope: "local", label: "Local only" },

    async init() {
      await this.load();
    },

    async load() {
      this.loading = true;
      this.error = "";
      try {
        const res = await fetch("/api/activity/nudges?limit=3");
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error((data && data.error) || `HTTP ${res.status}`);
        }
        // Defensive: the engine returns `{ nudges: [], activity_enabled }`.
        this.nudges = Array.isArray(data?.nudges) ? data.nudges : [];
        this.activityEnabled = Boolean(data?.activity_enabled);
      } catch (e) {
        this.error = (e && e.message) || "Failed to load nudges";
        this.nudges = [];
      } finally {
        this.loading = false;
      }
    },

    // The display text for the egress chip — `glyph word`, from the shared
    // helper concatenated ahead of this factory.
    egressText() {
      return typeof egressBadgeText === "function"
        ? egressBadgeText(this.egressBadge)
        : "";
    },

    // The record id a "Dictate with this" / citation refers to. A "record"
    // nudge's primary record is its first citation; a "window" nudge has
    // none to park, so the action hides.
    primaryRecordId(nudge) {
      const cites = nudge?.citations;
      if (!Array.isArray(cites) || cites.length === 0) return null;
      const id = cites[0]?.record_id;
      return Number.isInteger(id) ? id : null;
    },

    canDictateWith(nudge) {
      return this.primaryRecordId(nudge) !== null;
    },

    // Human label for a citation chip: entity (e.g. github_issue owner/repo#1)
    // falls back to title, then domain, then the record id.
    citationLabel(cite) {
      if (!cite) return "record";
      if (cite.entity_type && cite.entity_id) {
        return `${cite.entity_type} ${cite.entity_id}`;
      }
      if (cite.title) return cite.title;
      if (cite.domain) return cite.domain;
      return `record #${cite.record_id ?? "?"}`;
    },

    // Secondary meta line for a citation chip (source + recency), all
    // null-guarded.
    citationMeta(cite) {
      const parts = [];
      const src = cite?.source_browser;
      if (src) {
        parts.push(
          cite?.source_profile ? `${src} · ${cite.source_profile}` : src
        );
      }
      if (cite?.domain && cite?.title) parts.push(cite.domain);
      const seen = cite?.last_seen_at;
      if (seen) parts.push(this.relTime(seen));
      const visits = cite?.visit_count;
      if (Number.isInteger(visits) && visits > 1) {
        parts.push(`${visits} visits`);
      }
      return parts.join(" · ");
    },

    relTime(iso) {
      if (!iso) return "";
      const then = Date.parse(iso);
      if (Number.isNaN(then)) return iso;
      const secs = Math.max(0, Math.round((Date.now() - then) / 1000));
      if (secs < 60) return "just now";
      const mins = Math.round(secs / 60);
      if (mins < 60) return `${mins}m ago`;
      const hrs = Math.round(mins / 60);
      if (hrs < 24) return `${hrs}h ago`;
      const days = Math.round(hrs / 24);
      return `${days}d ago`;
    },

    isSelected(nudge) {
      const id = this.primaryRecordId(nudge);
      return id !== null && id === this.selectedRecordId;
    },

    async dictateWith(nudge) {
      const recordId = this.primaryRecordId(nudge);
      if (recordId === null) return;
      this.busyKey = nudge?.key || "";
      this.error = "";
      try {
        const res = await fetch("/api/activity/nudges/select", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ record_id: recordId }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error((data && data.error) || `HTTP ${res.status}`);
        }
        // Server echoes `{ selected: <id> }`.
        const sel = data?.selected;
        this.selectedRecordId = Number.isInteger(sel) ? sel : recordId;
      } catch (e) {
        this.error = (e && e.message) || "Could not select this record";
      } finally {
        this.busyKey = "";
      }
    },

    async clearSelection() {
      this.busyKey = "__clear__";
      this.error = "";
      try {
        const res = await fetch("/api/activity/nudges/select/clear", {
          method: "POST",
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error((data && data.error) || `HTTP ${res.status}`);
        }
        this.selectedRecordId = null;
      } catch (e) {
        this.error = (e && e.message) || "Could not clear selection";
      } finally {
        this.busyKey = "";
      }
    },

    async dismiss(nudge) {
      const key = nudge?.key;
      if (!key) return;
      this.busyKey = key;
      this.error = "";
      try {
        const res = await fetch(
          `/api/activity/nudges/${encodeURIComponent(key)}/dismiss`,
          { method: "POST" }
        );
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error((data && data.error) || `HTTP ${res.status}`);
        }
        // Persisted server-side: drop it from the board so it does not
        // reappear on this view.
        this.nudges = this.nudges.filter((n) => n?.key !== key);
      } catch (e) {
        this.error = (e && e.message) || "Could not dismiss this nudge";
      } finally {
        this.busyKey = "";
      }
    },
  };
}
