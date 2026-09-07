// HS-200-07 (C4) — the shade carries the same truth as the arrival:
// "Nothing missed" is an all-clear, so it is spoken only over complete
// coverage; an unobserved source shows its repair row instead.
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { SystemShade } from "../SystemShade";

const refresh = vi.fn().mockResolvedValue(undefined);

vi.mock("../../projections", () => ({
  useProjections: () => ({
    projections: [],
    counts: { needs_attention: 0, receipts: 0 },
    refresh,
    present: vi.fn(),
  }),
}));

vi.mock("../../../lib/api", () => ({ apiFetch: vi.fn() }));

const FAILED_ROOM = {
  source_id: "project:beta",
  kind: "project",
  state: "failed",
  observed_at: "2026-09-06T09:00:00",
  label: "Governance",
  project_id: "beta",
  reason: "needsYou_read_failed",
  repair: { token: "READ FAILED", verb: "Retry", href: "/projects/beta" },
};

function wire(needsYou: unknown) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (String(path).startsWith("/api/desk/needs-you")) return needsYou;
    if (String(path).startsWith("/api/dictation/corrections")) return { items: [] };
    return null;
  });
}

describe("SystemShade coverage (HS-200-07 / C4)", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset());

  it("says Nothing missed over a complete empty read", async () => {
    wire({ count: 0, projects: [], items: [], coverage: [], complete: true });
    render(<SystemShade open onClose={vi.fn()} onOpenMemory={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("Nothing missed")).toBeTruthy());
    expect(screen.queryByTestId("shade-coverage")).toBeNull();
  });

  it("shows the coverage section and no all-clear over a partial read", async () => {
    wire({ count: 0, projects: [], items: [], coverage: [FAILED_ROOM], complete: false });
    render(<SystemShade open onClose={vi.fn()} onOpenMemory={vi.fn()} />);

    await waitFor(() => expect(screen.getByTestId("shade-coverage")).toBeTruthy());
    expect(screen.queryByText("Nothing missed")).toBeNull();
    expect(screen.getByTestId("shade-coverage-row").textContent).toContain("Governance");
    expect(screen.getByTestId("shade-coverage-row").textContent).toContain("READ FAILED");
    expect(screen.getByTestId("shade-coverage-row").textContent).toContain("LAST SEEN");
    const verb = screen.getByTestId("shade-coverage-verb");
    expect(verb.textContent).toBe("Open source");
    expect(verb.className).toContain("btn");
  });

  it("counts the observed sources honestly in the caption", async () => {
    wire({
      count: 0, projects: [], items: [],
      coverage: [
        { ...FAILED_ROOM },
        { source_id: "project:alpha", kind: "project", state: "available",
          observed_at: "2026-09-06T09:30:00", label: "Q4 Platform",
          project_id: "alpha", reason: null, repair: null },
      ],
      complete: false,
    });
    render(<SystemShade open onClose={vi.fn()} onOpenMemory={vi.fn()} />);

    await waitFor(() => expect(screen.getByTestId("shade-coverage")).toBeTruthy());
    expect(screen.getByTestId("shade-coverage").textContent).toContain("1 of 2");
  });
});
