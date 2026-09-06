// HS-200-07 (C4) — the arrival's rendering rule: "Nothing needs you" is
// spoken ONLY over complete coverage. An empty PARTIAL result shows the
// coverage token and the repair row with its owning verb.
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { ChairHome } from "./ChairHome";

vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));

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

const HEALTHY_ROOM = {
  source_id: "project:alpha",
  kind: "project",
  state: "available",
  observed_at: "2026-09-06T09:30:00",
  label: "Q4 Platform",
  project_id: "alpha",
  reason: null,
  repair: null,
};

function wire(needsYou: unknown) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (String(path).startsWith("/api/desk/needs-you")) {
      if (needsYou === "reject") throw new Error("Connection lost");
      return needsYou;
    }
    return null;
  });
}

describe("Arrival coverage (HS-200-07 / C4)", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset());

  it("says Nothing needs you only when the empty result is complete", async () => {
    wire({ count: 0, projects: [], items: [], next: null,
           coverage: [HEALTHY_ROOM], complete: true });
    render(<ChairHome />);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-display").textContent).toBe("Nothing needs you"));
    expect(screen.queryByTestId("arrival-coverage")).toBeNull();
  });

  it("never speaks the all-clear over an empty PARTIAL result", async () => {
    wire({ count: 0, projects: [], items: [], next: null,
           coverage: [HEALTHY_ROOM, FAILED_ROOM], complete: false });
    render(<ChairHome />);

    await waitFor(() => expect(screen.getByTestId("arrival-coverage")).toBeTruthy());
    expect(screen.getByTestId("arrival-display").textContent)
      .not.toBe("Nothing needs you");
    expect(screen.getByText("COVERAGE · 1 OF 2")).toBeTruthy();
    expect(screen.getByTestId("arrival-coverage-token").textContent).toBe("READ FAILED");
    expect(screen.getByTestId("arrival-coverage-observed").textContent)
      .toContain("LAST SEEN");
    // The owning verb, as the library Button.
    const verb = screen.getByTestId("arrival-coverage-verb");
    expect(verb.textContent).toBe("Retry");
    expect(verb.className).toContain("btn");
  });

  it("shows the coverage row beside healthy items and marks a remembered row", async () => {
    wire({
      count: 1,
      projects: ["beta"],
      items: [{
        projectId: "beta", projectName: "Governance", ref: "CI red",
        title: "CI red on main", why: "CI RED · 2h", ageToken: "2h",
        source: "github", verbHref: null, severity: "danger",
        id: "beta:github:CI red", fromLastObservation: true,
        observedAt: "2026-09-06T09:00:00",
      }],
      next: null,
      coverage: [HEALTHY_ROOM, FAILED_ROOM],
      complete: false,
    });
    render(<ChairHome />);

    await waitFor(() => expect(screen.getByTestId("arrival-needs-you")).toBeTruthy());
    expect(screen.getByTestId("arrival-display").textContent).toContain("need you");
    expect(screen.getByTestId("arrival-coverage")).toBeTruthy();
    expect(screen.getByTestId("arrival-remembered").textContent).toContain("LAST SEEN");
  });

  it("treats a read that never landed as a coverage gap, not as quiet", async () => {
    wire("reject");
    render(<ChairHome />);

    await waitFor(() => expect(screen.getByTestId("arrival-coverage")).toBeTruthy());
    expect(screen.getByTestId("arrival-display").textContent)
      .not.toBe("Nothing needs you");
    expect(screen.getByText("COVERAGE · 0 OF 1")).toBeTruthy();
  });

  it("keeps the arrival honest at the narrow viewport rule (no prose row)", async () => {
    wire({ count: 0, projects: [], items: [], next: null,
           coverage: [HEALTHY_ROOM, FAILED_ROOM], complete: false });
    render(<ChairHome />);

    await waitFor(() => expect(screen.getByTestId("arrival-coverage")).toBeTruthy());
    const rows = screen.getAllByTestId("arrival-coverage-row");
    expect(rows).toHaveLength(1);
    for (const row of rows) {
      for (const text of Array.from(row.querySelectorAll("*"))
        .map((n) => n.textContent ?? "")) {
        expect(text.length).toBeLessThanOrEqual(60);
      }
    }
  });
});
