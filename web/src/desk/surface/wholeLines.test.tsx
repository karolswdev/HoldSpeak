import { useRef } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render } from "@testing-library/react";
import { useWholeLines } from "./wholeLines";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

function Well() {
  const ref = useRef<HTMLDivElement | null>(null);
  useWholeLines(ref);
  return <div ref={ref} data-testid="well"><span>Architecture reviewer</span><p>Keep the selected source in view.</p></div>;
}

it("moves the top edge past a neighbour box on the same visual line", () => {
  // A small speaker name is cut by the well's top edge; the larger words beside
  // it start inside the tolerance, so the first edge (the name's bottom) would
  // land inside the words and cut them. The edge moves to the words' bottom.
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue(new DOMRect(0, 0, 300, 200));
  const boxes = [[new DOMRect(0, -3, 80, 16)], [new DOMRect(90, -0.27, 200, 17), new DOMRect(90, 22, 200, 17)]];
  let turn = 0;
  vi.spyOn(document, "createRange").mockImplementation(() => ({ selectNodeContents: () => {}, getClientRects: () => boxes[turn++ % boxes.length] }) as unknown as Range);
  const { getByTestId } = render(<Well />);
  const top = parseFloat(getByTestId("well").style.clipPath.match(/inset\(([^ )]+)/)?.[1] ?? "0");
  expect(top).toBeGreaterThanOrEqual(16.73);
  expect(top).toBeLessThan(22);
});
