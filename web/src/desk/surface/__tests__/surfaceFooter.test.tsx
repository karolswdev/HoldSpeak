import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SurfaceFooter } from "../SurfaceFooter";
import { Button } from "../../../components/signal/Signal";

describe("SurfaceFooter", () => {
  it("renders three slots", () => {
    const { container } = render(
      <SurfaceFooter
        egress={<span>egress</span>}
        receipt={<span>receipt</span>}
        verbs={<button type="button">Copy</button>}
      />,
    );
    expect(screen.getByText("egress")).toBeTruthy();
    expect(screen.getByText("receipt")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Copy" })).toBeTruthy();
    expect(container.querySelector("footer.surface-footer")).toBeTruthy();
    expect(container.querySelector(".surface-footer-egress")).toBeTruthy();
    expect(container.querySelector(".surface-footer-receipt")).toBeTruthy();
    expect(container.querySelector(".surface-footer-verbs")).toBeTruthy();
  });

  it("collapses gracefully when slots are empty", () => {
    const { container } = render(<SurfaceFooter />);
    const footer = container.querySelector("footer.surface-footer");
    expect(footer).toBeTruthy();
    expect(container.querySelector(".surface-footer-egress")?.textContent).toBe(
      "",
    );
    expect(
      container.querySelector(".surface-footer-receipt")?.textContent,
    ).toBe("");
    expect(container.querySelector(".surface-footer-verbs")?.textContent).toBe(
      "",
    );
  });

  it("renders partial slots without affecting the others", () => {
    const { container } = render(
      <SurfaceFooter receipt={<span>Copied</span>} />,
    );
    expect(screen.getByText("Copied")).toBeTruthy();
    expect(container.querySelector(".surface-footer-egress")?.textContent).toBe(
      "",
    );
    expect(container.querySelector(".surface-footer-verbs")?.textContent).toBe(
      "",
    );
  });

  it("keeps the primary and More actions at phone width", () => {
    vi.stubGlobal("matchMedia", () => ({
      matches: true,
      media: "(max-width: 720px)",
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      onchange: null,
      dispatchEvent: () => false,
    }));
    const copy = vi.fn();
    const custom = vi.fn();
    function CustomAction() {
      return <Button variant="ghost" onClick={custom}>Custom action</Button>;
    }
    render(
      <SurfaceFooter
        verbs={
          <span className="surface-footer-verbs-group">
            <Button variant="primary" onClick={() => {}}>Send</Button>
            <Button variant="ghost" onClick={copy}>Copy</Button>
            <CustomAction />
            <Button type="submit">Submit</Button>
            <span>Material</span>
          </span>
        }
      />,
    );
    expect(screen.getByRole("button", { name: "Send" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "More actions" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Custom action" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Submit" })).toBeTruthy();
    expect(screen.getByText("Material")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "More actions" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Copy" }));
    expect(copy).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: "Custom action" }));
    expect(custom).toHaveBeenCalledOnce();
  });

  // Betterment shell S0 (UX-CANON A.11): More holds only extras that can
  // run; with none, More is not drawn (it opened an empty menu before).
  it("withholds a disabled extra, and More with it, at phone width", () => {
    vi.stubGlobal("matchMedia", () => ({
      matches: true,
      media: "(max-width: 720px)",
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      onchange: null,
      dispatchEvent: () => false,
    }));
    const { rerender } = render(
      <SurfaceFooter
        verbs={
          <span className="surface-footer-verbs-group">
            <Button variant="primary" onClick={() => {}}>Send</Button>
            <Button variant="ghost" disabled onClick={() => {}}>Open</Button>
          </span>
        }
      />,
    );
    expect(screen.getByRole("button", { name: "Send" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "More actions" })).toBeNull();
    rerender(
      <SurfaceFooter
        verbs={
          <span className="surface-footer-verbs-group">
            <Button variant="primary" onClick={() => {}}>Send</Button>
            <Button variant="ghost" disabled onClick={() => {}}>Open</Button>
            <Button variant="ghost" onClick={() => {}}>Copy</Button>
          </span>
        }
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "More actions" }));
    expect(screen.getAllByRole("menuitem").map((row) => row.textContent)).toEqual(["Copy"]);
  });

  afterEach(() => vi.unstubAllGlobals());
});
