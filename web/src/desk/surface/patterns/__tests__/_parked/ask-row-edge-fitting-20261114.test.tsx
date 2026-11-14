// Parked: Ask no longer changes row-edge policy; ObjectList wholeRows and main's form fitter own it.
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { SurfaceWell } from "../../../index";
afterEach(() => {cleanup(); vi.restoreAllMocks();});

it.each([40, 40.75])("paints complete %s-pixel form rows while keeping the full field scroll range", async (rowHeight) => {
  const { InspectorForm } = await import("../../../index");
  vi.spyOn(HTMLElement.prototype,"clientHeight","get").mockReturnValue(115);
  vi.spyOn(HTMLElement.prototype,"getBoundingClientRect").mockImplementation(function(this:HTMLElement) {
    if (this.classList.contains("surface-inspector-fields")) return new DOMRect(0,0,240,75);
    if (this.classList.contains("gadget-row")) return new DOMRect(0,this.textContent?.includes("Second")?rowHeight:0,240,rowHeight);
    if (this.classList.contains("surface-inspector-actions")) return new DOMRect(0,75,240,40);
    return new DOMRect(0,0,240,120);
  });
  const {container}=render(<InspectorForm wholeRows rows={[{label:"First",control:"First value"},{label:"Second",control:"Second value"}]} completion={{cancel:()=>{},primary:{label:"Save",run:()=>{}}}} />);
  const fields=container.querySelector<HTMLElement>(".surface-inspector-fields")!;
  expect(parseFloat(fields.style.maxHeight)).toBe(rowHeight);
  expect(fields.style.clipPath).not.toBe("");
  const bottom=75-parseFloat(fields.style.clipPath.split(" ")[2]);
  for (const row of fields.querySelectorAll(".gadget-row")) {
    const rect=row.getBoundingClientRect();
    expect(rect.top>=bottom || rect.bottom<=bottom).toBe(true);
  }
  expect(fields).toHaveTextContent("Second value");
  expect(screen.getByRole("button",{name:"Save"})).toBeVisible();
});

it.each([30, 30.75])("a reading well keeps an embedded selection row of %s pixels whole and reachable", rowHeight => {
  let scroll = 0;
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function(this: HTMLElement) {
    if (this.classList.contains("object-list-row")) return new DOMRect(0,(this.textContent === "First claim" ? 0 : rowHeight)-scroll,300,rowHeight);
    return new DOMRect(0,0,300,45);
  });
  vi.spyOn(document, "createRange").mockImplementation(() => ({selectNodeContents:()=>{},getClientRects:()=>[new DOMRect(0,-scroll,300,16),new DOMRect(0,36-scroll,300,16)]}) as unknown as Range);
  const {container}=render(<SurfaceWell wholeLines><div className="object-list-row">First claim</div><div className="object-list-row">Second claim</div></SurfaceWell>);
  const well=container.querySelector<HTMLElement>(".surface-well-body")!;
  const [first,second]=container.querySelectorAll(".object-list-row");
  const bottom=45-parseFloat(well.style.clipPath.split(" ")[2]);
  expect(bottom).toBeGreaterThanOrEqual(first.getBoundingClientRect().bottom);
  expect(bottom).toBeLessThanOrEqual(second.getBoundingClientRect().top);
  scroll=rowHeight; fireEvent.scroll(well);
  expect(well.style.clipPath).toBe("");
  expect(second.getBoundingClientRect().top).toBeGreaterThanOrEqual(0);
  expect(second.getBoundingClientRect().bottom).toBeLessThanOrEqual(45);
  expect(well).toHaveTextContent("Second claim");
});
