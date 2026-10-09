// PHILO-16 (L3): depth numbers in, planes out.
import { describe, expect, it } from "vitest";
import {
  assignPlanes,
  depthFromOrder,
  orderFromDepth,
  raise,
  rankOf,
  seat,
  sendBack,
  unseat,
  type StackState,
} from "../planes";

const wins = (depth: Record<string, number>, minimized: string[] = []) =>
  Object.entries(depth).map(([id, d]) => ({ id, depth: d, minimized: minimized.includes(id) }));

describe("planes", () => {
  it("three windows are front, near and far", () => {
    const p = assignPlanes(wins({ a: 1, b: 3, c: 2 }));
    expect(p.get("b")).toBe("front");
    expect(p.get("c")).toBe("near");
    expect(p.get("a")).toBe("far");
  });

  it("a minimized window keeps its depth and is seated, not front", () => {
    const p = assignPlanes(wins({ a: 1, b: 9, c: 2 }, ["b"]));
    expect(p.get("b")).toBe("seated");
    expect(p.get("c")).toBe("front");
    expect(p.get("a")).toBe("near");
  });

  it("exactly one window is front, also with equal depths", () => {
    const p = assignPlanes(wins({ a: 5, b: 5, c: 5 }));
    expect([...p.values()].filter((x) => x === "front")).toHaveLength(1);
    expect(p.get("c")).toBe("front"); // the later one is nearer
  });

  it("raise takes ++highest and is idempotent for the front", () => {
    const s: StackState = { depth: { a: 1, b: 2 }, seated: [] };
    const r = raise(s, "a");
    expect(r.depth.a).toBe(3);
    expect(raise(r, "a")).toBe(r);
    expect(assignPlanes(wins(r.depth)).get("a")).toBe("front");
  });

  it("send back goes under the lowest shown window; near comes forward", () => {
    const s: StackState = { depth: { a: 1, b: 2, c: 3 }, seated: [] };
    const r = sendBack(s, "c");
    expect(r.depth.c).toBe(0);
    const p = assignPlanes(wins(r.depth));
    expect(p.get("b")).toBe("front");
    expect(p.get("a")).toBe("near");
    expect(p.get("c")).toBe("far");
  });

  it("seat keeps the depth; unseat raises", () => {
    const s: StackState = { depth: { a: 1, b: 2 }, seated: [] };
    const seated = seat(s, "b");
    expect(seated.depth.b).toBe(2);
    expect(seated.seated).toEqual(["b"]);
    const back = unseat(seat(raise(seated, "a"), "b"), "b");
    expect(back.seated).toEqual([]);
    expect(assignPlanes(wins(back.depth)).get("b")).toBe("front");
  });

  it("a reload keeps the planes from the numbers alone", () => {
    const s: StackState = { depth: { a: 1, b: 2, c: 3 }, seated: [] };
    const after = raise(sendBack(s, "c"), "a");
    const stored = JSON.parse(JSON.stringify(after.depth)) as Record<string, number>;
    expect(assignPlanes(wins(stored))).toEqual(assignPlanes(wins(after.depth)));
  });

  it("the old order migrates to depths and back", () => {
    const depth = depthFromOrder(["x", "y", "z"]);
    expect(depth).toEqual({ x: 1, y: 2, z: 3 });
    expect(orderFromDepth(depth)).toEqual(["x", "y", "z"]);
    expect(rankOf(wins(depth)).get("z")).toBe(2);
  });
});
