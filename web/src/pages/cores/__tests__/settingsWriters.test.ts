// HS-130-07 — the one-writer guard. This is an ALLOWLIST keyed on PUT
// callers (which FILES issue `PUT /api/settings`), NOT on controls — so a
// surface may render many menu/shortcut/context-menu projections of one verb
// without tripping the guard. It fails when a genuine SECOND persistent writer
// of a settings subtree appears.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { describe, expect, it } from "vitest";

const WEB_SRC = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../..",
);

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    const s = statSync(full);
    if (s.isDirectory()) out.push(...walk(full));
    else if (/\.(ts|tsx)$/.test(entry) && !/\.test\.tsx?$/.test(entry))
      out.push(full);
  }
  return out;
}

/** Does a source blob issue a PUT to the top-level `/api/settings` document
 * (secrets sub-routes ride backtick template literals, never this double-quoted
 * literal, so they are excluded)? */
export function putsToSettings(content: string): boolean {
  const marker = '"/api/settings"';
  let from = 0;
  for (;;) {
    const at = content.indexOf(marker, from);
    if (at === -1) return false;
    // The `apiFetch(..., { method: "PUT" ... })` init trails the path.
    const tail = content.slice(at, at + 240);
    if (/method:\s*"PUT"/.test(tail)) return true;
    from = at + marker.length;
  }
}

/** The enablement subtrees that must have exactly ONE persistent writer. */
const ENABLEMENT_KEYS = [
  "pipeline: { enabled",
  "macros: { enabled",
];

function writesEnablement(content: string): string[] {
  if (!putsToSettings(content)) return [];
  return ENABLEMENT_KEYS.filter((key) => content.includes(key));
}

describe("the subtree-writer allowlist (HS-130-07)", () => {
  const files = walk(WEB_SRC).map((full) => ({
    name: path.relative(WEB_SRC, full),
    content: readFileSync(full, "utf8"),
  }));

  it("only the allowlisted files PUT /api/settings", () => {
    const writers = files
      .filter((f) => putsToSettings(f.content))
      .map((f) => f.name)
      .sort();
    // SettingsCore is the canonical full-document writer; CommandsCore writes
    // ONLY the macro `items`. No third writer is permitted.
    expect(writers).toEqual([
      "pages/cores/CommandsCore.tsx",
      "pages/cores/SettingsCore.tsx",
    ]);
  });

  it("no persistent enablement writer exists outside Settings", () => {
    const offenders = files
      .filter((f) => f.name !== "pages/cores/SettingsCore.tsx")
      .filter((f) => writesEnablement(f.content).length > 0)
      .map((f) => f.name);
    expect(offenders).toEqual([]);
  });

  it("the demoted feature surfaces no longer PUT settings", () => {
    const readiness = files.find((f) =>
      f.name.endsWith("dictation/Readiness.tsx"),
    )!;
    const speakDeck = files.find((f) =>
      f.name.endsWith("dictation/useSpeakDeck.ts"),
    )!;
    expect(putsToSettings(readiness.content)).toBe(false);
    expect(putsToSettings(speakDeck.content)).toBe(false);
  });

  it("CommandsCore writes items but not the enablement bit", () => {
    const commands = files.find((f) =>
      f.name.endsWith("pages/cores/CommandsCore.tsx"),
    )!;
    expect(putsToSettings(commands.content)).toBe(true);
    expect(commands.content).toContain("macros: { items");
    expect(writesEnablement(commands.content)).toEqual([]);
  });

  it("verb projections of one writer are NOT false-positived", () => {
    // A file that opens Settings (a menu/shortcut projection) is not a writer.
    const projection = `openSurfaceOr("configure-settings", "/settings", "voice-typing")`;
    expect(putsToSettings(projection)).toBe(false);
  });

  it("FAILS on a genuine second persistent writer", () => {
    // A synthetic rogue surface that PUTs the enablement bit is caught by the
    // same detection the allowlist rests on.
    const rogue = `
      await apiFetch("/api/settings", {
        method: "PUT",
        json: { dictation: { macros: { enabled: true } } },
      });
    `;
    expect(putsToSettings(rogue)).toBe(true);
    expect(writesEnablement(rogue)).toEqual(["macros: { enabled"]);
  });
});
