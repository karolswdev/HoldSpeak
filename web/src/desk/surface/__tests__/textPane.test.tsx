// PG-LANG §11: the TextPane species (a line editor with a gutter of line lamps).
import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import { TextPane, lineMarks, paintLine, type TextPaneLine } from "../TextPane";

const KEYWORDS = ["program", "step", "owns", "after", "merge", "brief", "every step"];

function Host({ start, seen }: { start: TextPaneLine[]; seen?: (lines: TextPaneLine[]) => void }) {
  const [lines, setLines] = useState(start);
  return <TextPane label="Program text" lines={lines} keywords={KEYWORDS} onChange={(next) => { setLines(next); seen?.(next); }} />;
}

const LINES: TextPaneLine[] = [
  { text: "# program text 1", readOnly: true },
  { text: "program The hub stops stalling", lamp: "Running · 0 of 3 done", tone: "info" },
  { text: "  > Every route under 100 ms." },
  { text: "step 3 The fan-out", lamp: "Planned", tone: "idle" },
  { text: "  after 1, 2" },
];

describe("TextPane", () => {
  it("draws each line with its number, its lamp dot and its lamp words at the line end; the lamp is never in the line's value", () => {
    render(<Host start={LINES} />);
    const rows = screen.getAllByTestId("kit-textpane-line");
    expect(rows).toHaveLength(5);
    const head = rows[1];
    expect(head.querySelector(".kit-textpane-n")?.textContent).toBe("2");
    expect(head.querySelector(".kit-textpane-lampdot .kit-dot")?.getAttribute("data-tone")).toBe("info");
    expect(head.querySelector(".kit-textpane-lamp")?.textContent).toBe("Running · 0 of 3 done");
    const input = screen.getByRole("textbox", { name: "Program text, line 2" }) as HTMLTextAreaElement;
    expect(input.value).toBe("program The hub stops stalling");
    expect(input.value).not.toContain("#");
  });

  it("a read-only line is drawn and not edited; his > line is in the body face; keywords and ids are painted", () => {
    render(<Host start={LINES} />);
    expect(screen.queryByRole("textbox", { name: "Program text, line 1" })).toBeNull();
    const rows = screen.getAllByTestId("kit-textpane-line");
    expect(rows[0]).toHaveAttribute("data-readonly");
    expect(rows[2]).toHaveAttribute("data-words");
    expect(rows[3].querySelector(".kit-textpane-keyword")?.textContent).toBe("step");
    const { container } = render(<>{paintLine("  R3 check: `echo` · merge owner", ["merge"])}</>);
    expect(container.querySelector(".kit-textpane-id")?.textContent).toBe("R3");
    expect(container.querySelector(".kit-textpane-keyword")?.textContent).toBe("merge");
    expect(container.textContent).toBe("  R3 check: `echo` · merge owner");
  });

  it("typing changes one line; Return splits it and carries the indent; Backspace at the start joins it back", () => {
    let last: TextPaneLine[] = [];
    render(<Host start={LINES} seen={(next) => { last = next; }} />);
    const after = screen.getByRole("textbox", { name: "Program text, line 5" }) as HTMLTextAreaElement;
    fireEvent.change(after, { target: { value: "  after 1, 2, 4" } });
    expect(last[4].text).toBe("  after 1, 2, 4");
    after.setSelectionRange(after.value.length, after.value.length);
    fireEvent.keyDown(after, { key: "Enter" });
    expect(last.map((line) => line.text).slice(4)).toEqual(["  after 1, 2, 4", "  "]);
    const fresh = screen.getByRole("textbox", { name: "Program text, line 6" }) as HTMLTextAreaElement;
    expect(document.activeElement).toBe(fresh);
    fireEvent.change(fresh, { target: { value: "  merge owner" } });
    fresh.setSelectionRange(0, 0);
    fireEvent.keyDown(fresh, { key: "Backspace" });
    expect(last).toHaveLength(5);
    expect(last[4].text).toBe("  after 1, 2, 4  merge owner");
  });

  it("a split keeps the lamp on the upper line; Backspace never joins into a read-only line", () => {
    let last: TextPaneLine[] = [];
    render(<Host start={LINES} seen={(next) => { last = next; }} />);
    const head = screen.getByRole("textbox", { name: "Program text, line 2" }) as HTMLTextAreaElement;
    head.setSelectionRange(0, 0);
    fireEvent.keyDown(head, { key: "Backspace" });
    expect(last).toEqual([]);
    head.setSelectionRange(7, 7);
    fireEvent.keyDown(head, { key: "Enter" });
    expect(last[1]).toMatchObject({ text: "program", lamp: "Running · 0 of 3 done", tone: "info" });
    expect(last[2].lamp).toBeUndefined();
  });

  it("the gutter marks follow a line diff: changed, added, removed above", () => {
    expect(lineMarks(["a", "b", "c"], ["a", "B", "c"])).toEqual([undefined, "~", undefined]);
    expect(lineMarks(["a", "b"], ["a", "x", "b"])).toEqual([undefined, "+", undefined]);
    expect(lineMarks(["a", "b", "c"], ["a", "c"])).toEqual([undefined, "-"]);
    render(<TextPane label="Program text" lines={[{ text: "a" }, { text: "B", mark: "~" }, { text: "c", mark: "!", title: "Line 3: refused" }]} onChange={() => undefined} />);
    const rows = screen.getAllByTestId("kit-textpane-line");
    expect(rows[1]).toHaveAttribute("data-mark", "~");
    expect(rows[2]).toHaveAttribute("title", "Line 3: refused");
  });

  it("carries the mic (the voice law): one MicButton named for the pane", () => {
    render(<Host start={LINES} />);
    expect(screen.getByRole("button", { name: /speak into program text/i })).toBeInTheDocument();
  });
});
