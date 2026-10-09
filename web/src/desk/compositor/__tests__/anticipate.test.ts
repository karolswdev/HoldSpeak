// PHILO-16 (L2): anticipate, then follow.
import { describe, expect, it } from "vitest";
import { ANTICIPATED_FRONT, anticipate, createPresentations, type WindowRecord } from "../anticipate";
import { assignPlanes } from "../planes";

function deferred() {
  let resolve!: () => void;
  let reject!: (e: unknown) => void;
  const promise = new Promise<void>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function setup(records: Record<string, WindowRecord>) {
  const truth = { ...records };
  const p = createPresentations((id) => truth[id]);
  const planes = () =>
    assignPlanes(Object.keys(truth).map((id) => ({ id, depth: p.view(id)!.depth, minimized: p.view(id)!.minimized })));
  return { truth, p, planes };
}

describe("anticipate", () => {
  it("shows the change at once and the record when the request resolves", async () => {
    const { truth, p, planes } = setup({ a: { depth: 1, minimized: false }, b: { depth: 2, minimized: false } });
    const req = deferred();
    const done = anticipate(p, "a", { front: true }, req.promise);
    expect(planes().get("a")).toBe("front");
    expect(p.view("a")!.depth).toBeGreaterThan(ANTICIPATED_FRONT);
    expect(p.pending("a")).toBe(1);
    truth.a = { depth: 3, minimized: false }; // the authority accepted
    req.resolve();
    await done;
    expect(p.pending("a")).toBe(0);
    expect(p.view("a")!.depth).toBe(3);
    expect(planes().get("a")).toBe("front");
  });

  it("a rejected request shows the record's truth again", async () => {
    const { p, planes } = setup({ a: { depth: 1, minimized: false }, b: { depth: 2, minimized: false } });
    const req = deferred();
    const done = anticipate(p, "a", { front: true }, req.promise);
    expect(planes().get("a")).toBe("front");
    req.reject(new Error("refused"));
    await done;
    expect(planes().get("b")).toBe("front");
    expect([...planes().values()].filter((x) => x === "front")).toHaveLength(1);
  });

  it("several changes hold together until the last one settles", async () => {
    const { p } = setup({ a: { depth: 1, minimized: false } });
    const r1 = deferred();
    const r2 = deferred();
    const d1 = anticipate(p, "a", { rect: { x: 1, y: 2, w: 300, h: 300 } }, r1.promise);
    const d2 = anticipate(p, "a", { minimized: true }, r2.promise);
    expect(p.pending("a")).toBe(2);
    r1.resolve();
    await d1;
    expect(p.view("a")).toMatchObject({ minimized: true, rect: { x: 1, y: 2, w: 300, h: 300 } });
    r2.resolve();
    await d2;
    expect(p.view("a")).toEqual({ depth: 1, minimized: false });
  });

  it("the latest anticipated front ranks above an earlier one", () => {
    const { p, planes } = setup({ a: { depth: 1, minimized: false }, b: { depth: 2, minimized: false } });
    anticipate(p, "a", { front: true }, new Promise(() => {}));
    anticipate(p, "b", { front: true }, new Promise(() => {}));
    expect(planes().get("b")).toBe("front");
    expect(planes().get("a")).toBe("near");
  });
});
