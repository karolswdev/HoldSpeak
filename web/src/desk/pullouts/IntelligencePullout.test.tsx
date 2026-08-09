import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { IntelligencePullout } from "./IntelligencePullout";
import { PULLOUT_CONTENT } from "./registry";

const object = {
  kind: "intelligence" as const,
  id: "desk",
  title: "Intelligence",
  ref: { kind: "intelligence" as const, id: "desk", name: "Intelligence" },
};

describe("HS-128-01 Intelligence pullout", () => {
  beforeEach(() => localStorage.clear());

  it("registers the Intelligence primitive in the pullout registry", () => {
    expect(PULLOUT_CONTENT.intelligence).toBe(IntelligencePullout);
  });

  it("opens on Brief and changes the active view", () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(screen.getByRole("button", { name: "Brief" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    fireEvent.click(screen.getByRole("button", { name: "Follow-through" }));

    expect(
      screen.getByRole("button", { name: "Follow-through" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("restores the last selected view after reopening", () => {
    const first = render(
      <IntelligencePullout object={object} onClose={() => {}} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Receipts" }));
    first.unmount();

    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(
      screen.getByRole("searchbox", { name: "Search decision receipts" }),
    ).toBeInTheDocument();
  });

  it("keeps Brief and Receipts inside a card-width pullout", () => {
    const css = readFileSync(resolve(process.cwd(), "src/desk/pullouts/intelligence.css"), "utf8");

    expect(css).toContain(`.intelligence-view.intelligence-brief {
  display: block;
  container-type: inline-size;
  min-width: 0;
  min-height: 0;
  /* The 100%-wide brief owns padding inside its resizeable body. */
  box-sizing: border-box;`);
    expect(css).toContain(`.intelligence-brief-headline {
  width: 100%;
  min-width: 0;`);
    expect(css).toContain(`.receipts-view > *,
.receipt-detail > *,
.receipts-view .surface-ledger,
.receipts-view .surface-ledger-row,
.receipts-view .surface-ledger-line {
  min-width: 0;
  max-width: 100%;
}`);
    expect(css).toContain(`.intelligence-brief-group .intelligence-brief-rows,
.intelligence-brief-group .surface-ledger-row,
.intelligence-brief-group .surface-ledger-line {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}`);
  });
});
