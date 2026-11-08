// HS-135-04 — L10 sparse-surface tests: below SPARSE_THRESHOLD filter
// chrome hides, zero-value metric tiles collapse, verbs and empty
// wells ALWAYS remain.
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SPARSE_THRESHOLD } from "../sparse";
import { MetricStrip, SurfaceState, SurfaceVerbs } from "../Surface";

// --------------- constant ---------------

describe("SPARSE_THRESHOLD constant", () => {
  it("is 5", () => {
    expect(SPARSE_THRESHOLD).toBe(5);
  });
});

// --------------- MetricStrip ---------------

describe("MetricStrip sparse gating (L10)", () => {
  it("collapses zero-value tiles below threshold", () => {
    const { container } = render(
      <MetricStrip
        itemCount={2}
        items={[
          { label: "meetings", value: 0 },
          { label: "actions", value: 0 },
          { label: "pending", value: 1 },
        ]}
      />,
    );
    // Only the non-zero tile survives.
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("pending")).toBeInTheDocument();
    expect(screen.queryByText("meetings")).toBeNull();
    expect(screen.queryByText("actions")).toBeNull();
    expect(container.querySelectorAll(".surface-metrics > div")).toHaveLength(1);
  });

  it("renders nothing when ALL values are zero below threshold", () => {
    const { container } = render(
      <MetricStrip
        itemCount={0}
        items={[
          { label: "meetings", value: 0 },
          { label: "actions", value: 0 },
        ]}
      />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("keeps zero-value tiles at or above threshold", () => {
    render(
      <MetricStrip
        itemCount={5}
        items={[
          { label: "meetings", value: 0 },
          { label: "actions", value: 3 },
        ]}
      />,
    );
    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getByText("meetings")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("keeps zero-value tiles when itemCount is omitted (backwards compat)", () => {
    render(
      <MetricStrip
        items={[
          { label: "meetings", value: 0 },
          { label: "actions", value: 3 },
        ]}
      />,
    );
    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getByText("meetings")).toBeInTheDocument();
  });

  it("always omits empty-presenting values regardless of threshold", () => {
    const { container } = render(
      <MetricStrip
        itemCount={10}
        items={[
          { label: "known", value: 5 },
          { label: "unknown", value: "unknown" },
          { label: "empty", value: "" },
        ]}
      />,
    );
    expect(container.querySelectorAll(".surface-metrics > div")).toHaveLength(1);
  });
});

// --------------- Verb bars ALWAYS render (L10 rule 4) ---------------

describe("SurfaceVerbs always render (L10 rule 4)", () => {
  it("renders verb bar even on a sparse surface", () => {
    render(
      <SurfaceVerbs>
        <button type="button">Record meeting</button>
      </SurfaceVerbs>,
    );
    expect(
      screen.getByRole("button", { name: "Record meeting" }),
    ).toBeInTheDocument();
  });
});

// --------------- SurfaceState empty well ALWAYS renders (L10 rule 5) ---------------

describe("SurfaceState empty well always renders (L10 rule 5)", () => {
  it("shows empty well on a surface with zero items", () => {
    render(<SurfaceState empty emptyLabel="No meetings yet" />);
    expect(screen.getByText("No meetings yet")).toBeInTheDocument();
  });

  it("shows empty well with an action verb", () => {
    const onAction = vi.fn();
    render(
      <SurfaceState
        empty
        emptyLabel="No meetings yet"
        onAction={onAction}
        actionLabel="Record meeting"
      />,
    );
    expect(screen.getByText("No meetings yet")).toBeInTheDocument();
    const btn = screen.getByRole("button", { name: "Record meeting" });
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onAction).toHaveBeenCalledTimes(1);
  });
});
