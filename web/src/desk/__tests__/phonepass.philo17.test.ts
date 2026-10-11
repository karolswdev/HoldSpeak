// PHILO-17 (phonepass): a read that lands never moves a palette row he can see.
import { describe, expect, it } from "vitest";
import { keepDrawnOrder } from "../components/DeskToolShelf";

const r = (...ids: string[]) => ids.map((id) => ({ id }));
const ids = (rows: Array<{ id: string }>) => rows.map((x) => x.id);

describe("keepDrawnOrder", () => {
  it("a fresh list keeps its ranking", () => {
    expect(ids(keepDrawnOrder([], r("a", "b", "c")))).toEqual(["a", "b", "c"]);
  });

  it("rows already drawn keep their places; a row that arrives later goes below them", () => {
    // the people read lands: a PERSON row ranks first, but he sees a, b drawn
    expect(ids(keepDrawnOrder(["a", "b"], r("p", "a", "b")))).toEqual(["a", "b", "p"]);
  });

  it("a re-rank of drawn rows (a needs-you count arrives) does not reorder them", () => {
    expect(ids(keepDrawnOrder(["a", "b", "c"], r("c", "a", "b")))).toEqual(["a", "b", "c"]);
  });

  it("a row whose read went away leaves; the rest keep their order", () => {
    expect(ids(keepDrawnOrder(["a", "b", "c"], r("c", "a", "m")))).toEqual(["a", "c", "m"]);
  });
});
