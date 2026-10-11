// Replay the hub's own recorded answers through a mocked `apiFetch` (the test
// diet, 2026-10-11). The answers come from `scripts/record_needs_you_fixture.py`
// (the real hub through TestClient, on the browser tests' seeds), so a face test
// that replays them reads no field the hub does not send (the SCAR LAW).
//
// `gets` maps a GET path to its answer. `/api/desk/needs-you` (with or without
// `?fresh=1`) answers the recorded read. Every path the table does not hold is
// noted in `misses` and answers null, as an unseeded read would.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Gets = Record<string, any>;

export function recordedGet(gets: Gets, path: string, misses?: string[]): unknown {
  const value = String(path);
  if (value in gets) return structuredClone(gets[value]);
  if (value.startsWith("/api/desk/needs-you")) return structuredClone(gets["/api/desk/needs-you?fresh=1"]);
  misses?.push(value);
  return null;
}
