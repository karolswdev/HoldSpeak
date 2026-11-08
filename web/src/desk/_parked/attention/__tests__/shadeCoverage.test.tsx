// HS-200-07 (C4) — the shade carries the same truth as the arrival:
// "Nothing missed" is an all-clear, so it is spoken only over complete
// coverage; an unobserved source shows its repair row instead.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { SystemShade } from "../SystemShade";
import { recordedGet, type Gets } from "../../../test/recordedHub";
import { AttentionDrawer } from "../AttentionDrawer";
import { activateLauncher } from "../window/launcherRegistry";
import recorded from "../../__tests__/fixtures/needsYou.recorded.json";

const shell = vi.hoisted(() => ({ openSurfaceOr: vi.fn() }));
vi.mock("../../shell", async (original) => ({
  ...(await original<typeof import("../../shell")>()),
  openSurfaceOr: shell.openSurfaceOr,
}));

const refresh = vi.fn().mockResolvedValue(undefined);

vi.mock("../../projections", () => ({
  useProjections: () => ({
    projections: [],
    counts: { needs_attention: 0, receipts: 0 },
    refresh,
    present: vi.fn(),
    // The Missed drawer's own fields (AttentionDrawer, closed in these tests).
    open: false, setOpen: vi.fn(), query: "", setQuery: vi.fn(), kind: "", setKind: vi.fn(),
    error: "", select: vi.fn(), page: { total: 0, offset: 0, limit: 50, has_more: false },
  }),
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
}));
vi.mock("../DeskWindow", async (original) => ({
  ...(await original<typeof import("../DeskWindow")>()),
  DeskWindowFrame: () => null,
}));
vi.mock("../MicButton", () => ({ MicButton: () => null }));

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

/* The hub's own answer (scripts/record_needs_you_fixture.py, `grouped`: signed-out
 * GitHub Watches minted by the producer on the real hub). */
describe("SystemShade coverage over the recorded hub (HS-200-07)", () => {
  const GROUPED = (recorded as unknown as { grouped: { gets: Gets } }).grouped.gets;
  type Gap = { kind: string; label: string; state: string; repair: { token: string; verb: string } | null };
  const gaps = (GROUPED["/api/desk/needs-you?fresh=1"] as { coverage: Gap[] }).coverage
    .filter((row) => row.kind === "watch" && row.state === "failed");

  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    shell.openSurfaceOr.mockReset();
    vi.mocked(apiFetch).mockImplementation(async (path: string) => recordedGet(GROUPED, path) as never);
  });

  it("a Watch the hub could not check is a row naming the Watch, CANT CHECK and its repair; no all-clear", async () => {
    // replaces: tests/e2e/test_hs200_coverage_glass.py::TestCoverageGlass::test_shade_coverage_1440 (the 393 twin is the same DOM)
    expect(gaps.length).toBeGreaterThan(0);
    const onClose = vi.fn();
    render(<SystemShade open onClose={onClose} onOpenMemory={vi.fn()} />);
    const section = await screen.findByTestId("shade-coverage");
    expect(screen.queryByText("Nothing missed")).toBeNull();
    const rows = within(section).getAllByTestId("shade-coverage-row");
    const row = rows.find((r) => r.querySelector("strong")?.textContent === gaps[0].label)!;
    expect(row, `a row for ${gaps[0].label}`).toBeTruthy();
    expect(row.textContent).toContain(gaps[0].repair!.token);
    expect(gaps[0].repair!.token).toBe("CANT CHECK");
    const verb = within(row).getByTestId("shade-coverage-verb");
    expect(verb.textContent).toBe(gaps[0].repair!.verb);
    expect(verb.className).toContain("btn");
    fireEvent.click(verb);
    expect(onClose).toHaveBeenCalled();
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "connections");
  });

  it("the Missed launcher the Dock presses opens this shade", async () => {
    // replaces: tests/e2e/test_hs200_coverage_glass.py::TestCoverageGlass::test_shade_coverage_1440 (the open leg;
    // the Dock's press on [data-launcher=attention] is Dock.test.tsx's)
    render(<AttentionDrawer />);
    expect(document.querySelector(".desk-shade")).toBeNull();
    act(() => { expect(activateLauncher("attention")).toBe(true); });
    expect(await screen.findByTestId("shade-coverage")).toBeTruthy();
    expect(document.querySelector(".desk-shade")).not.toBeNull();
  });
});
