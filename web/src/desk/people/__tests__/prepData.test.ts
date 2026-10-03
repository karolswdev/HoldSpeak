import { describe, expect, it, vi } from "vitest";
import type { apiFetch } from "../../../lib/api";
import { composePeoplePrep, readPeoplePrep } from "../prepData";

const brief = {
  calendar_link_suggestions: [
    {
      id: "event-1",
      uid: "uid-1",
      title: "1:1 Priya / Karol",
      starts_at: "2099-11-04T16:00:00Z",
      ends_at: "2099-11-04T16:30:00Z",
      source_id: "calendar-1",
      source_label: "Work",
    },
  ],
  next_one_on_one: null,
  agenda_items: [{ id: "agenda-1", body: "Review the launch plan" }],
  open_meeting_actions: [
    {
      id: "action-1",
      meeting_id: "meeting-1",
      task: "Send the dry-run report",
      owner: "Priya",
      due: null,
      delegated_at: null,
      meeting_title: "1:1 Priya / Karol",
      meeting_started_at: "2099-11-04T16:00:00+00:00",
      calendar_event_id: "event-1",
    },
  ],
  projects: [{ id: "project-1", name: "Dry-run project" }],
};

describe("People Prep data", () => {
  it("composes the transient brief without changing its references", () => {
    const result = composePeoplePrep(brief);

    expect(result).toEqual({
      calendarLinkSuggestions: brief.calendar_link_suggestions,
      nextOneOnOne: null,
      agenda: brief.agenda_items,
      openMeetingActions: brief.open_meeting_actions,
      projects: brief.projects,
    });
    expect(brief.open_meeting_actions[0].meeting_id).toBe("meeting-1");
  });

  it("reads the existing brief route and returns the typed composition", async () => {
    const fetcher = vi.fn(async () => ({ brief })) as unknown as typeof apiFetch;

    await expect(readPeoplePrep("relationship/1", fetcher)).resolves.toEqual(
      composePeoplePrep(brief),
    );
    expect(fetcher).toHaveBeenCalledWith(
      "/api/people/relationships/relationship%2F1/brief",
    );
  });
});
