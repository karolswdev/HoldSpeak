// HS-111-03 — SurfaceWell: the sunken scrolling inset (audit §3.2).
// The head is a mono token line; the body carries the record's tape.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SurfaceWell } from "../Surface";

describe("SurfaceWell (the sunken inset)", () => {
  it("renders the head token and the body inside the well", () => {
    const { container } = render(
      <SurfaceWell head="TRANSCRIPT · 4 SEG">
        <ol className="transcript-list">
          <li>hello</li>
        </ol>
      </SurfaceWell>,
    );
    expect(screen.getByText("TRANSCRIPT · 4 SEG")).toBeInTheDocument();
    const well = container.querySelector(".surface-well");
    expect(well).not.toBeNull();
    expect(well?.querySelector(".surface-well-body .transcript-list")).not.toBeNull();
  });

  it("omits the head slot when no token is given", () => {
    const { container } = render(<SurfaceWell>body</SurfaceWell>);
    expect(container.querySelector(".surface-well-head")).toBeNull();
  });
});
