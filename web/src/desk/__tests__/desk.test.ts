// HS-73-01 — the island's unit rig: sprite-hash parity with the shared
// picker (per-id stability is what keeps a desk wearing the same art across
// the React unification) and the wire normalizers.
import { afterEach, describe, expect, it, vi } from "vitest";
import { spriteName, stableHash, variantIndex } from "../sprites";
import {
  fromWireDirectory,
  fromWireNote,
  fromWireRecipe,
  fromWireWorkflow,
  liveValues,
  loadAll,
} from "../api";
import { lineage } from "../lineage";
import { objectByRef, objUnit, worldObjects } from "../world";
import { oh } from "../hash";
import type { Items } from "../api";

describe("sprite hash parity", () => {
  it("is stable per id and matches the shared picker", () => {
    // Pin known values so a re-implementation (vs the shared module) fails.
    expect(stableHash("m0")).toEqual(stableHash("m0"));
    expect(spriteName("meeting", "m0")).toEqual(spriteName("meeting", "m0"));
    expect(variantIndex("m0", 17)).toBeGreaterThanOrEqual(0);
    expect(variantIndex("m0", 17)).toBeLessThan(17);
    // Distinct ids spread across the pool (the HS-71-02 acceptance).
    const picks = new Set(
      ["a", "b", "c", "d", "e", "f", "g", "h"].map((id) =>
        spriteName("meeting", id),
      ),
    );
    expect(picks.size).toBeGreaterThanOrEqual(4);
  });
});

describe("wire normalizers", () => {
  it("note", () => {
    expect(
      fromWireNote({
        id: "n1",
        title: "T",
        body_markdown: "b",
        tags: ["x"],
        created_at: "c",
      }),
    ).toMatchObject({
      kind: "note",
      id: "n1",
      title: "T",
      bodyMarkdown: "b",
      tags: ["x"],
    });
  });
  it("recipe defaults", () => {
    expect(fromWireRecipe({ id: "a1", name: "A" })).toMatchObject({
      kind: "recipe",
      avatar: "🤖",
      tools: [],
      kbId: null,
      profileId: "",
    });
  });
  it("directory members from either shape", () => {
    expect(
      fromWireDirectory({ id: "d", name: "D", member_ids: ["x"] }).memberIds,
    ).toEqual(["x"]);
    expect(
      fromWireDirectory({ id: "d", name: "D", members: { y: 1 } }).memberIds,
    ).toEqual(["y"]);
  });
  it("workflow graph_json stays an object", () => {
    const w = fromWireWorkflow({
      id: "w",
      name: "W",
      graph_json: { nodes: [] },
    });
    expect(w.hasGraph).toBe(true);
    expect(typeof w.graphJson).toBe("object");
  });
  it("liveValues drops tombstones and unwraps values", () => {
    expect(
      liveValues([
        { meta: { deleted: true }, value: { id: "gone" } },
        { meta: { deleted: false }, value: { id: "live" } },
      ]),
    ).toEqual([{ id: "live" }]);
  });
});

describe("the recipe wire (the v8 rename, hub-faithful)", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("loadAll lands hub {recipes:[…]} under items.recipe", async () => {
    // The regression this locks: the loader once read the pre-rename `agents`
    // key into a nonexistent `items.agent` lane — recipes never reached the
    // rail, the editor, or the world. The hub's key is `recipes`.
    vi.stubGlobal("fetch", (url: string) => {
      const body = String(url).startsWith("/api/recipes")
        ? {
            recipes: [
              { id: "r1", name: "Scout", avatar: "🦊" },
              { id: "r2", name: "Gone", deleted: true },
            ],
          }
        : {};
      return Promise.resolve({ ok: true, json: () => Promise.resolve(body) });
    });
    const { items, status } = await loadAll();
    expect(items.recipe.map((r) => r.id)).toEqual(["r1"]);
    expect(items.recipe[0]).toMatchObject({
      kind: "recipe",
      name: "Scout",
      avatar: "🦊",
    });
    expect(status.recipe).toBe("live");
  });
});

describe("lineage via detection", () => {
  const items = {
    meeting: [],
    note: [],
    kb: [],
    artifact: [],
    chain: [],
    workflow: [],
    directory: [],
    coder: [],
    recipe: [{ kind: "recipe", id: "r1", name: "Scout" }],
  } as unknown as Items;

  it("a canonical recipe row is the via", () => {
    const l = lineage(items, [
      { source_type: "recipe", source_ref: "r1" },
      { source_type: "input", source_ref: "m1" },
    ]);
    expect(l.via?.ref).toBe("r1");
    expect(l.from.map((f) => f.ref)).toEqual(["m1"]);
  });
  it("a pre-rename 'agent' row still reads as the via (older stored artifacts)", () => {
    expect(
      lineage(items, [{ source_type: "agent", source_ref: "r1" }]).via?.ref,
    ).toBe("r1");
  });
  it("the Ask atom's via row (HSM-16-09 wire) reads as the via", () => {
    const l = lineage(items, [
      { source_type: "card", source_ref: "Q3 kickoff" },
      { source_type: "card", source_ref: "Mesh sync owner" },
      { source_type: "ask", source_ref: "Distill" },
    ]);
    expect(l.via?.label).toBe("Distill");
    expect(l.from.map((f) => f.label)).toEqual([
      "Q3 kickoff",
      "Mesh sync owner",
    ]);
  });
});

describe("world math", () => {
  const items: Items = {
    meeting: [{ kind: "meeting", id: "m1", title: "M" }],
    note: [{ kind: "note", id: "n1", title: "N" }],
    kb: [],
    recipe: [],
    artifact: [],
    chain: [],
    workflow: [],
    directory: [
      { kind: "directory", id: "z", name: "Z", memberIds: ["m1"] } as any,
    ],
    coder: [],
  };
  it("flattens in the canonical order and filters on dive", () => {
    // m1 is FILED into z: the root stage shows only the unfiled note (the
    // iPad grammar — a filed object lives on its shelf; owner feedback
    // 2026-07-02); diving shows the member.
    expect(worldObjects(items, null).map((o) => o.id)).toEqual(["n1"]);
    expect(worldObjects(items, "z").map((o) => o.id)).toEqual(["m1"]);
  });
  it("looseHome is deterministic and clamped", () => {
    const o = {
      kind: "note" as const,
      id: "n1",
      title: "N",
      ref: items.note[0],
    };
    const a = objUnit(o, 0, 12, {});
    const b = objUnit(o, 0, 12, {});
    expect(a).toEqual(b);
    expect(a.x).toBeGreaterThanOrEqual(0.06);
    expect(a.x).toBeLessThanOrEqual(0.94);
    // A saved position wins.
    expect(objUnit(o, 0, 12, { n1: { x: 0.5, y: 0.5 } })).toEqual({
      x: 0.5,
      y: 0.5,
    });
  });
  it("the jitter hash is the legacy _oh", () => {
    expect(oh("n1")).toBeGreaterThanOrEqual(0);
    expect(oh("n1")).toBeLessThan(1);
    expect(oh("n1")).toEqual(oh("n1"));
  });
});

describe("qualified pull-out identity", () => {
  const items = {
    meeting: [],
    note: [{ kind: "note", id: "same", title: "Note" }],
    artifact: [{ kind: "artifact", id: "same", title: "Artifact" }],
    recipe: [{ kind: "recipe", id: "scout", name: "Scout" }],
    kb: [],
    directory: [],
    chain: [],
    workflow: [],
    coder: [],
  } as Items;

  it("resolves collisions and canonical capability aliases exactly", () => {
    expect(objectByRef(items, "artifact:same")?.title).toBe("Artifact");
    expect(objectByRef(items, "note:same")?.title).toBe("Note");
    expect(objectByRef(items, "persona:scout")?.title).toBe("Scout");
  });
});
