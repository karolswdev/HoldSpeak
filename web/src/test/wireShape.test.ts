// The guard itself (Astra r1 on #1107): an invented subtree under a recorded
// null or an empty recorded list is a difference.
import { describe, expect, it } from "vitest";
import { inventedFields } from "./wireShape";

describe("inventedFields", () => {
  it("an object typed where the recording holds null is a difference", () => {
    expect(inventedFields({ x: { invented: true } }, { x: null })).toEqual(["$.x: typed object, the recordings hold only null"]);
  });

  it("is proven by another recording that holds the key non-null", () => {
    expect(inventedFields({ x: { a: 1 } }, { x: null }, { x: { a: 2 } })).toEqual([]);
    expect(inventedFields({ x: { invented: 1 } }, { x: null }, { x: { a: 2 } })).toEqual(["$.x.invented: not in the hub's answer"]);
  });

  it("rows typed against an empty recorded list are a difference; no rows are not", () => {
    expect(inventedFields({ rows: [{ a: 1 }] }, { rows: [] })).toEqual([
      "$.rows: typed rows, the recorded list is empty (record a state with rows)",
    ]);
    expect(inventedFields({ rows: [] }, { rows: [] })).toEqual([]);
  });

  it("a typed row matches the recorded row it fits best", () => {
    const hub = { rows: [{ kind: "a", x: 1 }, { kind: "b", y: "s" }] };
    expect(inventedFields({ rows: [{ kind: "b", y: "t" }, { kind: "a", x: 2 }] }, hub)).toEqual([]);
    expect(inventedFields({ rows: [{ kind: "a", z: 1 }] }, hub)).toEqual(["$.rows[0].z: not in the hub's answer"]);
  });

  it("names a missing key, a type change, and keeps a typed null or leaf against null", () => {
    expect(inventedFields({ a: 1, b: "x" }, { a: "1" })).toEqual(["$.a: typed number, hub string", "$.b: not in the hub's answer"]);
    expect(inventedFields({ a: null, b: "x" }, { a: { deep: 1 }, b: null })).toEqual([]);
  });
});
