// PHILO-16 (L7): departure is representation.
import { describe, expect, it } from "vitest";
import { createDepartures, inheritedAtMount } from "../departure";

describe("departures", () => {
  it("retains an immutable snapshot until it is released", () => {
    const d = createDepartures();
    const seen: number[] = [];
    d.subscribe(() => seen.push(d.list().length));
    const snap = d.retainSnapshot("w", { x: 1, y: 2, w: 3, h: 4 }, "front");
    expect(d.list()).toHaveLength(1);
    expect(Object.isFrozen(snap)).toBe(true);
    expect(Object.isFrozen(snap.rect)).toBe(true);
    d.release("w");
    expect(d.list()).toHaveLength(0);
    expect(seen).toEqual([1, 0]);
  });

  it("the same window may leave twice; release by key frees one", () => {
    const d = createDepartures();
    const a = d.retainSnapshot("w", { x: 0, y: 0, w: 1, h: 1 }, "near");
    d.retainSnapshot("w", { x: 0, y: 0, w: 1, h: 1 }, "front");
    d.release("w", a.key);
    expect(d.list().map((s) => s.plane)).toEqual(["front"]);
  });

  it("windows present at mount are inherited until they close", () => {
    const i = inheritedAtMount(["a", "b"]);
    expect(i.isInherited("a")).toBe(true);
    expect(i.isInherited("a")).toBe(true); // idempotent (a double-run mount)
    expect(i.isInherited("c")).toBe(false);
    i.forget("a");
    expect(i.isInherited("a")).toBe(false);
    expect(i.isInherited("b")).toBe(true);
  });
});
