/** HS-200-07 (C4) — the command deck's PROJECTS badge carries the same
 *  truth: a Room with items counts them; a Room that was NOT observed
 *  shows its repair token instead of a silent zero. */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { apiFetch } from "../../lib/api";
import { DeskToolShelf } from "../components/DeskToolShelf";

vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));

const NEEDS_YOU = {
  count: 1,
  projects: ["alpha"],
  items: [{ projectId: "alpha", muted: false }],
  coverage: [
    { source_id: "project:alpha", kind: "project", state: "available",
      observed_at: "2026-09-06T09:30:00", label: "Q4 Platform",
      project_id: "alpha", reason: null, repair: null },
    { source_id: "project:beta", kind: "project", state: "failed",
      observed_at: null, label: "Governance", project_id: "beta",
      reason: "needsYou_read_failed",
      repair: { token: "READ FAILED", verb: "Retry", href: "/projects/beta" } },
  ],
  complete: false,
};

beforeEach(() => {
  localStorage.clear();
  usePalette.setState({ open: false });
  vi.mocked(apiFetch).mockReset();
  vi.mocked(apiFetch).mockImplementation(async (path: string) =>
    String(path).startsWith("/api/desk/needs-you") ? NEEDS_YOU : null);
  useDesk.setState({
    items: { ...EMPTY_ITEMS },
    projects: [
      { id: "alpha", name: "Q4 Platform" },
      { id: "beta", name: "Governance" },
    ] as never,
    inferenceTargets: [],
    models: [],
    setup: null,
    selectedIds: [],
    openPullout: vi.fn(),
    openToolInspector: vi.fn(),
    openChat: vi.fn(),
    diveInto: vi.fn(),
  });
});

describe("Command deck coverage (HS-200-07 / C4)", () => {
  it("badges an observed Room with its count and an unobserved Room with its token", async () => {
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));

    await waitFor(() =>
      expect(screen.getByText("Open Q4 Platform")).toBeTruthy());
    const alpha = screen.getByText("Open Q4 Platform").closest("li, [role=option], div");
    const beta = screen.getByText("Open Governance").closest("li, [role=option], div");
    await waitFor(() => expect(alpha?.textContent).toContain("1 NEEDS YOU"));
    // The unobserved Room never reads as a quiet zero.
    expect(beta?.textContent).toContain("READ FAILED");
  });
});
