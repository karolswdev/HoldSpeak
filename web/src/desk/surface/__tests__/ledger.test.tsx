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
});
