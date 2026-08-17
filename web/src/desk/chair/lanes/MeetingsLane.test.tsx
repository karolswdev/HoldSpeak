// HS-135-09 -- Meetings lane tests: seeded list rendering with badges,
// live-meeting pinning (frame fixture), maxItems, open targets fire
// correctly, empty state honest.

import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MeetingsLane, intelBadge } from "./MeetingsLane";
import type { Meeting } from "../../../lib/primitives";

// ---------------------------------------------------------------------------
// store mock: items.meeting + recording state
// ---------------------------------------------------------------------------

let storeState: {
  recording: "idle" | "busy" | "recording";
  items: { meeting: Meeting[] };
} = {
  recording: "idle",
  items: { meeting: [] },
};

vi.mock("../../store", () => {
  const useDesk = (selector: (s: typeof storeState) => unknown) =>
    selector(storeState);
  useDesk.getState = () => storeState;
  return { useDesk };
});

// ---------------------------------------------------------------------------
// fixtures
// ---------------------------------------------------------------------------

function makeMeeting(overrides: Partial<Meeting> = {}): Meeting {
  return {
    kind: "meeting",
    id: `meeting-${Math.random().toString(36).slice(2, 8)}`,
    title: "Weekly standup",
    startedAt: "2026-08-10T14:00:00Z",
    endedAt: "2026-08-10T14:30:00Z",
    segmentCount: 12,
    actionItemCount: 3,
    intelStatus: "complete",
    ...overrides,
  };
}

const finishedMeeting = makeMeeting({
  id: "m-finished",
  title: "Sprint review",
  startedAt: "2026-08-10T14:00:00Z",
  endedAt: "2026-08-10T14:30:00Z",
  segmentCount: 8,
  actionItemCount: 2,
  intelStatus: "complete",
});

const liveMeeting = makeMeeting({
  id: "m-live",
  title: "Design sync",
  startedAt: "2026-08-16T10:00:00Z",
  endedAt: null,
  segmentCount: 4,
  actionItemCount: 0,
  intelStatus: null,
});

const olderMeeting = makeMeeting({
  id: "m-older",
  title: "Retro",
  startedAt: "2026-08-05T09:00:00Z",
  endedAt: "2026-08-05T10:00:00Z",
  segmentCount: 20,
  actionItemCount: 5,
  intelStatus: "running",
});

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

function resetStore(overrides: Partial<typeof storeState> = {}) {
  storeState = {
    recording: "idle",
    items: { meeting: [] },
    ...overrides,
  };
}

function renderLane(
  props: Partial<React.ComponentProps<typeof MeetingsLane>> = {},
) {
  const onOpenInWindow = props.onOpenInWindow ?? vi.fn();
  const result = render(
    <MeetingsLane onOpenInWindow={onOpenInWindow} {...props} />,
  );
  return { ...result, onOpenInWindow };
}

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------

describe("MeetingsLane", () => {
  beforeEach(() => {
    resetStore();
    vi.clearAllMocks();
  });

  // -- seeded list rendering with badges -----------------------------------

  describe("seeded list rendering with badges", () => {
    it("renders meetings with titles and detail (date, segments, actions)", () => {
      resetStore({ items: { meeting: [finishedMeeting] } });
      renderLane();
      expect(screen.getByText("Sprint review")).toBeInTheDocument();
      // Detail: AUG 10 · 8 seg · 2 action
      expect(screen.getByText(/AUG 10/)).toBeInTheDocument();
      expect(screen.getByText(/8 seg/)).toBeInTheDocument();
      expect(screen.getByText(/2 action/)).toBeInTheDocument();
    });

    it("renders truthful intel badge as meta", () => {
      resetStore({ items: { meeting: [finishedMeeting] } });
      renderLane();
      // complete -> "SAVED"
      expect(screen.getByText("SAVED")).toBeInTheDocument();
    });

    it("shows RUNNING badge for in-progress intelligence", () => {
      resetStore({ items: { meeting: [olderMeeting] } });
      renderLane();
      expect(screen.getByText("RUNNING")).toBeInTheDocument();
    });

    it("uses the meetings glyph for finished meetings", () => {
      resetStore({ items: { meeting: [finishedMeeting] } });
      const { container } = renderLane();
      const glyphs = container.querySelectorAll(".surface-row-glyph");
      expect(glyphs).toHaveLength(1);
      expect(glyphs[0].textContent).toBe("▣"); // ▣
    });

    it("falls back to 'Untitled meeting' when title is empty", () => {
      const untitled = makeMeeting({ id: "m-untitled", title: "" });
      resetStore({ items: { meeting: [untitled] } });
      renderLane();
      expect(screen.getByText("Untitled meeting")).toBeInTheDocument();
    });

    it("sorts by startedAt descending (most recent first)", () => {
      resetStore({
        items: { meeting: [olderMeeting, finishedMeeting] },
      });
      renderLane();
      const listItems = screen.getAllByRole("listitem");
      const titles = listItems
        .map(
          (li) =>
            within(li).queryByText(/Sprint review|Retro/)?.textContent,
        )
        .filter(Boolean);
      expect(titles).toEqual(["Sprint review", "Retro"]);
    });
  });

  // -- live meeting pinning ------------------------------------------------

  describe("live-meeting pinning (frame fixture)", () => {
    it("pins the live meeting first when recording is active", () => {
      resetStore({
        recording: "recording",
        items: { meeting: [finishedMeeting, liveMeeting, olderMeeting] },
      });
      renderLane();
      const listItems = screen.getAllByRole("listitem");
      const titles = listItems
        .map(
          (li) =>
            within(li).queryByText(/Design sync|Sprint review|Retro/)
              ?.textContent,
        )
        .filter(Boolean);
      // Live meeting first, then by date descending.
      expect(titles[0]).toBe("Design sync");
    });

    it("shows REC badge for the live meeting", () => {
      resetStore({
        recording: "recording",
        items: { meeting: [liveMeeting] },
      });
      renderLane();
      expect(screen.getByText("REC")).toBeInTheDocument();
    });

    it("uses the live glyph for the recording meeting", () => {
      resetStore({
        recording: "recording",
        items: { meeting: [liveMeeting] },
      });
      const { container } = renderLane();
      const glyphs = container.querySelectorAll(".surface-row-glyph");
      expect(glyphs[0].textContent).toBe("●"); // ●
    });

    it("does NOT pin when recording is idle (no endedAt is just data)", () => {
      resetStore({
        recording: "idle",
        items: { meeting: [finishedMeeting, liveMeeting] },
      });
      renderLane();
      // liveMeeting.startedAt (2026-08-16) is newer than finishedMeeting
      // (2026-08-10), so it sorts first by date regardless.
      const listItems = screen.getAllByRole("listitem");
      const titles = listItems
        .map(
          (li) =>
            within(li).queryByText(/Design sync|Sprint review/)
              ?.textContent,
        )
        .filter(Boolean);
      expect(titles[0]).toBe("Design sync");
      // But it should NOT show REC badge.
      expect(screen.queryByText("REC")).not.toBeInTheDocument();
    });
  });

  // -- maxItems ------------------------------------------------------------

  describe("maxItems", () => {
    it("caps visible items at maxItems", () => {
      const many = Array.from({ length: 5 }, (_, i) =>
        makeMeeting({
          id: `m-${i}`,
          title: `Meeting ${i}`,
          startedAt: `2026-08-${String(10 + i).padStart(2, "0")}T10:00:00Z`,
        }),
      );
      resetStore({ items: { meeting: many } });
      renderLane({ maxItems: 3 });
      // Only 3 of 5 visible.
      const listItems = screen.getAllByRole("listitem");
      expect(listItems).toHaveLength(3);
    });

    it("shows overflow footer when items exceed maxItems", () => {
      const many = Array.from({ length: 5 }, (_, i) =>
        makeMeeting({
          id: `m-${i}`,
          title: `Meeting ${i}`,
          startedAt: `2026-08-${String(10 + i).padStart(2, "0")}T10:00:00Z`,
        }),
      );
      resetStore({ items: { meeting: many } });
      renderLane({ maxItems: 3 });
      expect(screen.getByText(/2 more/)).toBeInTheDocument();
    });

    it("defaults maxItems to 12", () => {
      const many = Array.from({ length: 14 }, (_, i) =>
        makeMeeting({
          id: `m-${i}`,
          title: `Meeting ${i}`,
          startedAt: `2026-08-${String(i + 1).padStart(2, "0")}T10:00:00Z`,
        }),
      );
      resetStore({ items: { meeting: many } });
      renderLane();
      const listItems = screen.getAllByRole("listitem");
      expect(listItems).toHaveLength(12);
      expect(screen.getByText(/2 more/)).toBeInTheDocument();
    });
  });

  // -- open targets --------------------------------------------------------

  describe("open targets fire correctly", () => {
    it("header click fires onOpenInWindow with 'review-meetings'", () => {
      resetStore({ items: { meeting: [finishedMeeting] } });
      const { onOpenInWindow } = renderLane();
      const headerBtn = screen.getByLabelText("Open MEETINGS");
      fireEvent.click(headerBtn);
      expect(onOpenInWindow).toHaveBeenCalledWith("review-meetings");
    });

    it("item click fires onOpenInWindow with the meeting id", () => {
      resetStore({ items: { meeting: [finishedMeeting] } });
      const { onOpenInWindow } = renderLane();
      const rowBtn = screen.getByRole("button", { name: /Sprint review/ });
      fireEvent.click(rowBtn);
      expect(onOpenInWindow).toHaveBeenCalledWith("m-finished");
    });

    it("footer click fires onOpenInWindow with 'review-meetings'", () => {
      const many = Array.from({ length: 5 }, (_, i) =>
        makeMeeting({
          id: `m-${i}`,
          title: `Meeting ${i}`,
          startedAt: `2026-08-${String(10 + i).padStart(2, "0")}T10:00:00Z`,
        }),
      );
      resetStore({ items: { meeting: many } });
      const { onOpenInWindow } = renderLane({ maxItems: 3 });
      const footerBtn = screen.getByText(/2 more/);
      fireEvent.click(footerBtn);
      expect(onOpenInWindow).toHaveBeenCalledWith("review-meetings");
    });
  });

  // -- empty state ---------------------------------------------------------

  describe("empty state honest", () => {
    it("returns null when there are no meetings", () => {
      resetStore({ items: { meeting: [] } });
      const { container } = renderLane();
      expect(container.innerHTML).toBe("");
    });
  });

  // -- intelBadge unit tests -----------------------------------------------

  describe("intelBadge", () => {
    it.each([
      ["complete", "SAVED"],
      ["running", "RUNNING"],
      ["queued", "QUEUED"],
      ["pending", "QUEUED"],
      ["error", "FAILED"],
      ["failed", "FAILED"],
      ["partial", "PARTIAL"],
      ["skipped", "SKIPPED"],
      ["disabled", "OFF"],
      [null, "SAVED"],
      [undefined, "SAVED"],
      ["unknown_value", "SAVED"],
    ] as const)("maps %s to %s", (input, expected) => {
      expect(intelBadge(input)).toBe(expected);
    });
  });
});
