import { createRef } from "react";
import { render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const mermaid = vi.hoisted(() => ({
  initialize: vi.fn(),
  render: vi.fn(async (_id: string, text: string) => {
    if (text.includes("broken")) throw new Error("Parse error on line 2:\nmore detail");
    return { svg: '<svg data-testid="drawn-diagram" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>' };
  }),
}));
vi.mock("mermaid", () => ({ default: mermaid }));

import { DeskEditor, type DeskEditorHandle } from "../components/DeskEditor";
import { mermaidPreview, resetMermaidPreview } from "./mermaidPreview";

const extensions = mermaidPreview();
const FENCE = "```mermaid\nflowchart LR\n  A --> B\n```";
const BODY = `Plan for the week.\n\n${FENCE}\n\nThe end.`;

function mount(value: string) {
  const ref = createRef<DeskEditorHandle>();
  const view = render(<DeskEditor ref={ref} value={value} onChange={() => {}} showToolbar={false} extensions={extensions} />);
  return { ref, ...view };
}

describe("the Note draws its mermaid fences in place", () => {
  afterEach(() => {
    resetMermaidPreview();
    mermaid.render.mockClear();
    mermaid.initialize.mockClear();
  });

  it("shows the drawn diagram while the caret is outside the fence, and the source when it enters", async () => {
    const { ref, container } = mount(BODY);

    await waitFor(() => expect(container.querySelector('[data-testid="note-mermaid"][data-state="drawn"]')).not.toBeNull());
    expect(container.querySelector('[data-testid="drawn-diagram"]')).not.toBeNull();
    expect(container.querySelector(".cm-content")?.textContent).not.toContain("flowchart LR");
    expect(mermaid.initialize).toHaveBeenCalledWith(expect.objectContaining({ securityLevel: "strict", theme: "base" }));

    const inside = BODY.indexOf("A --> B");
    ref.current!.restoreSelection(inside, inside, { focus: false });

    await waitFor(() => expect(container.querySelector('[data-testid="note-mermaid"]')).toBeNull());
    expect(container.querySelector(".cm-content")?.textContent).toContain("flowchart LR");

    ref.current!.restoreSelection(0, 0, { focus: false });
    await waitFor(() => expect(container.querySelector('[data-testid="note-mermaid"][data-state="drawn"]')).not.toBeNull());
    // One render per source: the second showing reads the drawn copy.
    expect(mermaid.render).toHaveBeenCalledTimes(1);
  });

  it("a diagram that does not render shows its source and one quiet line", async () => {
    const errors = vi.spyOn(console, "error");
    const { container } = mount(`Intro\n\n\`\`\`mermaid\nflowchart LR\n  broken -->\n\`\`\``);

    await waitFor(() => expect(container.querySelector('[data-testid="note-mermaid"][data-state="failed"]')).not.toBeNull());
    expect(container.querySelector(".cm-mermaid-source")?.textContent).toContain("broken -->");
    expect(container.querySelector(".cm-mermaid-error")?.textContent).toBe("Diagram did not render: Parse error on line 2:");
    expect(errors).not.toHaveBeenCalled();
    errors.mockRestore();
  });

  it("a note without a diagram never loads mermaid", async () => {
    const { container } = mount("Just words.\n\n```js\nconst a = 1;\n```");
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(container.querySelector('[data-testid="note-mermaid"]')).toBeNull();
    expect(mermaid.initialize).not.toHaveBeenCalled();
  });
});
