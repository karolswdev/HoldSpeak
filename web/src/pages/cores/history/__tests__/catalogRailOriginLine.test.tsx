// HS-147-04 -- CatalogRail origin line test: event-linked meetings
// show a quiet "FROM SOURCE . EVENT TITLE" line; unlinked meetings
// show nothing. The stable data-meeting-origin selector is asserted.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogRail } from "../CatalogRail";

function baseProps(rows: Record<string, unknown>[]) {
  return {
    meetingRows: rows,
    meetings: { loading: false, error: "", reload: vi.fn(async () => ({})) },
    facets: { data: {} },
    selected: null,
    setSelected: vi.fn(),
    query: "",
    setQuery: vi.fn(),
    filterTokens: [],
    removeFilterToken: vi.fn(),
    clearFilter: vi.fn(),
    filterActive: false,
    filterTotal: rows.length,
    filtersOpen: false,
    setFiltersOpen: vi.fn(),
    dateFrom: "",
    setDateFrom: vi.fn(),
    dateTo: "",
    setDateTo: vi.fn(),
    speaker: "",
    setSpeaker: vi.fn(),
    tag: "",
    setTag: vi.fn(),
    openActions: false,
    setOpenActions: vi.fn(),
    needing: 0,
  };
}

describe("CatalogRail origin line (HS-147-04)", () => {
  it("shows origin line on event-linked meeting with source label and title", () => {
    const rows = [
      {
        id: "m-linked",
        title: "Sprint Review",
        started_at: "2026-08-28T14:00:00Z",
        segment_count: 5,
        duration_seconds: 1800,
        capture_status: "finalized",
        calendar_event_id: "ce_abc123",
        calendar_event_title: "Team Standup",
        calendar_source_label: "Work",
      },
    ];
    render(<CatalogRail {...baseProps(rows)} />);
    const origin = screen.getByText(/FROM WORK/);
    expect(origin).toBeInTheDocument();
    expect(origin.textContent).toContain("TEAM STANDUP");
    expect(origin).toHaveAttribute("data-meeting-origin", "calendar-event");
  });

  it("does not show origin line on unlinked meeting", () => {
    const rows = [
      {
        id: "m-unlinked",
        title: "Ad-hoc Meeting",
        started_at: "2026-08-28T14:00:00Z",
        segment_count: 3,
        duration_seconds: 600,
        capture_status: "finalized",
      },
    ];
    render(<CatalogRail {...baseProps(rows)} />);
    expect(screen.getByText("Ad-hoc Meeting")).toBeInTheDocument();
    const origins = document.querySelectorAll("[data-meeting-origin]");
    expect(origins.length).toBe(0);
  });

  it("shows origin line without title when event title missing", () => {
    const rows = [
      {
        id: "m-no-title",
        title: "Recording",
        started_at: "2026-08-28T14:00:00Z",
        segment_count: 1,
        duration_seconds: 300,
        capture_status: "finalized",
        calendar_event_id: "ce_xyz",
        // calendar_event_title absent (event row gone)
        calendar_source_label: "Personal",
      },
    ];
    render(<CatalogRail {...baseProps(rows)} />);
    const origin = screen.getByText("FROM PERSONAL");
    expect(origin).toBeInTheDocument();
    expect(origin).toHaveAttribute("data-meeting-origin", "calendar-event");
  });

  it("degrades to CALENDAR when source label absent", () => {
    const rows = [
      {
        id: "m-no-source",
        title: "Recording",
        started_at: "2026-08-28T14:00:00Z",
        segment_count: 1,
        duration_seconds: 300,
        capture_status: "finalized",
        calendar_event_id: "ce_fallback",
        calendar_event_title: "Design Review",
        // calendar_source_label absent
      },
    ];
    render(<CatalogRail {...baseProps(rows)} />);
    const origin = screen.getByText(/FROM CALENDAR/);
    expect(origin).toBeInTheDocument();
    expect(origin.textContent).toContain("DESIGN REVIEW");
  });
});
