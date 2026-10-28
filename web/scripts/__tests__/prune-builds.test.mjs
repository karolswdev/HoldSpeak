import { mkdirSync, mkdtempSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";

import { readBuilds, recordBuild } from "../prune-builds.mjs";

let out = "";

/** One fake build: its chunks land in assets/, its index.html names its entry. */
function build(n) {
  const names = [`index-${n}.js`, `desk-${n}.js`, `NoteCore-${n}.js`, `desk-${n}.css`];
  for (const name of names) writeFileSync(join(out, "assets", name), `// build ${n}\n`);
  writeFileSync(join(out, "index.html"), `<script src="/_built/assets/index-${n}.js"></script>`);
  return recordBuild(out, names, { buildId: `b${n}` });
}

const kept = () => readdirSync(join(out, "assets")).sort();

afterEach(() => rmSync(out, { recursive: true, force: true }));

describe("prune-builds", () => {
  it("three builds keep three sets; a fourth drops the oldest", () => {
    out = mkdtempSync(join(tmpdir(), "prune-builds-"));
    mkdirSync(join(out, "assets"));
    writeFileSync(join(out, "assets", "stale-old.js"), "// from before the manifest\n");

    build(1);
    expect(kept()).not.toContain("stale-old.js");
    build(2);
    build(3);
    expect(kept()).toHaveLength(12);
    expect(readBuilds(out).map((b) => b.build_id)).toEqual(["b3", "b2", "b1"]);

    const { removed } = build(4);
    expect(removed).toEqual(["NoteCore-1.js", "desk-1.css", "desk-1.js", "index-1.js"]);
    expect(kept()).toHaveLength(12);
    expect(kept().some((name) => name.endsWith("-1.js"))).toBe(false);
    expect(readBuilds(out).map((b) => b.build_id)).toEqual(["b4", "b3", "b2"]);
  });

  it("an unchanged rebuild keeps one entry, not two", () => {
    out = mkdtempSync(join(tmpdir(), "prune-builds-"));
    mkdirSync(join(out, "assets"));
    build(1);
    build(2);
    build(2);
    expect(readBuilds(out).map((b) => b.build_id)).toEqual(["b2", "b1"]);
    expect(kept()).toHaveLength(8);
  });
});
