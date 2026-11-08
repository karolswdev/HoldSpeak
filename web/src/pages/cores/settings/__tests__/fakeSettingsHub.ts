// The fake hub of the one-writer tests (2026-11-08): one settings document; a
// write with a stale `_revision` gets the hub's 409 word and its revision.
import type { Mock } from "vitest";

export const STALE = "Settings changed in another surface since you loaded them. Reload and reapply your edit.";

type ApiErrorClass = new (status: number, message: string, payload?: unknown) => Error;

export function fakeSettingsHub(apiFetch: Mock, ApiError: ApiErrorClass, initial: Record<string, unknown>) {
  let doc = JSON.parse(JSON.stringify(initial)) as Record<string, unknown>;
  let revision = Number(String(doc._revision ?? "r1").replace(/^r/, "")) || 1;
  const merge = (target: Record<string, unknown>, patch: Record<string, unknown>) => {
    for (const [key, value] of Object.entries(patch)) {
      const current = target[key];
      if (value && typeof value === "object" && !Array.isArray(value) && current && typeof current === "object" && !Array.isArray(current)) {
        merge(current as Record<string, unknown>, value as Record<string, unknown>);
      } else target[key] = value;
    }
  };
  const fallback = apiFetch.getMockImplementation();
  apiFetch.mockImplementation(async (url: string, init?: { method?: string; json?: Record<string, unknown> }) => {
    if (url !== "/api/settings") return fallback ? fallback(url, init) : {};
    if (init?.method !== "PUT") return JSON.parse(JSON.stringify(doc));
    const { _revision, ...patch } = init.json ?? {};
    if (_revision !== undefined && _revision !== doc._revision) {
      throw new ApiError(409, STALE, { success: false, error: STALE, revision: doc._revision });
    }
    merge(doc, patch);
    revision += 1;
    doc = { ...doc, _revision: `r${revision}` };
    return { success: true, settings: JSON.parse(JSON.stringify(doc)) };
  });
  return {
    get doc() { return doc; },
    moveElsewhere() { revision += 1; doc = { ...doc, _revision: `r${revision}` }; },
    puts: () => apiFetch.mock.calls.filter(([url, init]) => url === "/api/settings" && init?.method === "PUT"),
  };
}
