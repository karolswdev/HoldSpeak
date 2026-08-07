import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SurfaceFooter } from "../SurfaceFooter";

describe("SurfaceFooter", () => {
  it("renders three slots", () => {
    const { container } = render(
      <SurfaceFooter
        egress={<span>egress</span>}
        receipt={<span>receipt</span>}
        verbs={<button type="button">Copy</button>}
      />,
    );
    expect(screen.getByText("egress")).toBeInTheDocument();
    expect(screen.getByText("receipt")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy" })).toBeInTheDocument();
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
    expect(screen.getByText("Copied")).toBeInTheDocument();
    expect(container.querySelector(".surface-footer-egress")?.textContent).toBe(
      "",
    );
    expect(container.querySelector(".surface-footer-verbs")?.textContent).toBe(
      "",
    );
  });
});
