// HS-134-05 — the recipe profile_id writer guard. Only RecipeEditor may
// write profile_id to a recipe. Get Info hands off — it summarizes and
// delegates. This test FAILS when a second writer appears (the same
// pattern as settingsWriters.test.ts).
import { readFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { describe, expect, it } from "vitest";

const DESK_SRC = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../..",
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

/** Does a source file write `profile_id` to a recipe?
 *
 * Detection heuristic (matching the two known write mechanisms):
 * - `updatePrimitive("recipe"` + `profile_id:` — the direct store path
 * - `useDebouncedSave("recipe"` + `profile_id:` — the editor save path
 *
 * Both produce a recipe PUT with `{ profile_id: ... }`. A file that
 * merely reads `profile_id` (e.g. the API layer) won't match. */
export function writesRecipeProfileId(content: string): boolean {
  if (!/profile_id\s*:/.test(content)) return false;
  if (/updatePrimitive\s*\(\s*["']recipe["']/.test(content)) return true;
  if (/useDebouncedSave\s*\(\s*["']recipe["']/.test(content)) return true;
  return false;
}

describe("the recipe profile_id writer guard (HS-134-05)", () => {
  const files = walk(DESK_SRC).map((full) => ({
    name: path.relative(DESK_SRC, full),
    content: readFileSync(full, "utf8"),
  }));

  it("only RecipeEditor writes profile_id to a recipe", () => {
    const writers = files
      .filter((f) => writesRecipeProfileId(f.content))
      .map((f) => f.name)
      .sort();
    expect(writers).toEqual([
      "desk/pullouts/editors/RecipeEditor.tsx",
    ]);
  });

  it("infoContract does NOT write profile_id", () => {
    const contract = files.find((f) => f.name.endsWith("infoContract.ts"))!;
    expect(writesRecipeProfileId(contract.content)).toBe(false);
  });

  it("FAILS on a genuine second writer", () => {
    const rogue = `
      import { useDesk } from "../store";
      const save = () => {
        useDesk.getState().updatePrimitive("recipe", id, {
          profile_id: value || null,
        });
      };
    `;
    expect(writesRecipeProfileId(rogue)).toBe(true);
  });

  it("FAILS on a rogue editor-style writer", () => {
    const rogue = `
      const save = useDebouncedSave("recipe", id);
      save({ profile_id: value || null });
    `;
    expect(writesRecipeProfileId(rogue)).toBe(true);
  });

  it("does NOT false-positive on read-only profile_id access", () => {
    // API layers read profile_id but do not write it to a recipe.
    const readOnly = `
      const profileId = wireStringOrNull(w, "profile_id");
    `;
    expect(writesRecipeProfileId(readOnly)).toBe(false);
  });
});
