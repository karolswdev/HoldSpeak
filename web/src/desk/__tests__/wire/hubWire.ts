// The hub's own answers, captured on a real hub by
// tests/integration/test_desk_agents_wire.py (the test diet, 2026-10-11).
// That Python file reads the same routes on every run and fails when a stored
// answer's shape is not the hub's shape (SCAR LAW: a double that lies about
// the field a check reads proves nothing). The *.app.test.tsx successors read
// these files as their apiFetch answers; they never invent a field.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const DIR = dirname(fileURLToPath(import.meta.url));

export interface HubWire<T> {
  captured_at: string;
  wire: T;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function hubWire<T = any>(name: string): HubWire<T> {
  return JSON.parse(readFileSync(join(DIR, `${name}.wire.json`), "utf8")) as HubWire<T>;
}
