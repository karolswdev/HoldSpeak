import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FinishThoughtsLane, relativeUpdated } from "./FinishThoughtsLane";
import { unfinishedThoughts, type UnfinishedThought } from "../thoughts";
import { useDesk } from "../store";

vi.mock("../thoughts", () => ({ unfinishedThoughts: vi.fn() }));

const NOW = Date.parse("2026-08-19T18:00:00Z");

function item(overrides: Partial<UnfinishedThought> = {}): UnfinishedThought {
  return {
    id: "thought-1",
    working_note_id: "note-1",
    source_kind: "typed",
    title: "Plan the migration dry run",
    body_preview: "Plan the migration dry run",
    updated_at: "2026-08-19T17:53:00Z",
    continuity_state: "idle",
    filing_status: "filed",
    ...overrides,
  };
}

beforeEach(() => {
  vi.setSystemTime(NOW);
  vi.mocked(unfinishedThoughts).mockResolvedValue({
    items: [],
    next_cursor: null,
  });
  useDesk.setState({ openPullout: vi.fn(), updatedAt: null });
});

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("FinishThoughtsLane", () => {
  it("is absent when unfinished work is empty", async () => {
    const { container } = render(<FinishThoughtsLane />);
    await waitFor(() => expect(unfinishedThoughts).toHaveBeenCalledWith());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows three semantic rows, an honest count, and bounded pagination", async () => {
    const first = [
      item(),
      item({
        id: "thought-2",
        working_note_id: "note-2",
        title: "A voice draft",
        body_preview: "A distinct useful preview",
        source_kind: "voice",
        continuity_state: "in_flight",
      }),
      item({
        id: "thought-3",
        working_note_id: "note-3",
        title: "Decision needed",
        body_preview: "Choose the rollback owner",
        continuity_state: "review_ready",
        filing_status: "missing",
      }),
    ];
    vi.mocked(unfinishedThoughts)
      .mockResolvedValueOnce({ items: first, next_cursor: "page-2" })
      .mockResolvedValueOnce({
        items: [
          first[2],
          item({
            id: "thought-4",
            working_note_id: "note-4",
            title: "Repair the failed run",
            continuity_state: "named_failure",
          }),
        ],
        next_cursor: null,
      });

    render(<FinishThoughtsLane />);
    const heading = await screen.findByRole("heading", {
      name: "Finish thoughts",
    });
    expect(heading).toBeInTheDocument();
    expect(
      screen.getByLabelText("3 or more unfinished thoughts"),
    ).toHaveTextContent("3+");

    const list = screen.getByRole("list");
    expect(within(list).getAllByRole("listitem")).toHaveLength(3);
    expect(within(list).getAllByRole("button")).toHaveLength(3);
    expect(screen.getAllByText("Plan the migration dry run")).toHaveLength(1);
    expect(screen.getByText("A distinct useful preview")).toBeInTheDocument();
    expect(screen.getByText("Working")).toBeInTheDocument();
    expect(screen.getByText("Ready for you")).toBeInTheDocument();
    expect(screen.getByText("Not in a drawer")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show more" }));
    await screen.findByRole("button", { name: /Repair the failed run/ });
    expect(unfinishedThoughts).toHaveBeenLastCalledWith("page-2");
    expect(screen.getByLabelText("4 unfinished thoughts")).toHaveTextContent(
      "4",
    );
    expect(screen.queryByRole("button", { name: "Show more" })).toBeNull();
  });

  it("retains the bounded page and lets an explicit Show more retry after failure", async () => {
    vi.mocked(unfinishedThoughts)
      .mockResolvedValueOnce({ items: [item()], next_cursor: "retry-page" })
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({
        items: [
          item({
            id: "thought-2",
            working_note_id: "note-2",
            title: "Recovered row",
          }),
        ],
        next_cursor: null,
      });
    render(<FinishThoughtsLane />);
    const more = await screen.findByRole("button", { name: "Show more" });

    fireEvent.click(more);
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Show more" }),
      ).not.toBeDisabled(),
    );
    expect(screen.getAllByRole("listitem")).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "Show more" }));
    await screen.findByRole("button", { name: /Recovered row/ });
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(unfinishedThoughts).toHaveBeenNthCalledWith(2, "retry-page");
    expect(unfinishedThoughts).toHaveBeenNthCalledWith(3, "retry-page");
  });

  it("opens the exact working Note without a write or model action", async () => {
    vi.mocked(unfinishedThoughts).mockResolvedValue({
      items: [item({ working_note_id: "note-exact", title: "Continue this" })],
      next_cursor: null,
    });
    render(<FinishThoughtsLane />);
    fireEvent.click(
      await screen.findByRole("button", { name: /Continue this/ }),
    );
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith(
      "note:note-exact",
    );
    expect(unfinishedThoughts).toHaveBeenCalledTimes(1);
  });

  it("re-reads unfinished work after the Desk refreshes", async () => {
    vi.mocked(unfinishedThoughts)
      .mockResolvedValueOnce({ items: [item({ title: "Still working" })], next_cursor: null })
      .mockResolvedValueOnce({ items: [], next_cursor: null });

    const { container } = render(<FinishThoughtsLane />);
    await screen.findByRole("button", { name: /Still working/ });

    useDesk.setState({ updatedAt: NOW + 1 });
    await waitFor(() => expect(unfinishedThoughts).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });

  it("maps continuity into concise owner states", async () => {
    vi.mocked(unfinishedThoughts).mockResolvedValue({
      items: [
        item({ id: "a", title: "A", continuity_state: "idle" }),
        item({ id: "b", title: "B", continuity_state: "awaiting_projection" }),
        item({ id: "c", title: "C", continuity_state: "review_ready" }),
        item({ id: "d", title: "D", continuity_state: "stale" }),
      ],
      next_cursor: null,
    });
    render(<FinishThoughtsLane />);
    await screen.findByRole("button", { name: /^A/ });
    expect(screen.getByText("Continue")).toBeInTheDocument();
    expect(screen.getByText("Working")).toBeInTheDocument();
    expect(screen.getByText("Ready for you")).toBeInTheDocument();
    expect(screen.getByText("Needs attention")).toBeInTheDocument();
  });
});

describe("relativeUpdated", () => {
  it("uses compact stable minute, hour, day, week, month, and year labels", () => {
    expect(relativeUpdated("2026-08-19T17:59:40Z", NOW)).toBe("Updated now");
    expect(relativeUpdated("2026-08-19T17:53:00Z", NOW)).toBe("Updated 7m ago");
    expect(relativeUpdated("2026-08-19T15:00:00Z", NOW)).toBe("Updated 3h ago");
    expect(relativeUpdated("2026-08-17T18:00:00Z", NOW)).toBe("Updated 2d ago");
    expect(relativeUpdated("2026-08-05T18:00:00Z", NOW)).toBe("Updated 2w ago");
    expect(relativeUpdated("2026-06-20T18:00:00Z", NOW)).toBe(
      "Updated 2mo ago",
    );
    expect(relativeUpdated("2025-08-19T18:00:00Z", NOW)).toBe("Updated 1y ago");
  });
});
