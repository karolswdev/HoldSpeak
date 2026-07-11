import { create } from "zustand";
import { api } from "./api.js";

function stepSlotIds(step) {
  return (step.execution_slots || []).map((slot) => slot.id);
}

// Given a sitting + a scenario, return the first step whose explicit execution
// slots are not all answered. An empty slot list fails closed instead of
// silently completing an invalid protocol.
export function currentStep(sitting, scenario) {
  const answered = new Set(
    sitting.verdicts.map((v) => `${v.scenario_id}|${v.step_index}|${v.slot_id}`)
  );
  for (const step of scenario.steps) {
    const slotIds = stepSlotIds(step);
    if (slotIds.length === 0) return step;
    const done = slotIds.every((slotId) => answered.has(`${scenario.id}|${step.index}|${slotId}`));
    if (!done) return step;
  }
  return null;
}

export function stepAnswered(sitting, scenario, step) {
  const answered = new Set(
    sitting.verdicts.map((v) => `${v.scenario_id}|${v.step_index}|${v.slot_id}`)
  );
  const slotIds = stepSlotIds(step);
  return slotIds.length > 0 && slotIds.every((slotId) => answered.has(`${scenario.id}|${step.index}|${slotId}`));
}

export function verdictFor(sitting, scenarioId, stepIndex, slotId) {
  return sitting.verdicts.find(
    (v) => v.scenario_id === scenarioId && v.step_index === stepIndex && v.slot_id === slotId
  );
}

export const useStore = create((set, get) => ({
  view: "home",
  packs: [],
  sittings: [],
  sitting: null,
  staging: null,
  stagedIds: {},
  confirmedIds: {},
  afterRan: {},
  error: null,
  busy: false,

  setView: (view) => set({ view }),
  setError: (error) => set({ error }),

  async loadHome() {
    set({ busy: true, error: null });
    try {
      const [packs, sittings] = await Promise.all([api.packs(), api.listSittings()]);
      set({ packs: packs.packs, sittings: sittings.sittings, view: "home", busy: false });
    } catch (e) {
      set({ error: String(e.message || e), busy: false });
    }
  },

  async start(pack, deck, lan = false) {
    set({ busy: true, error: null, staging: null, stagedIds: {}, afterRan: {} });
    try {
      const sitting = await api.createSitting(pack, deck, lan);
      set({ sitting, view: "sitting", busy: false });
    } catch (e) {
      set({ error: String(e.message || e), busy: false });
    }
  },

  async open(id) {
    set({ busy: true, error: null, staging: null, stagedIds: {}, afterRan: {}, debrief: null, backlog: null });
    try {
      const sitting = await api.getSitting(id);
      set({ sitting, view: "sitting", busy: false });
      // Re-opening a completed (or already-walked) sitting is a REVIEW: load its
      // recorded debrief so the findings are there to look at, not just the score.
      if (sitting.status === "done" || sitting.legacy_invalid || sitting.progress?.complete || sitting.verdicts?.length) {
        try {
          const packet = await api.readDebrief(id); // GET returns the packet directly
          set({ debrief: packet });
        } catch (_) {}
      }
    } catch (e) {
      set({ error: String(e.message || e), busy: false });
    }
  },

  async refresh() {
    const s = get().sitting;
    if (!s) return;
    const sitting = await api.getSitting(s.id);
    set({ sitting });
  },

  async ensureStaged(scenarioId) {
    if (get().stagedIds[scenarioId]) return get().staging;
    set({ busy: true, error: null });
    try {
      const staging = await api.stage(get().sitting.id, scenarioId);
      set((st) => ({
        staging,
        busy: false,
        stagedIds: staging.ok ? { ...st.stagedIds, [scenarioId]: true } : st.stagedIds,
      }));
      return staging;
    } catch (e) {
      set({ error: String(e.message || e), busy: false, staging: { ok: false, error: String(e.message || e) } });
      return get().staging;
    }
  },

  async confirmStaged(scenarioId) {
    try {
      const sitting = await api.confirmManual(get().sitting.id, scenarioId);
      set((state) => ({
        sitting,
        confirmedIds: { ...state.confirmedIds, [scenarioId]: true },
      }));
    } catch (e) {
      set({ error: String(e.message || e) });
    }
  },

  retryStage(scenarioId) {
    set((st) => ({ stagedIds: { ...st.stagedIds, [scenarioId]: false }, staging: null }));
    return get().ensureStaged(scenarioId);
  },

  async cast(body) {
    set({ error: null });
    try {
      const sitting = await api.castVerdict(get().sitting.id, body);
      set({ sitting });
    } catch (e) {
      set({ error: String(e.message || e) });
    }
  },

  async uploadShot(scenarioId, stepIndex, slotId, file) {
    return api.uploadShot(get().sitting.id, scenarioId, stepIndex, slotId, file);
  },

  async registerDeviceSession(body) {
    set({ error: null });
    try {
      const result = await api.createDeviceSession(get().sitting.id, body);
      // The endpoint may return the refreshed sitting directly or a created
      // attestation. A GET keeps the UI correct in both cases.
      if (result?.scenarios && result?.device_sessions) set({ sitting: result });
      else await get().refresh();
      return result;
    } catch (e) {
      set({ error: String(e.message || e) });
      throw e;
    }
  },

  // Speak-to-fill: WAV in, transcribed text out via the run's own transcribe
  // route. Returns { ok, text } | { ok:false, error }.
  async transcribeNote(wavBlob) {
    return api.transcribe(get().sitting.id, wavBlob);
  },

  async runAfter(scenarioId, stepIndex) {
    set({ busy: true, error: null });
    try {
      await api.runAfter(get().sitting.id, scenarioId, stepIndex);
      await get().refresh();
    } catch (e) {
      set({ error: String(e.message || e) });
    } finally {
      set({ busy: false });
    }
  },

  debrief: null,
  backlog: null,

  async finish() {
    try {
      const sitting = await api.finish(get().sitting.id);
      set({ sitting });
      const res = await api.generateDebrief(sitting.id);
      set({ debrief: res.packet });
    } catch (e) {
      set({ error: String(e.message || e) });
    }
  },

  async triage(findingId, state, disposition) {
    try {
      await api.triage(findingId, state, disposition);
      const res = await api.generateDebrief(get().sitting.id);
      set({ debrief: res.packet });
    } catch (e) {
      set({ error: String(e.message || e) });
    }
  },

  async loadBacklog() {
    try {
      const res = await api.backlogBlock(get().sitting.id);
      set({ backlog: res.block });
    } catch (e) {
      set({ error: String(e.message || e) });
    }
  },
}));
