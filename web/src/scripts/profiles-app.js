// HSM-24-05: the web Runtime Profiles surface.
//
// A "runtime profile" is a named place intelligence runs — either on a device
// (a downloaded GGUF) or an OpenAI-compatible endpoint (OpenRouter / Claude /
// a local server). The web is a first-class AUTHORING port: it manages the
// profile SHAPE (name / kind / endpoint / model / context window) over the
// hub's REST routes, exactly like the desk authors its primitives.
//
// The one hard rule (Phase 24 canon): the API KEY NEVER touches the browser.
// The shape carries only `requires_key` (a boolean); the secret lives in the
// hub's environment as HOLDSPEAK_PROFILE_<id>_KEY and is joined at run time.
// So a cloud profile here states "key set on the hub" — there is no key field.
//
// Honest n/a: an on-device (GGUF) profile cannot run in a browser, so its card
// reads "On device" and is marked unavailable-here rather than pretending.
//
// Cards + the editor are rendered at runtime, so their CSS lives in a
// `<style is:global>` block (Astro scoped styles don't reach JS-injected DOM).

function ProfilesApp() {
  const blankForm = () => ({
    id: "",
    name: "",
    kind: "openAICompatible",
    model_file: "",
    base_url: "",
    model: "",
    node: "",
    context_limit: 16384,
    requires_key: true,
  });

  return {
    profiles: [],
    meshLiveness: {},
    loading: true,
    status: "", // "live" | "unreachable"
    error: "",

    editing: null, // the form object when the editor is open, else null
    isNew: false,
    busy: false,
    confirmingId: "", // a profile pending delete confirmation

    async init() {
      await this.loadProfiles();
      this.loading = false;
    },

    async fetchJson(url, opts) {
      const res = await fetch(url, opts);
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.error || body.detail || `HTTP ${res.status}`);
      return body;
    },

    async loadProfiles() {
      try {
        const data = await this.fetchJson("/api/profiles");
        this.profiles = (data.profiles || []).filter((p) => !p.deleted);
        this.meshLiveness = data.mesh_liveness || {};
        this.status = "live";
      } catch (e) {
        this.status = "unreachable";
        this.profiles = [];
        this.error = `Profiles: ${e.message}`;
      }
    },

    // ── editor ──
    openCreate() {
      this.editing = blankForm();
      this.isNew = true;
      this.error = "";
    },
    openEdit(p) {
      this.editing = {
        id: p.id,
        name: p.name || "",
        kind: p.kind || "openAICompatible",
        model_file: p.model_file || "",
        base_url: p.base_url || "",
        model: p.model || "",
        node: p.node || "",
        context_limit: p.context_limit || 16384,
        requires_key: !!p.requires_key,
      };
      this.isNew = false;
      this.error = "";
    },
    close() {
      this.editing = null;
      this.busy = false;
    },

    async save() {
      const f = this.editing;
      if (!f.name.trim()) {
        this.error = "A profile needs a name.";
        return;
      }
      if (f.kind === "meshNode" && !String(f.node || "").trim()) {
        this.error = "A mesh profile needs its node's name.";
        return;
      }
      const payload = {
        name: f.name.trim(),
        kind: f.kind,
        model_file: f.kind === "onDevice" ? f.model_file.trim() : "",
        base_url: f.kind === "openAICompatible" ? f.base_url.trim() : "",
        model: f.model.trim(),
        node: f.kind === "meshNode" ? String(f.node || "").trim() : "",
        context_limit: Number(f.context_limit) || 16384,
        requires_key: f.kind === "openAICompatible" ? !!f.requires_key : false,
      };
      this.busy = true;
      this.error = "";
      try {
        const url = this.isNew ? "/api/profiles" : `/api/profiles/${f.id}`;
        const data = await this.fetchJson(url, {
          method: this.isNew ? "POST" : "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
        });
        const saved = data.profile || data;
        if (this.isNew) {
          this.profiles.unshift(saved);
        } else {
          const i = this.profiles.findIndex((p) => p.id === saved.id);
          if (i >= 0) this.profiles[i] = saved;
        }
        // a new mesh profile's liveness lives in the list envelope — re-pull
        // so the card states the node's real state, not "never served"
        await this.loadProfiles();
        this.status = "live";
        this.close();
      } catch (e) {
        this.error = `Save profile: ${e.message}`;
      } finally {
        this.busy = false;
      }
    },

    askDelete(p) {
      this.confirmingId = p.id;
    },
    cancelDelete() {
      this.confirmingId = "";
    },
    async confirmDelete(p) {
      this.busy = true;
      try {
        await this.fetchJson(`/api/profiles/${p.id}`, { method: "DELETE" });
        this.profiles = this.profiles.filter((x) => x.id !== p.id);
        this.confirmingId = "";
      } catch (e) {
        this.error = `Delete profile: ${e.message}`;
      } finally {
        this.busy = false;
      }
    },

    // ── presentation ──
    isLocal(p) {
      return (p.kind || "onDevice") === "onDevice";
    },
    hostOf(url) {
      try {
        return new URL(url).host;
      } catch (_e) {
        return (url || "").replace(/^https?:\/\//, "").split("/")[0] || "endpoint";
      }
    },
    // The canonical egress badge `{scope, text, title}` keyed by the shared
    // `.egress-badge.is-*` CSS (the one structured chip, never prose).
    egress(p) {
      if (this.isLocal(p)) {
        return { scope: "local", text: "⌂ On device", title: "Runs on a device. Unavailable here on the web." };
      }
      if ((p.kind || "") === "meshNode") {
        return { scope: "mesh", text: `⇄ mesh · ${p.node || "?"}`, title: `Relays through the hub to ${p.node}.` };
      }
      const host = this.hostOf(p.base_url);
      return { scope: "cloud", text: `☁ ${host}`, title: `Calls ${host} from the hub.` };
    },
    kindLabel(p) {
      if ((p.kind || "") === "meshNode") return "Mesh node";
      return this.isLocal(p) ? "On-device" : "Endpoint";
    },
    // HS-85-04: liveness rides the list envelope; existence is not availability
    meshState(p) {
      const l = this.meshLiveness[p.node || ""];
      if (!l) return "offline — never served";
      if (l.live) return `live (${l.last_seen_seconds}s ago)`;
      return `offline (${l.last_seen_seconds}s ago)`;
    },
    meshIsLive(p) {
      return !!(this.meshLiveness[p.node || ""] || {}).live;
    },
    count() {
      return this.profiles.length;
    },
  };
}
