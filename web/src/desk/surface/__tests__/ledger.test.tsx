// HS-111-02 — the machine ledger (SurfaceLedger): one-line mono rows,
// a token head, and the open-in-place cursor line. SurfaceStream stays
// the said-text composition; this is the machine-rows one.
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SurfaceLedger, SurfaceLedgerRow } from "../Surface";

describe("the machine ledger", () => {
  it("head leads with the token line and carries controls", () => {
    render(
      <SurfaceLedger
        count="Today 2 · Taught 1"
        controls={<button type="button">Clear</button>}
      >
        <ul />
      </SurfaceLedger>,
    );
    expect(screen.getByText("Today 2 · Taught 1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Clear" })).toBeInTheDocument();
  });

  it("a row is one press target; open renders the expansion in place", () => {
    const onToggle = vi.fn();
    const { rerender } = render(
      <ul>
        <SurfaceLedgerRow
          time="09:38"
          primary="ship the native innards brief"
          onToggle={onToggle}
          cells={<span className="surface-ledger-cell">→ claude_code</span>}
        >
          <span>expansion</span>
        </SurfaceLedgerRow>
      </ul>,
    );
    const line = screen.getByRole("button", { expanded: false });
    expect(line).toHaveTextContent("09:38");
    expect(line).toHaveTextContent("ship the native innards brief");
    expect(line).toHaveTextContent("→ claude_code");
    expect(screen.queryByText("expansion")).toBeNull();
    fireEvent.click(line);
    expect(onToggle).toHaveBeenCalled();
    rerender(
      <ul>
        <SurfaceLedgerRow
          time="09:38"
          primary="ship the native innards brief"
          open
          onToggle={onToggle}
        >
          <span>expansion</span>
        </SurfaceLedgerRow>
      </ul>,
    );
    expect(screen.getByRole("button", { expanded: true })).toBeInTheDocument();
    expect(screen.getByText("expansion")).toBeInTheDocument();
  });

  // HS-111-08 — roving focus is kit law (audit §3.1): ONE Tab stop,
  // arrows walk, Home/End jump, letters seek, editors are untouched.
  const ledgerFixture = (children?: import("react").ReactNode) => (
    <SurfaceLedger count="3 ROWS">
      <ul>
        <SurfaceLedgerRow primary="alpha entry" expands={false} />
        <SurfaceLedgerRow primary="beta entry" expands={false} />
        <SurfaceLedgerRow primary="gamma entry" expands={false}>
          {children}
        </SurfaceLedgerRow>
      </ul>
    </SurfaceLedger>
  );

  it("roving tabindex: one Tab stop, ArrowDown/Up walk, no wrap", () => {
    render(ledgerFixture());
    const rows = screen.getAllByRole("button");
    expect(rows.map((row) => row.tabIndex)).toEqual([0, -1, -1]);
    rows[0].focus();
    fireEvent.keyDown(rows[0], { key: "ArrowDown" });
    expect(rows[1]).toHaveFocus();
    expect(rows.map((row) => row.tabIndex)).toEqual([-1, 0, -1]);
    fireEvent.keyDown(rows[1], { key: "ArrowUp" });
    expect(rows[0]).toHaveFocus();
    // No wrap: ArrowUp at the first row stays put (Home/End exist).
    fireEvent.keyDown(rows[0], { key: "ArrowUp" });
    expect(rows[0]).toHaveFocus();
  });

  it("Home/End jump and first-letter type-ahead seeks the row", () => {
    render(ledgerFixture());
    const rows = screen.getAllByRole("button");
    rows[0].focus();
    fireEvent.keyDown(rows[0], { key: "End" });
    expect(rows[2]).toHaveFocus();
    fireEvent.keyDown(rows[2], { key: "Home" });
    expect(rows[0]).toHaveFocus();
    fireEvent.keyDown(rows[0], { key: "b" });
    expect(rows[1]).toHaveFocus();
  });

  it("typing in an open row's editor never moves the rover", () => {
    render(
      <SurfaceLedger count="OPEN ROW">
        <ul>
          <SurfaceLedgerRow primary="alpha entry" expands={false} />
          <SurfaceLedgerRow primary="beta entry" open>
            <input aria-label="Editor" />
          </SurfaceLedgerRow>
        </ul>
      </SurfaceLedger>,
    );
    const editor = screen.getByRole("textbox", { name: "Editor" });
    editor.focus();
    fireEvent.keyDown(editor, { key: "ArrowDown" });
    expect(editor).toHaveFocus();
  });
});
