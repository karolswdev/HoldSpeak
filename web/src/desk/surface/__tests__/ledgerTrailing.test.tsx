// HS-167-03 — SurfaceLedgerRow trailing + wrap vitest.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SurfaceLedger, SurfaceLedgerRow } from "../Surface";

describe("SurfaceLedgerRow trailing prop", () => {
  it("renders a trailing slot after cells", () => {
    render(
      <SurfaceLedger count="ITEMS 2">
        <SurfaceLedgerRow
          primary="Deploy pipeline"
          cells={<span className="surface-ledger-cell">12m</span>}
          trailing={<span data-testid="trailing-chevron">{"▸"}</span>}
        />
      </SurfaceLedger>,
    );
    expect(screen.getByTestId("trailing-chevron")).toBeInTheDocument();
    const line = screen.getByRole("button");
    expect(line).toHaveAttribute("data-has-trailing", "true");
  });

  it("does not render the trailing slot when absent", () => {
    const { container } = render(
      <SurfaceLedger count="ITEMS 1">
        <SurfaceLedgerRow primary="Plain row" />
      </SurfaceLedger>,
    );
    expect(container.querySelector(".surface-ledger-trailing")).toBeNull();
    const line = container.querySelector(".surface-ledger-line");
    expect(line?.hasAttribute("data-has-trailing")).toBe(false);
  });

  it("existing callers without trailing are unchanged", () => {
    const { container } = render(
      <SurfaceLedger count="ITEMS 1">
        <SurfaceLedgerRow
          primary="Legacy row"
          time="09:15"
          cells={<span className="surface-ledger-cell">dest</span>}
        />
      </SurfaceLedger>,
    );
    expect(screen.getByText("Legacy row")).toBeInTheDocument();
    expect(screen.getByText("09:15")).toBeInTheDocument();
    expect(container.querySelector(".surface-ledger-trailing")).toBeNull();
  });
});

describe("SurfaceLedgerRow wrap prop", () => {
  it("stamps data-wrap on the row when wrap=true", () => {
    const { container } = render(
      <SurfaceLedger count="ITEMS 1">
        <SurfaceLedgerRow primary="A long primary that should wrap" wrap />
      </SurfaceLedger>,
    );
    const row = container.querySelector(".surface-ledger-row");
    expect(row?.hasAttribute("data-wrap")).toBe(true);
  });

  it("does not stamp data-wrap when wrap is absent", () => {
    const { container } = render(
      <SurfaceLedger count="ITEMS 1">
        <SurfaceLedgerRow primary="Normal row" />
      </SurfaceLedger>,
    );
    const row = container.querySelector(".surface-ledger-row");
    expect(row?.hasAttribute("data-wrap")).toBe(false);
  });
});
