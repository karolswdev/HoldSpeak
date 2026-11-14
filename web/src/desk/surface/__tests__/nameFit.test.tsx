/** A name is never only an ellipsis.
 *
 *  The owner's live Needs you (2026-11-13): three of four rows read "…". Their
 *  names began with a long path ("scripts/some_module.py:126-128 keeps …") and
 *  the list's name seat showed a bare ellipsis when the first word did not
 *  fit. */
import { cleanup, render } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { fitName } from "../objects/fitName";
import { MiddleText } from "../MiddleText";
import { Mast } from "../index";

vi.mock("../objects/fitName", async original => ({...await original<object>(), textMeasure: () => ({average: 8, width: (text: string) => text.length * 8})}));
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

const LONG_PATH_FIRST = "scripts/tools/related_modules.py:126-128 keeps parked modules in its graph";
const BACKTICK_FIRST = "`package/db/models/mixins.py::Serializable` is dead; park it";
const fitsIn = (chars: number) => (line: string) => line.length <= chars;

it("cuts a first word that is too long by its letters, then one ellipsis", () => {
  for (const name of [LONG_PATH_FIRST, BACKTICK_FIRST]) {
    const [shown] = fitName(name, 20, 1, fitsIn(20), "end");
    expect(shown.length).toBeGreaterThan(4);
    expect(shown.endsWith("…")).toBe(true);
    expect(name.startsWith(shown.slice(0, -1))).toBe(true);
  }
});

it("keeps whole words when they fit and ends at a word", () => {
  expect(fitName("Review the rollout plan before Friday", 20, 1, fitsIn(20), "end")).toEqual(["Review the rollout…"]);
});

it("is never only an ellipsis, even when no letter fits beside it", () => {
  expect(fitName(LONG_PATH_FIRST, 4, 1, () => false, "end")).toEqual(["s…"]);
});

it("a list name with a long first word shows the start of that word", () => {
  vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(160);
  for (const name of [LONG_PATH_FIRST, BACKTICK_FIRST]) {
    const { container, unmount } = render(<MiddleText value={name} cut="end" />);
    const shown = container.textContent ?? "";
    expect(shown).not.toBe("…");
    expect(shown.length).toBeGreaterThan(4);
    expect(name.startsWith(shown.replace(/…$/, ""))).toBe(true);
    unmount();
  }
});

it("a Mast title with one long word shows the start of that word", () => {
  vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(120);
  const { container } = render(<Mast framed kind="project" title={<span>Payments-ledger-cutover-rehearsal</span>} />);
  const shown = container.querySelector("h2")?.textContent ?? "";
  expect(shown).not.toBe("…");
  expect(shown).toMatch(/^Payments.*…$/);
});

it("breaks identifiers at colon joins before cutting a run of letters", () => {
  expect(fitName("scope:owner:revision",8,3,fitsIn(8),"end")).toEqual(["scope:","owner:","revision"]);
});

it("fits an inspector name into two measured lines and keeps its full accessible name", async () => {
  const { PaneInspector } = await import("../index");
  vi.spyOn(HTMLElement.prototype,"clientWidth","get").mockReturnValue(120);
  const name="relationship_"+"platformarchitecturedecision".repeat(7);
  const {container}=render(<PaneInspector label={name} rows={[]} />);
  const title=container.querySelector("strong")!;
  expect(title.textContent).toMatch(/…$/);
  expect(title.textContent!.split("\n").length).toBeLessThanOrEqual(2);
  expect(title.querySelector('[title]')).toHaveAttribute('title',name);
});


it("cuts receipt paths at joins on both sides of the middle gap", () => {
  const path="~/Documents/Reports/2026-11-13-review-the-architecture-migration-and-keep-the-current-rollback-note-b5c4e405.md";
  const [shown]=fitName(path, 48, 1, fitsIn(48), "path");
  const [head,tail]=shown.split("…");
  expect(path.startsWith(head)).toBe(true);
  expect(path.endsWith(tail)).toBe(true);
  expect(head).toMatch(/[\s_\-./:]$/);
  expect(path[path.length-tail.length-1]).toMatch(/[\s_\-./:]/);
});
