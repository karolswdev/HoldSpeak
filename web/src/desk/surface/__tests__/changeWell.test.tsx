// PG-LANG §11: the DiffRow species and the ChangeWell pattern.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Button } from "../../../components/signal/Signal";
import { ChangeWell } from "../ChangeWell";
import { DiffRow } from "../DiffRow";

describe("DiffRow", () => {
  it("an allowed change: the op glyph, where · field, before → after in mono, the verdict as a DotWord", () => {
    render(<ul><DiffRow op="change" where="step 3" field="merge" before="level" after="owner" verdict="allowed" /></ul>);
    const row = screen.getByRole("listitem");
    expect(row).toHaveAttribute("data-op", "change");
    expect(within(row).getByLabelText("Change").textContent).toBe("~");
    expect(row.querySelector(".kit-diffrow-where")?.textContent).toBe("step 3 · merge");
    expect([...row.querySelectorAll("code")].map((node) => node.textContent)).toEqual(["level", "owner"]);
    expect(screen.getByTestId("kit-diffrow-verdict").textContent).toBe("Allowed");
    expect(screen.getByTestId("kit-diffrow-verdict").querySelector(".kit-dot")?.getAttribute("data-tone")).toBe("ok");
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("a refused change says its line and its reason under the row; it has no verb", () => {
    render(<ul><DiffRow op="change" where="step 2" field="brief" before="a" after="b" verdict="refused" line={19}
      reason="Step 2 · brief: The agent has read it. Add a line with + instead." /></ul>);
    expect(screen.getByTestId("kit-diffrow-verdict").textContent).toBe("Refused");
    expect(screen.getByTestId("kit-diffrow-reason").textContent).toBe("Line 19Step 2 · brief: The agent has read it. Add a line with + instead.");
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("a row that lowers the bar has its own Apply this; the press flips it to Allowed by you", () => {
    const press = vi.fn();
    const { rerender } = render(<ul><DiffRow op="change" where="program" field="control" before="normal" after="yolo" verdict="lowers" onPress={press} /></ul>);
    expect(screen.getByTestId("kit-diffrow-verdict").textContent).toBe("Lowers the bar");
    const verb = screen.getByRole("button", { name: "Apply this" });
    expect(verb.className).toContain("btn");
    expect(verb).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(verb);
    expect(press).toHaveBeenCalledWith(true);
    rerender(<ul><DiffRow op="change" where="program" field="control" before="normal" after="yolo" verdict="lowers" pressed onPress={press} /></ul>);
    expect(screen.getByTestId("kit-diffrow-verdict").textContent).toBe("Allowed by you");
    expect(screen.getByRole("button", { name: "Undo" })).toHaveAttribute("aria-pressed", "true");
  });

  it("a conflict reads Changed since you read it", () => {
    render(<ul><DiffRow op="change" where="step 4" field="agent" before="Claude Code" after="Codex" verdict="conflict"
      reason="Step 4's agent changed since you read it: now Codex." /></ul>);
    expect(screen.getByTestId("kit-diffrow-verdict").textContent).toBe("Changed since you read it");
  });
});

describe("ChangeWell", () => {
  it("a named inset: the head and its fact, the rows, the verbs and a failure line", () => {
    render(
      <ChangeWell head="Changes from the text" fact="2 changes · 1 refused" failure={{ words: "The change was not applied", title: "500" }}
        verbs={<Button dense variant="primary">Apply 1</Button>}>
        <DiffRow op="add" where="step 4" after="The loop watch" verdict="allowed" />
        <DiffRow op="change" where="step 2" field="brief" before="a" after="b" verdict="refused" reason="It is read." />
      </ChangeWell>,
    );
    const well = screen.getByRole("region", { name: "Proposed change" });
    expect(within(well).getByText("Changes from the text")).toBeInTheDocument();
    expect(within(well).getByText("2 changes · 1 refused")).toBeInTheDocument();
    expect(within(well).getAllByRole("listitem")).toHaveLength(2);
    expect(within(well).getByRole("button", { name: "Apply 1" })).toBeInTheDocument();
    expect(screen.getByTestId("kit-changewell-failure")).toHaveAttribute("title", "500");
  });

  it("settling marks the well for its closing motion", () => {
    render(<ChangeWell head="x" verbs={null} settling><DiffRow op="add" where="step 1" after="A" verdict="allowed" /></ChangeWell>);
    expect(screen.getByRole("region")).toHaveAttribute("data-settling");
  });
});
