// HS-167-03 — SurfaceVerbs active prop vitest.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SurfaceVerbs } from "../Surface";

describe("SurfaceVerbs active prop", () => {
  it("stamps data-active-verb on the verb bar", () => {
    const { container } = render(
      <SurfaceVerbs active="Steward">
        <button type="button" aria-current="true">Steward</button>
        <button type="button">Review</button>
      </SurfaceVerbs>,
    );
    const bar = container.querySelector(".surface-verbs");
    expect(bar?.getAttribute("data-active-verb")).toBe("Steward");
  });

  it("does not stamp data-active-verb when active is absent", () => {
    const { container } = render(
      <SurfaceVerbs>
        <button type="button">Run</button>
      </SurfaceVerbs>,
    );
    const bar = container.querySelector(".surface-verbs");
    expect(bar?.hasAttribute("data-active-verb")).toBe(false);
  });

  it("buttons with aria-current='true' can carry a count chip", () => {
    render(
      <SurfaceVerbs active="Review">
        <button type="button" aria-current="true">
          Review <span className="surface-verb-count">3</span>
        </button>
        <button type="button">Updates</button>
        <button type="button">Steward</button>
      </SurfaceVerbs>,
    );
    expect(screen.getByText("3")).toHaveClass("surface-verb-count");
    expect(screen.getByText("3").closest("button")).toHaveAttribute(
      "aria-current",
      "true",
    );
  });

  it("existing callers without active are unchanged", () => {
    const { container } = render(
      <SurfaceVerbs status={<span>status-chip</span>}>
        <button type="button">Run</button>
      </SurfaceVerbs>,
    );
    expect(screen.getByText("status-chip")).toBeInTheDocument();
    expect(screen.getByText("Run")).toBeInTheDocument();
    expect(container.querySelector(".surface-verbs")?.hasAttribute("data-active-verb")).toBe(false);
  });
});
