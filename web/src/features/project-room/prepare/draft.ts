// HS-200-11 — the purpose survives a reload, a refusal and a trip to
// Settings.  The same custody rule as `desk/threadComposerDrafts.ts`
// (HS-200-41, ruling R2's escape hatch): sessionStorage, never
// localStorage — a purpose can be dictated meeting material, so it dies
// with the tab and never sits on disk unattended.  Every access is
// wrapped: a browser that refuses storage renders with no draft.

const STORAGE_KEY = "hs.room.prepareDrafts";

type DraftMap = Record<string, { purpose: string }>;

function session(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

function load(): DraftMap {
  const store = session();
  if (!store) return {};
  try {
    const raw = store.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    const out: DraftMap = {};
    for (const [projectId, value] of Object.entries(parsed as Record<string, unknown>)) {
      const purpose = (value as { purpose?: unknown } | null)?.purpose;
      if (typeof purpose === "string" && purpose) out[projectId] = { purpose };
    }
    return out;
  } catch {
    return {};
  }
}

function persist(drafts: DraftMap): void {
  const store = session();
  if (!store) return;
  try {
    if (!Object.keys(drafts).length) store.removeItem(STORAGE_KEY);
    else store.setItem(STORAGE_KEY, JSON.stringify(drafts));
  } catch {
    // Persistence is an enhancement; refused storage must not block typing.
  }
}

export function readPrepareDraft(projectId: string): string {
  return load()[projectId]?.purpose ?? "";
}

export function writePrepareDraft(projectId: string, purpose: string): void {
  const drafts = load();
  if (purpose) drafts[projectId] = { purpose };
  else delete drafts[projectId];
  persist(drafts);
}

export function clearPrepareDraft(projectId: string): void {
  writePrepareDraft(projectId, "");
}
