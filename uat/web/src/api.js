// The site talks ONLY to the conductor. Same-origin in production (the conductor
// serves these assets); proxied to :8799 in dev.

async function req(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch (_) {}
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

export const api = {
  health: () => req("/api/health"),
  packs: () => req("/api/packs"),
  features: () => req("/api/features"),
  listSittings: () => req("/api/sittings"),
  getSitting: (id) => req(`/api/sittings/${id}`),
  createSitting: (pack, deck) =>
    req("/api/sittings", { method: "POST", body: JSON.stringify({ pack, deck: deck || null }) }),
  stage: (id, scenarioId) =>
    req(`/api/sittings/${id}/stage`, { method: "POST", body: JSON.stringify({ scenario_id: scenarioId }) }),
  castVerdict: (id, body) =>
    req(`/api/sittings/${id}/verdicts`, { method: "POST", body: JSON.stringify(body) }),
  runAfter: (id, scenarioId, stepIndex) =>
    req(`/api/sittings/${id}/after`, {
      method: "POST",
      body: JSON.stringify({ scenario_id: scenarioId, step_index: stepIndex }),
    }),
  finish: (id) => req(`/api/sittings/${id}/finish`, { method: "POST" }),
  generateDebrief: (id) => req(`/api/sittings/${id}/debrief`, { method: "POST" }),
  triage: (findingId, triageState, disposition) =>
    req(`/api/findings/${findingId}`, {
      method: "PATCH",
      body: JSON.stringify({ triage_state: triageState, disposition: disposition || null }),
    }),
  backlogBlock: (id) => req(`/api/sittings/${id}/findings/backlog-block`),
  uploadShot: async (id, scenarioId, stepIndex, surface, file) => {
    const fd = new FormData();
    fd.append("scenario_id", scenarioId);
    fd.append("step_index", String(stepIndex));
    fd.append("surface", surface);
    fd.append("file", file);
    const res = await fetch(`/api/sittings/${id}/shots`, { method: "POST", body: fd });
    if (!res.ok) throw new Error(`shot upload failed: ${res.status}`);
    return res.json();
  },
};
