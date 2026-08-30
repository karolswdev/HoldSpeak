// HS-132-06 — the swallowed-write guard.
//
// The desk's dominant defect class was the silent write: a `try { …POST… }
// catch { /* */ }` that left the user staring at a no-op. This census reads
// the desk sources and fails when a write is caught into an empty block.
// The ledger below records the swallows this story did not own; it is a
// ceiling, never a licence — adding one more anywhere fails the guard.
import { describe, expect, it } from "vitest";

const sources = import.meta.glob<string>("/src/desk/**/*.{ts,tsx}", {
  eager: true,
  import: "default",
  query: "?raw",
});

/** Names that read rather than write; a bare catch around them is not this bug. */
const READ_PREFIX = /^(fetch|load|get|list|resolve|read|use)/;

/** Modules whose exports are hub calls. */
const API_MODULE = /(^|\/)api$|lib\/api|\/threads$|repository|settingsWrite|store$/;

function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/[^\n]*/g, "");
}

function forwardMatch(source: string, open: number): number {
  let depth = 0;
  for (let i = open; i < source.length; i++) {
    if (source[i] === "{") depth++;
    else if (source[i] === "}" && --depth === 0) return i;
  }
  return -1;
}

function backwardMatch(source: string, close: number): number {
  let depth = 0;
  for (let i = close; i >= 0; i--) {
    if (source[i] === "}") depth++;
    else if (source[i] === "{" && --depth === 0) return i;
  }
  return -1;
}

function writeNames(source: string): Set<string> {
  const names = new Set<string>();
  const imports = /import\s*\{([^}]*)\}\s*from\s*["']([^"']+)["']/g;
  let match: RegExpExecArray | null;
  while ((match = imports.exec(source))) {
    if (!API_MODULE.test(match[2])) continue;
    for (const raw of match[1].split(",")) {
      const name = (raw.trim().split(/\s+as\s+/).pop() || "").trim();
      if (!name || READ_PREFIX.test(name)) continue;
      names.add(name);
    }
  }
  return names;
}

/**
 * Every `try { <a write> } catch { }` whose catch body holds no statement.
 * Returns the 1-based line of each offending `catch`.
 */
export function swallowedWrites(source: string): number[] {
  const names = writeNames(source);
  const catches = /\bcatch\s*(\([^)]*\))?\s*\{/g;
  const found: number[] = [];
  let match: RegExpExecArray | null;
  while ((match = catches.exec(source))) {
    const open = source.indexOf("{", match.index);
    const close = forwardMatch(source, open);
    if (close < 0) continue;
    if (stripComments(source.slice(open + 1, close)).trim().length > 0) continue;

    let cursor = match.index - 1;
    while (cursor >= 0 && /\s/.test(source[cursor])) cursor--;
    if (source[cursor] !== "}") continue;
    const tryOpen = backwardMatch(source, cursor);
    if (tryOpen < 0) continue;
    if (!/\btry\s*$/.test(source.slice(Math.max(0, tryOpen - 12), tryOpen))) continue;

    const tryBody = source.slice(tryOpen, cursor + 1);
    const writes =
      /\bapi(Request|Fetch)\s*\(/.test(tryBody) ||
      [...names].some((name) => new RegExp(`\\b${name}\\s*\\(`).test(tryBody));
    if (!writes) continue;
    found.push(source.slice(0, match.index).split("\n").length);
  }
  return found;
}

/**
 * Swallows this story did not own, with the verb behind them. Each entry is
 * a debt, not a pattern: shrink it, never grow it.
 */
const KNOWN_SWALLOWS: Record<string, number> = {
  "/src/desk/deliveryFactory.ts": 1, // delivery claim POST
  "/src/desk/gate.ts": 1, // gate decision POST
  "/src/desk/prReceipts.ts": 1, // PR receipt POST
  "/src/desk/steering.ts": 3, // steering submit/ack/clear
  "/src/desk/store/dataSlice.ts": 5, // update/delete/file/remove/knowledge
  "/src/desk/store/recordingSlice.ts": 1, // recording stop POST
  "/src/desk/store/scheduledRecordingSlice.ts": 1, // HS-136-03: delete schedule
};

describe("HS-132-06 swallowed-write guard", () => {
  it("flags a write caught into an empty block", () => {
    const sample = `
      import { addWorkbenchItem } from "../api";
      async function go() {
        try {
          await addWorkbenchItem("w", {});
        } catch { /* */ }
      }
    `;
    expect(swallowedWrites(sample)).toHaveLength(1);
  });

  it("flags a bare apiRequest swallow with a named binding", () => {
    const sample = `
      import { apiRequest } from "../../lib/api";
      async function go() {
        try {
          await apiRequest("/api/x", { method: "POST" });
        } catch (error) {
        }
      }
    `;
    expect(swallowedWrites(sample)).toHaveLength(1);
  });

  it("passes a write that reports into the receipt channel", () => {
    const sample = `
      import { addWorkbenchItem } from "../api";
      async function go() {
        try {
          await addWorkbenchItem("w", {});
        } catch (cause) {
          reportWriteFailure("ADD ITEM", cause);
        }
      }
    `;
    expect(swallowedWrites(sample)).toEqual([]);
  });

  it("ignores bare catches that guard no write", () => {
    const sample = `
      function positions() {
        try {
          return JSON.parse(localStorage.getItem("k") || "{}");
        } catch {
        }
      }
    `;
    expect(swallowedWrites(sample)).toEqual([]);
  });

  it("keeps every desk write out of a bare catch", () => {
    const offenders: string[] = [];
    for (const [path, source] of Object.entries(sources)) {
      if (/\.test\.tsx?$/.test(path)) continue;
      const lines = swallowedWrites(source);
      const allowed = KNOWN_SWALLOWS[path] ?? 0;
      if (lines.length > allowed) {
        offenders.push(`${path}: ${lines.length} swallowed (allowed ${allowed}) at ${lines.join(", ")}`);
      }
    }
    expect(offenders).toEqual([]);
  });

  it("keeps the debt ledger pointed at real files", () => {
    // The counts are a ceiling: pay a debt down and lower the number.
    for (const [path, allowed] of Object.entries(KNOWN_SWALLOWS)) {
      const source = sources[path];
      expect(source, `${path} missing`).toBeTruthy();
      expect(swallowedWrites(source).length, path).toBeLessThanOrEqual(allowed);
    }
  });

  it("leaves the wired surfaces with no swallowed write at all", () => {
    for (const path of [
      "/src/desk/components/WorkbenchWindow.tsx",
      "/src/desk/components/EmptyDesk.tsx",
    ]) {
      expect(swallowedWrites(sources[path]), path).toEqual([]);
    }
  });
});
