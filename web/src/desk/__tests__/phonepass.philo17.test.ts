// PHILO-17 (phonepass): a read that lands never moves a palette row he can see.
import { describe, expect, it } from "vitest";
import { stableDeck } from "../components/DeskToolShelf";
import { allResolved } from "../../features/project-room/roomReads";

const r = (...ids: string[]) => ids.map((id) => ({ id }));
const ids = (rows: Array<{ id: string }>) => rows.map((x) => x.id);

describe("stableDeck", () => {
  it("nothing drawn yet: the fresh drawing", () => {
    expect(ids(stableDeck(null, r("a", "b", "c"), r("a", "b")))).toEqual(["a", "b"]);
  });

  it("drawn rows keep their places; a row the fresh drawing adds goes below them", () => {
    // the people read lands: a PERSON row ranks first, but he sees a, b drawn
    expect(ids(stableDeck(["a", "b"], r("p", "a", "b"), r("p", "a", "b")))).toEqual(["a", "b", "p"]);
  });

  it("a late rank change across the section limit evicts no drawn row (11 projects, the 11th promoted)", () => {
    const drawn = ["p01", "p02", "p03", "p04", "p05", "p06", "p07", "p08", "p09", "p10"];
    const full = r("p11", ...drawn); // the count lands: p11 ranks first
    const fresh = r("p11", ...drawn.slice(0, 9)); // the limit of 10 would cut p10
    expect(ids(stableDeck(drawn, full, fresh))).toEqual([...drawn, "p11"]);
  });

  it("only a row that is no longer a candidate leaves", () => {
    expect(ids(stableDeck(["a", "b", "c"], r("c", "a", "m"), r("c", "a", "m")))).toEqual(["a", "c", "m"]);
  });
});

describe("allResolved (the Room's first reads)", () => {
  it("waits for every named read and every reported read", () => {
    expect(allResolved({}, ["items"])).toBe(false);
    expect(allResolved({ items: true, door: false }, ["items"])).toBe(false);
    expect(allResolved({ items: true, door: true }, ["items"])).toBe(true);
  });
});
