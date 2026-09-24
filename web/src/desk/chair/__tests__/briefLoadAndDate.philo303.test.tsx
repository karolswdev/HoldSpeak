/* PHILO-3-03 (A3) — the BRIEF section tells the truth about its read.
 *
 * The defect: the Chair's `GET /api/brief/latest` caught every failure as
 * null (ChairHome.tsx `.catch(() => null)`), so a failed read drew
 * "No brief yet"; the brief's date (the route's period_label and
 * generated_label) was never on the face. The ratified canvas
 * (assets/story-03-canvas, owner 2026-09-23): READING… while the read is
 * open; BRIEF DID NOT LOAD · HTTP n (or NO ANSWER) with a Retry that reads
 * again; "No brief yet" only on a null answer; one date caption under the
 * brief. This drives the REAL Chair with a mocked apiFetch.
 */
import { act, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../../lib/api";
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

/** Each GET /api/brief/latest takes the next answer from this queue. */
let answers: Array<() => Promise<unknown>> = [];
let latestCalls = 0;

function wire() {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    const url = String(path);
    if (url === "/api/inference/assignments")
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 } as never;
    if (url.startsWith("/api/desk/needs-you"))
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    if (url.startsWith("/api/brief/latest")) {
      latestCalls += 1;
      const next = answers.shift() ?? (async () => null);
      return (await next()) as never;
    }
    return null as never;
  });
}

const POPULATED = {
  id: "brief-2",
  headline: "1 decision to review.",
  generated_at: "2026-09-24T09:30:00",
  is_empty: false,
  period_label: "SEP 21 – 24",
  generated_label: "GENERATED SEP 24 09:30",
  sections: {
    decisions: [{ id: "i1", section: "decisions", text: "Review decision: Adopt the one desk bus", priority: 200 }],
  },
};

describe("the BRIEF section: absent, loading, did not load, dated", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    answers = [];
    latestCalls = 0;
    wire();
  });

  it("says No brief yet only when the read answered null", async () => {
    answers = [async () => null];
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-brief");
    await waitFor(() => expect(within(section).getByText("No brief yet")).toBeTruthy());
    expect(screen.queryByTestId("arrival-brief-load-failed")).toBeNull();
  });

  it("says READING… while the read is open", async () => {
    answers = [() => new Promise(() => undefined)];
    render(<ChairHome />);
    const loading = await screen.findByTestId("arrival-brief-loading");
    expect(loading.textContent).toBe("READING…");
    expect(loading.classList.contains("surface-receipt-line")).toBe(true);
    expect(screen.queryByText("No brief yet")).toBeNull();
    expect(screen.queryByTestId("arrival-brief-generate")).toBeNull();
  });

  it("names a failed read with its status and Retry reads again", async () => {
    answers = [
      async () => {
        throw new ApiError(500, "boom", null);
      },
      async () => null,
    ];
    render(<ChairHome />);
    const failed = await screen.findByTestId("arrival-brief-load-failed");
    expect(failed.textContent).toBe("BRIEF DID NOT LOAD · HTTP 500");
    expect(failed.getAttribute("data-tone")).toBe("danger");
    expect(failed.classList.contains("surface-receipt-line")).toBe(true);
    expect(screen.queryByText("No brief yet")).toBeNull();
    expect(screen.queryByTestId("arrival-brief-generate")).toBeNull();

    const retry = screen.getByRole("button", { name: "Retry" });
    expect(retry.getAttribute("data-testid")).toBe("arrival-brief-retry");
    await act(async () => {
      retry.click();
    });
    expect(latestCalls).toBe(2);
    await waitFor(() => expect(screen.getByText("No brief yet")).toBeTruthy());
    expect(screen.queryByTestId("arrival-brief-load-failed")).toBeNull();
  });

  it("says NO ANSWER when the fetch got no response", async () => {
    answers = [
      async () => {
        throw new TypeError("Failed to fetch");
      },
    ];
    render(<ChairHome />);
    const failed = await screen.findByTestId("arrival-brief-load-failed");
    expect(failed.textContent).toBe("BRIEF DID NOT LOAD · NO ANSWER");
  });

  it("puts the period and the generated date under a populated brief", async () => {
    answers = [async () => POPULATED];
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-row");
    const date = screen.getByTestId("arrival-brief-date");
    expect(date.textContent).toBe("SEP 21 – 24 · GENERATED SEP 24 09:30");
    expect(date.classList.contains("surface-receipt-line")).toBe(true);
  });

  it("puts the date under an empty brief's headline too", async () => {
    answers = [async () => ({ ...POPULATED, is_empty: true, sections: {}, headline: "Nothing material changed." })];
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-headline");
    expect(screen.getByTestId("arrival-brief-date").textContent).toBe(
      "SEP 21 – 24 · GENERATED SEP 24 09:30",
    );
  });
});
