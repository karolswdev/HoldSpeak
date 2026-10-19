/* HS-202-04 — the Speak gear door counts nothing to zero (UX-CANON A.8).
 *
 * `01-measured-walk.md`, leg `door-speak` (Speak → the gear door,
 * "Configure dictation"), all four desk/width legs: `U3 "0 (beside
 * 'runs')"`. The face printed `Runs 0` on a machine that had never run the
 * pipeline. A.8: "omit the zero token or say the true thing".
 *
 * The rig's selector points into `FoldGadget`'s body, where the readiness
 * WIRE is shown verbatim. A raw fold that edits the wire is a lie, so the
 * wire stays as the hub sent it and the fold now declares itself RAW (the
 * owner's ruling: debug hides behind RAW). The FACE row is what this fence
 * governs.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), open: vi.fn() }));
vi.mock("../../../../desk/shell", () => ({ openSurfaceOr: mocks.open }));

vi.mock("../../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) =>
    error instanceof Error ? error.message : "Request failed",
}));

import { Readiness } from "../Readiness";
import { useBuilderTools } from "../../../../desk/builderTools";

const readiness = (runs: number) => ({
  config: { pipeline_enabled: true, backend: "mlx", max_total_latency_ms: 900 },
  target: { label: "Codex CLI", confidence: 0.9 },
  depth: { runs },
  warnings: [],
});

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  // Betterment C8: the raw fold is behind RAW (Builder tools), on here.
  useBuilderTools.getState().setOn(true);
});

describe("the gear door's Runs fact (A.8)", () => {
  it("names a missing model and opens the dictation engine choice; raw paths fold", async () => {
    const raw = "Model file missing: /temporary/artifact/hash/model.gguf";
    mocks.apiFetch.mockResolvedValue({ ...readiness(0), warnings: [{ code: "runtime_model_missing", message: raw }] });
    render(<Readiness />);
    expect(await screen.findByText("Model missing")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Choose engine" }));
    expect(mocks.open).toHaveBeenCalledWith("open-concierge", "/models", "writing_dictation");
    expect(screen.queryByText(raw)).toBeNull();
    const rawFold = screen.getByText("RAW · READINESS").closest("details")!;
    expect(rawFold.open).toBe(false);
    fireEvent.click(rawFold.querySelector("summary")!);
    expect(rawFold.textContent).toContain(raw);
  });
  it("withholds the row when the pipeline has never run", async () => {
    mocks.apiFetch.mockResolvedValue(readiness(0));
    render(<Readiness />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());
    await screen.findByText("Delivery");
    const rows = [...document.querySelectorAll(".gadget-row-label")].map(
      (label) => label.textContent ?? "",
    );
    expect(rows).toContain("Delivery target");
    expect(rows).not.toContain("Runs");
  });

  it("draws the row once there is a run to count", async () => {
    mocks.apiFetch.mockResolvedValue(readiness(3));
    render(<Readiness />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());
    expect(await screen.findByText("Runs")).toBeInTheDocument();
    const row = screen.getByText("Runs").closest(".gadget-row");
    expect(row?.textContent).toContain("3");
  });

  it("RAW off: the raw readiness fold is not on the face (betterment C8)", async () => {
    useBuilderTools.getState().setOn(false);
    mocks.apiFetch.mockResolvedValue(readiness(0));
    render(<Readiness />);
    await screen.findByText("Delivery");
    expect(screen.queryByText("RAW · READINESS")).toBeNull();
  });

  it("keeps the readiness wire behind a fold that says it is raw", async () => {
    mocks.apiFetch.mockResolvedValue(readiness(0));
    render(<Readiness />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());
    expect(await screen.findByText("RAW · READINESS")).toBeInTheDocument();
  });
});
