/** The desk chunk holds what the first paint needs (measure 2026-11-08).
 * Three window cores are not on glass at first paint, so each loads in its
 * own chunk when its window opens: the Program window, the note window and
 * the Room. The build puts every module that DeskApp reaches by a static
 * import into the "desk" chunk (vite.config.ts chunkFor), so a static path
 * from DeskApp to one of these cores puts it back in that chunk.
 *
 * This is a lexical walk of the source graph: static imports and re-exports
 * are followed; dynamic import() and type-only imports are not (the build
 * erases type imports and splits at import()). */
import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";

const SRC = path.resolve(__dirname, "../..");
const ENTRY = "desk/DeskApp.tsx";
const LAZY_CORES = [
  "desk/programs/ProgramWindow.tsx",
  "desk/thought-workspace/ThoughtWorkspaceWindow.tsx",
  "features/project-room/ProjectRoomCore.tsx",
];

const STATIC_RE = /^\s*(import|export)\s+(?!type\b)([\s\S]*?)\s*from\s*["']([^"']+)["']|^\s*import\s+["']([^"']+)["']/gm;

function typeOnly(clause: string): boolean {
  const named = clause.trim().match(/^\{([\s\S]*)\}$/);
  if (!named) return false;
  const parts = named[1].split(",").map((part) => part.trim()).filter(Boolean);
  return parts.length > 0 && parts.every((part) => part.startsWith("type "));
}

function resolve(from: string, spec: string): string | null {
  if (!spec.startsWith(".")) return null;
  const base = path.join(path.dirname(from), spec);
  for (const candidate of [base, `${base}.ts`, `${base}.tsx`, path.join(base, "index.ts"), path.join(base, "index.tsx")]) {
    const full = path.join(SRC, candidate);
    if (/\.tsx?$/.test(candidate) && fs.existsSync(full) && fs.statSync(full).isFile()) return candidate;
  }
  return null;
}

function staticClosure(entry: string): Map<string, string | null> {
  const via = new Map<string, string | null>([[entry, null]]);
  const queue = [entry];
  while (queue.length) {
    const name = queue.shift() as string;
    const text = fs.readFileSync(path.join(SRC, name), "utf8");
    for (const match of text.matchAll(STATIC_RE)) {
      if (match[2] !== undefined && typeOnly(match[2])) continue;
      const next = resolve(name, match[3] ?? match[4]);
      if (!next || via.has(next)) continue;
      via.set(next, name);
      queue.push(next);
    }
  }
  return via;
}

describe("the desk chunk", () => {
  const closure = staticClosure(ENTRY);

  it("reaches the shell it paints", () => {
    expect(closure.has("desk/components/Pullout.tsx")).toBe(true);
    expect(closure.has("desk/drawer/DrawerWindow.tsx")).toBe(true);
  });

  it.each(LAZY_CORES)("does not statically import %s", (core) => {
    const chain: string[] = [];
    for (let at: string | null | undefined = core; at; at = closure.get(at)) chain.unshift(at);
    expect(closure.has(core) ? chain.join(" -> ") : "not in the desk chunk").toBe("not in the desk chunk");
  });
});
