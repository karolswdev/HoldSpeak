// HS-135-04 — CatalogRail consuming-surface test: LedgerFilterBar
// hides below SPARSE_THRESHOLD, shows at/above it.
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogRail } from "../CatalogRail";
import { SPARSE_THRESHOLD } from "../../../../desk/surface/sparse";

function baseProps(rowCount: number) {
  const meetingRows = Array.from({ length: rowCount }, (_, i) => ({
    id: `m${i}`,
    title: `Meeting ${i}`,
    started_at: "2026-08-16T10:00:00Z",
    segment_count: 2,
    duration_seconds: 300,
    capture_status: "done",
  }));
  return {
    meetingRows,
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
    filterTotal: rowCount,
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

describe("CatalogRail sparse behavior (L10)", () => {
  it("hides filter bar when meetings < SPARSE_THRESHOLD", () => {
    render(<CatalogRail {...baseProps(1)} />);
    // The meeting row renders.
    expect(screen.getByText("Meeting 0")).toBeInTheDocument();
    // Filter bar does not render.
    expect(screen.queryByPlaceholderText("Filter...")).toBeNull();
    // But the Filters button is still there (it is a verb, not filter chrome).
    expect(screen.getByText("Filters")).toBeInTheDocument();
  });

  it("shows filter bar when meetings >= SPARSE_THRESHOLD", () => {
    render(<CatalogRail {...baseProps(SPARSE_THRESHOLD)} />);
    expect(screen.getByPlaceholderText("Filter...")).toBeInTheDocument();
  });

  it("shows empty well when there are zero meetings", () => {
    render(<CatalogRail {...baseProps(0)} />);
    expect(screen.getByText("Nothing here yet")).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("Filter...")).toBeNull();
  });
});
