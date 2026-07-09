import { create } from "zustand";
import { api } from "./api.js";

// Given a sitting + a scenario, the lowest step whose applicable surfaces are
// not all answered (the step the human is on). Null = scenario complete.
export function currentStep(sitting, scenario) {
  const answered = new Set(
    sitting.verdicts.map((v) => `${v.scenario_id}|${v.step_index}|${v.surface}`)
  );
  for (const step of scenario.steps) {
    const applicable = Object.entries(step.surfaces)
      .filter(([, v]) => v.applicable)
      .map(([s]) => s);
    const done = applicable.every((s) => answered.has(`${scenario.id}|${step.index}|${s}`));
    if (!done) return step;
  }
  return null;
}

export function stepAnswered(sitting, scenario, step) {
  const answered = new Set(
    sitting.verdicts.map((v) => `${v.scenario_id}|${v.step_index}|${v.surface}`)
  );
  const applicable = Object.entries(step.surfaces)
    .filter(([, v]) => v.applicable)
    .map(([s]) => s);
  return applicable.every((s) => answered.has(`${scenario.id}|${step.index}|${s}`));
}

export function verdictFor(sitting, scenarioId, stepIndex, surface) {
  return sitting.verdicts.find(
    (v) => v.scenario_id === scenarioId && v.step_index === stepIndex && v.surface === surface
  );
}

export const useStore = create((set, get) => ({
  view: "home",
  packs: [],
  sittings: [],
  sitting: null,
  staging: null,
  stagedIds: {},
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

  async start(pack, deck) {
    set({ busy: true, error: null, staging: null, stagedIds: {}, afterRan: {} });
    try {
      const sitting = await api.createSitting(pack, deck);
      set({ sitting, view: "sitting", busy: false });
    } catch (e) {
      set({ error: String(e.message || e), busy: false });
    }
  },

  async open(id) {
    set({ busy: true, error: null, staging: null, stagedIds: {}, afterRan: {} });
    try {
      const sitting = await api.getSitting(id);
      set({ sitting, view: "sitting", busy: false });
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

  async uploadShot(scenarioId, stepIndex, surface, file) {
    return api.uploadShot(get().sitting.id, scenarioId, stepIndex, surface, file);
  },

  // Speak-to-fill: WAV in, transcribed text out via the run's own transcribe
  // route. Returns { ok, text } | { ok:false, error }.
  async transcribeNote(wavBlob) {
    return api.transcribe(get().sitting.id, wavBlob);
  },

  async runAfter(scenarioId, stepIndex) {
    const key = `${scenarioId}|${stepIndex}`;
    if (get().afterRan[key]) return;
    set((st) => ({ afterRan: { ...st.afterRan, [key]: true }, busy: true }));
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
