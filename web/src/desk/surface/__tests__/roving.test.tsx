/* HS-200-41 F2 — `useRovingRows` on a list that MOUNTS EMPTY.
 *
 * The keyboard law is kit law: one Tab stop per composite, arrows walk rows.
 * It was silently absent on any list that renders nothing while it is empty
 * and fills from a fetch — which, because A.8 forbids a caption of zero, is
 * most of them. The listener effect read `ref.current` once under deps
 * `[ref, selector, rowSelector]`, all three stable: a null ref on mount
 * returned early and the effect never ran again.
 *
 * It survived every existing test because every existing specimen renders its
 * rows on mount. The glass caught it by listener census, not by eye. These
 * tests mount the way the product does — empty first, rows later.
 */
import { act, fireEvent, render, screen } from "@testing-library/react";
import { useRef, useState } from "react";
import { describe, expect, it } from "vitest";
import { useRovingRows } from "../roving";

/** A list with the shape A.8 forces: NOTHING at all while it is empty. */
function SparseList({ initial = 0 }: { initial?: number }) {
  const [rows, setRows] = useState(initial);
  const rootRef = useRef<HTMLDivElement>(null);
  useRovingRows(rootRef, { selector: ".row button", rowSelector: ".row" });
  return (
    <>
      <button type="button" onClick={() => setRows(3)}>
        load
      </button>
      {rows === 0 ? null : (
        <div ref={rootRef}>
          {Array.from({ length: rows }, (_, i) => (
            <div className="row" key={i}>
              <button type="button">open {i}</button>
              <button type="button">more {i}</button>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

function rowVerbs(): HTMLElement[] {
  return Array.from(document.querySelectorAll<HTMLElement>(".row button"));
}

describe("useRovingRows on a list that mounts empty (HS-200-41 F2)", () => {
  it("attaches once the rows arrive: arrows walk rows", () => {
    render(<SparseList />);
    // Nothing yet — the container itself does not exist.
    expect(rowVerbs()).toHaveLength(0);

    act(() => {
      fireEvent.click(screen.getByRole("button", { name: "load" }));
    });

    const verbs = rowVerbs();
    expect(verbs).toHaveLength(6);
    verbs[0].focus();
    fireEvent.keyDown(verbs[0], { key: "ArrowDown" });
    // Before the fix this asserted nothing moved: zero listeners were bound.
    expect(document.activeElement).toBe(verbs[2]);
    fireEvent.keyDown(verbs[2], { key: "ArrowUp" });
    expect(document.activeElement).toBe(verbs[0]);
  });

  it("Left/Right still walk a row's own controls after a late mount", () => {
    render(<SparseList />);
    act(() => {
      fireEvent.click(screen.getByRole("button", { name: "load" }));
    });
    const verbs = rowVerbs();
    verbs[0].focus();
    fireEvent.keyDown(verbs[0], { key: "ArrowRight" });
    expect(document.activeElement).toBe(verbs[1]);
  });

  it("stamps ONE Tab stop across the late-arriving list", () => {
    render(<SparseList />);
    act(() => {
      fireEvent.click(screen.getByRole("button", { name: "load" }));
    });
    expect(rowVerbs().filter((v) => v.tabIndex === 0)).toHaveLength(1);
  });

  it("still works for a list that had its rows on mount", () => {
    // The path every existing consumer takes; it must not regress.
    render(<SparseList initial={3} />);
    const verbs = rowVerbs();
    verbs[0].focus();
    fireEvent.keyDown(verbs[0], { key: "ArrowDown" });
    expect(document.activeElement).toBe(verbs[2]);
  });

  it("Home and End reach the ends of a late-arriving list", () => {
    render(<SparseList />);
    act(() => {
      fireEvent.click(screen.getByRole("button", { name: "load" }));
    });
    const verbs = rowVerbs();
    verbs[0].focus();
    fireEvent.keyDown(verbs[0], { key: "End" });
    expect(document.activeElement).toBe(verbs[4]);
    fireEvent.keyDown(verbs[4], { key: "Home" });
    expect(document.activeElement).toBe(verbs[0]);
  });
});
