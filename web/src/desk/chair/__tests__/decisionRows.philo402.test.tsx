/* PHILO-4-02 — the Arrival puts the newest decision in its visible rows.
 *
 * The payload mirrors the API shape produced by the real brief producer,
 * including record timestamps and an intentionally non-recency-sorted id set.
 */
import { act, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { ChairHome } from "../ChairHome";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

const ARRIVAL_BRIEF = {
  id: "brief-next-day",
  headline: "3 things changed, 4 decisions waiting.",
  generated_at: "2026-09-24T08:02:00",
  is_empty: false,
  period_label: "SEP 21 – 24",
  generated_label: "GENERATED SEP 24 08:02",
  shelf: {},
  sections: {
    // Intentionally UNSORTED. Arrival ordering must use created_at, not id
    // or the wire's incidental order.
    decisions: [
      {
        id: "decision-z-old-item",
        section: "decisions",
        text: "Review decision: Old decision one",
        priority: 200,
        created_at: "2026-09-23T18:05:00",
      },
      {
        id: "decision-a-new-item",
        section: "decisions",
        text: "Review decision: Newest decision",
        priority: 200,
        created_at: "2026-09-24T07:58:00",
      },
      {
        id: "decision-m-old-item",
        section: "decisions",
        text: "Review decision: Old decision two",
        priority: 200,
        created_at: "2026-09-23T17:31:00",
      },
      {
        id: "decision-b-old-item",
        section: "decisions",
        text: "Review decision: Old decision three",
        priority: 200,
        created_at: "2026-09-22T09:10:00",
      },
    ],
    changed: [
      { id: "changed-old", section: "changed", text: "Meeting recorded: Older meeting", priority: 50 },
    ],
    broke: [
      { id: "broke-old", section: "broke", text: "Older breakage", priority: 1 },
    ],
    waiting: [
      { id: "waiting-old", section: "waiting", text: "Open loop: Older loop", priority: 100 },
    ],
  },
};

const DAY_ONE = {
  ...ARRIVAL_BRIEF,
  id: "brief-day-one",
  headline: "1 thing changed, 1 decision waiting.",
  sections: {
    changed: [{ id: "day-one-change", section: "changed", text: "Meeting recorded: Yesterday", priority: 50 }],
    broke: [],
    waiting: [],
    decisions: [ARRIVAL_BRIEF.sections.decisions[0]],
  },
};

let latest: unknown;
let generated: unknown;

function wire() {
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
    const url = String(path);
    const method = (init as { method?: string } | undefined)?.method ?? "GET";
    if (url === "/api/inference/assignments") {
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 } as never;
    }
    if (url.startsWith("/api/desk/needs-you")) {
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    }
    if (url === "/api/door") return null as never;
    if (url.startsWith("/api/brief/latest")) return latest as never;
    if (url === "/api/brief/generate" && method === "POST") return generated as never;
    return null as never;
  });
}

function expectDecisionRows() {
  const section = screen.getByTestId("arrival-brief");
  const rows = screen.getAllByTestId("arrival-brief-row");
  expect(rows).toHaveLength(3);
  expect(rows.map((row) => row.textContent)).toEqual([
    expect.stringContaining("Review decision: Newest decision"),
    expect.stringContaining("Review decision: Old decision one"),
    expect.stringContaining("Review decision: Old decision two"),
  ]);
  expect(within(section).getByRole("heading", { name: "BRIEF · 7 THINGS WAITING" })).toBeTruthy();
  expect(within(section).getByTestId("arrival-brief-more").textContent).toBe("4 more");
}

describe("PHILO-4-02: decision rows lead the Arrival cap", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    latest = ARRIVAL_BRIEF;
    generated = ARRIVAL_BRIEF;
    wire();
  });

  it("shows the newest decision first with an honest cap and fold", async () => {
    render(<ChairHome />);
    await screen.findAllByTestId("arrival-brief-row");
    expectDecisionRows();
  });

  it("keeps the result ordered after Generate replaces an existing brief", async () => {
    latest = DAY_ONE;
    render(<ChairHome />);
    await screen.findAllByTestId("arrival-brief-row");

    await act(async () => {
      screen.getByTestId("arrival-brief-generate").click();
    });
    await waitFor(() => {
      expect(screen.getByText("Review decision: Newest decision")).toBeTruthy();
    });
    expectDecisionRows();
  });
});
