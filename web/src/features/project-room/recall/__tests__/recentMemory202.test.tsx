/* HS-202-02 job 4 — Desk memory shows the desk's memory.
 *
 * 03-interaction-walk.md finding 7: the window's body is empty on a desk
 * that holds a meeting, two decision records and a brief. Traced: the face
 * is query-first — `useRecallController.run` returns before fetching when
 * the query is blank, and the whole result region is gated on `searched`.
 * A cold open asked the hub for nothing.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { apiFetch } from "../../../../lib/api";
import { RecallFace } from "../RecallFace";

vi.mock("../../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../../lib/api")>()),
  apiFetch: vi.fn(),
}));

const RECENT = {
  query: "",
  recent: true,
  filter: "all",
  searched_at: "2026-09-20T15:00:00",
  projects_searched: 2,
  current: [
    {
      id: "rec-1",
      ref: "decision_record:rec-1",
      text: "Freeze window is Saturday 02:00",
      rationale: "",
      lifecycle: "active",
      state: "current",
      dec_token: "DEC 09-19",
      decided_at: "2026-09-19T10:00:00",
      axes: ["DECISION", "SUPPORTED", "ACCEPTED"],
      support: "SUPPORTED",
      acceptance: "ACCEPTED",
      successor: null,
      predecessor_id: null,
      supersession_reason: null,
      dispute_reason: null,
      project: null,
      source: null,
      carried: false,
      commitment_ids: [],
    },
  ],
  superseded: [],
  disputed: [],
  owed: [],
  meetings: [],
  briefs: [],
  also: [],
  remembered: 1,
};

describe("the cold Desk memory window", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    localStorage.clear();
  });

  it("asks the hub for the desk's recent memory on open", async () => {
    vi.mocked(apiFetch).mockResolvedValue(RECENT as never);
    render(<RecallFace />);

    await waitFor(() =>
      expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
        expect.stringContaining("recent=1"),
      ),
    );
    const url = String(vi.mocked(apiFetch).mock.calls[0][0]);
    expect(url).toContain("/api/memory/recall?");
    expect(url).not.toContain("query=");
  });

  it("draws what came back, instead of a blank body", async () => {
    vi.mocked(apiFetch).mockResolvedValue(RECENT as never);
    render(<RecallFace />);

    expect(
      await screen.findByText("Freeze window is Saturday 02:00"),
    ).toBeVisible();
    expect(screen.getByTestId("recall-results")).toBeInTheDocument();
  });

  it("names the read for what it is, not as a search", async () => {
    vi.mocked(apiFetch).mockResolvedValue(RECENT as never);
    render(<RecallFace />);

    const results = await screen.findByTestId("recall-results");
    expect(results.getAttribute("aria-label")).toBe("Recent on this desk");
  });

  it("does not bury a resumed search under the recent read", async () => {
    localStorage.setItem(
      "hs.desk-memory.recall.v1",
      JSON.stringify({ query: "freeze window", filter: "all" }),
    );
    vi.mocked(apiFetch).mockResolvedValue({ ...RECENT, query: "freeze window", recent: false } as never);
    render(<RecallFace />);

    await waitFor(() => expect(vi.mocked(apiFetch)).toHaveBeenCalled());
    const url = String(vi.mocked(apiFetch).mock.calls[0][0]);
    expect(url).toContain("query=freeze+window");
    expect(url).not.toContain("recent=1");
  });
});
