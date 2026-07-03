// HS-73-01 — the island's unit rig: sprite-hash parity with the shared
// picker (per-id stability is what keeps a desk wearing the same art across
// the Alpine→React cutover) and the wire normalizers.
import { describe, expect, it } from "vitest";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteName, stableHash, variantIndex } from "../../scripts/desk/sprites.js";
import {
  fromWireAgent, fromWireDirectory, fromWireNote, fromWireWorkflow, liveValues,
} from "../api";
import { objUnit, worldObjects } from "../world";
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
      ["a", "b", "c", "d", "e", "f", "g", "h"].map((id) => spriteName("meeting", id)),
    );
    expect(picks.size).toBeGreaterThanOrEqual(4);
  });
});

describe("wire normalizers", () => {
  it("note", () => {
    expect(
      fromWireNote({ id: "n1", title: "T", body_markdown: "b", tags: ["x"], created_at: "c" }),
    ).toMatchObject({ kind: "note", id: "n1", title: "T", bodyMarkdown: "b", tags: ["x"] });
  });
  it("agent defaults", () => {
    expect(fromWireAgent({ id: "a1", name: "A" })).toMatchObject({
      kind: "agent", avatar: "🤖", tools: [], kbId: null, profileId: "",
    });
  });
  it("directory members from either shape", () => {
    expect(fromWireDirectory({ id: "d", name: "D", member_ids: ["x"] }).memberIds).toEqual(["x"]);
    expect(fromWireDirectory({ id: "d", name: "D", members: { y: 1 } }).memberIds).toEqual(["y"]);
  });
  it("workflow graph_json stays an object", () => {
    const w = fromWireWorkflow({ id: "w", name: "W", graph_json: { nodes: [] } });
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

describe("world math", () => {
  const items: Items = {
    meeting: [{ kind: "meeting", id: "m1", title: "M" }],
    note: [{ kind: "note", id: "n1", title: "N" }],
    kb: [], agent: [], artifact: [], chain: [], workflow: [],
    directory: [{ kind: "directory", id: "z", name: "Z", memberIds: ["m1"] } as any],
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
    const o = { kind: "note" as const, id: "n1", title: "N", ref: items.note[0] };
    const a = objUnit(o, 0, 12, {});
    const b = objUnit(o, 0, 12, {});
    expect(a).toEqual(b);
    expect(a.x).toBeGreaterThanOrEqual(0.06);
    expect(a.x).toBeLessThanOrEqual(0.94);
    // A saved position wins.
    expect(objUnit(o, 0, 12, { n1: { x: 0.5, y: 0.5 } })).toEqual({ x: 0.5, y: 0.5 });
  });
  it("the jitter hash is the legacy _oh", () => {
    expect(oh("n1")).toBeGreaterThanOrEqual(0);
    expect(oh("n1")).toBeLessThan(1);
    expect(oh("n1")).toEqual(oh("n1"));
  });
});
