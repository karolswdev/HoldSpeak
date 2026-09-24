/* PHILO-4-04 — the saved brief headline and current Arrival triage state
 * occupy two durable facts. The six-row values below are the day-one
 * fixture from story 01's `compose_headline.py`, which runs the real
 * MondayBriefService._compose: m1, o1, u1, l1, d2 and c1.
 *
 * These are rendered fences. They deliberately read the Chair after the
 * brief read, after a Generate transition, and after generation failure or
 * success. A helper-only count cannot prove the line survives a branch
 * change.
 */
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../../lib/api";
import { ChairHome } from "../ChairHome";
import headlineFixture from "../../../../../docs/internal/philo/phase-4/headline/fixture.json";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../thoughts", () => ({
  unfinishedThoughts: async () => ({ items: [] }),
}));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
  useRuntimeFrame: () => null,
}));

type FixtureRow = {
  id: string;
  section: string;
  text: string;
  source_ref: string;
  priority: number;
};
type FixtureSections = Record<string, FixtureRow[]>;

// Shared with the storage fence: this is the six-row real `_compose` output,
// rather than a second hand-written UI-only version of the producer fixture.
const COMPOSED_SECTIONS = Object.fromEntries(
  Object.entries(headlineFixture.sections).map(([section, rows]) => [
    section,
    rows.map((row) => ({ ...row, section })),
  ]),
) as FixtureSections;
const DAY_ONE_HEADLINE = headlineFixture.headline;
const DAY_ONE_SHELF = {
  m1: "acknowledged",
  o1: "deferred",
  u1: "acknowledged",
  l1: "deferred",
  d2: "acknowledged",
  c1: "deferred",
};

function dayOneBrief(
  overrides: Record<string, unknown> = {},
  sections: Record<string, unknown[]> = COMPOSED_SECTIONS,
) {
  return {
    id: "brief-day-one",
    headline: DAY_ONE_HEADLINE,
    generated_at: "2026-09-23T17:40:00",
    is_empty: false,
    period_label: "SEP 21 – 23",
    generated_label: "GENERATED SEP 23 17:40",
    sections,
    shelf: DAY_ONE_SHELF,
    ...overrides,
  };
}

let latest: Record<string, unknown> | null = null;
let generated: Record<string, unknown> = dayOneBrief();
let generationFailure: unknown = null;
let generationGate: Promise<unknown> | null = null;

function wire() {
  vi.mocked(apiFetch).mockImplementation(
    async (path: string, init?: unknown) => {
      const url = String(path);
      if (url === "/api/inference/assignments") {
        return {
          schema: "InferenceAssignmentSummary@1",
          rows: [],
          task_overrides: [],
          issue_count: 0,
        } as never;
      }
      if (url.startsWith("/api/desk/needs-you")) {
        return {
          count: 0,
          items: [],
          projects: [],
          next: null,
          coverage: [],
          complete: true,
        } as never;
      }
      if (url.startsWith("/api/brief/latest")) return latest as never;
      if (
        url === "/api/brief/generate" &&
        (init as { method?: string })?.method === "POST"
      ) {
        if (generationFailure) throw generationFailure;
        if (generationGate) return (await generationGate) as never;
        return generated as never;
      }
      return null as never;
    },
  );
}

function expectHandledOrder(
  section: HTMLElement,
  count: number,
  expectedHeadline = DAY_ONE_HEADLINE,
) {
  const headline = screen.getByTestId("arrival-brief-headline");
  const date = screen.getByTestId("arrival-brief-date");
  const handled = screen.getByTestId("arrival-brief-handled");
  expect(headline.textContent).toBe(expectedHeadline);
  expect(date.textContent).toBe("SEP 21 – 23 · GENERATED SEP 23 17:40");
  expect(handled.textContent).toBe(`ALL ${count} HANDLED`);
  expect(handled.getAttribute("role")).toBeNull();
  expect(section.textContent!.indexOf(expectedHeadline)).toBeLessThan(
    section.textContent!.indexOf(date.textContent!),
  );
  expect(section.textContent!.indexOf(date.textContent!)).toBeLessThan(
    section.textContent!.indexOf(`ALL ${count} HANDLED`),
  );
}

describe("the triaged Arrival headline", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    latest = null;
    generated = dayOneBrief();
    generationFailure = null;
    generationGate = null;
    wire();
  });

  it("keeps the real six-row headline and date, then names all six handled", async () => {
    latest = dayOneBrief();
    const expectedSections = structuredClone(COMPOSED_SECTIONS);
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-brief");
    await waitFor(() =>
      expect(screen.getByTestId("arrival-brief-headline")).toBeInTheDocument(),
    );

    expectHandledOrder(section, 6);
    expect(section.textContent).not.toContain("BRIEF · 0");
    expect(screen.queryAllByTestId("arrival-brief-row")).toHaveLength(0);
    // The quiet branch must not rewrite the producer's stored six-row result.
    expect(latest?.sections).toEqual(expectedSections);
    expect(latest?.headline).toBe(DAY_ONE_HEADLINE);
  });

  it("does not count THIS WEEK toward the Arrival handled line", async () => {
    const thisWeekVariant = headlineFixture.this_week_variant;
    latest = dayOneBrief({
      sections: {
        ...structuredClone(COMPOSED_SECTIONS),
        this_week: [{ ...thisWeekVariant.row }],
      },
      headline: thisWeekVariant.headline,
      shelf: {},
    });
    // The six Arrival rows are handled; the separate THIS WEEK row has no
    // shelf state and must not block or inflate the Arrival count.
    (latest as { shelf: Record<string, string> }).shelf = DAY_ONE_SHELF;
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-brief");
    await waitFor(() =>
      expect(screen.getByTestId("arrival-brief-headline")).toBeInTheDocument(),
    );
    expectHandledOrder(section, 6, thisWeekVariant.headline);
    expect(screen.queryByText(thisWeekVariant.row.text)).toBeNull();
  });

  it("withholds the line while one Arrival row is still untriaged", async () => {
    const partialShelf: Record<string, string> = { ...DAY_ONE_SHELF };
    delete partialShelf.c1;
    latest = dayOneBrief({ shelf: partialShelf });
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-row");
    expect(screen.queryByTestId("arrival-brief-handled")).toBeNull();
    expect(screen.queryByText(/ALL \d+ HANDLED/)).toBeNull();
    expect(screen.queryByTestId("arrival-brief-headline")).toBeNull();
  });

  it("does not claim handling when a hidden raw-id Arrival row has no shelf", async () => {
    latest = dayOneBrief({
      sections: {
        ...structuredClone(COMPOSED_SECTIONS),
        waiting: [
          ...structuredClone(COMPOSED_SECTIONS.waiting),
          {
            id: "raw-row",
            section: "waiting",
            text: "PrimitiveService.delete_directory",
            source_ref: "action_item:raw-row",
            priority: 1,
          },
        ],
      },
      shelf: DAY_ONE_SHELF,
    });
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief");
    await waitFor(() =>
      expect(screen.queryByTestId("arrival-brief-date")).toBeInTheDocument(),
    );
    expect(screen.queryByTestId("arrival-brief-handled")).toBeNull();
    expect(screen.queryByText("PrimitiveService.delete_directory")).toBeNull();
  });

  it("keeps No changes bare without a zero handled count", async () => {
    latest = dayOneBrief({
      id: "brief-empty",
      headline: "No changes",
      is_empty: true,
      sections: {},
      shelf: {},
    });
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-brief");
    await waitFor(() =>
      expect(screen.getByTestId("arrival-brief-headline")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("arrival-brief-headline").textContent).toBe(
      "No changes",
    );
    expect(screen.queryByTestId("arrival-brief-handled")).toBeNull();
    expect(section.textContent).not.toContain("BRIEF · 0");
    expect(section.textContent).not.toContain("HANDLED");
  });

  it("keeps the line in place while Generate is open", async () => {
    latest = dayOneBrief();
    generationGate = new Promise(() => undefined);
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-brief");
    const generateButton = await screen.findByTestId("arrival-brief-generate");
    await act(async () => {
      generateButton.click();
    });
    expect(
      await screen.findByTestId("arrival-brief-generating"),
    ).toHaveTextContent("GENERATING…");
    expectHandledOrder(section, 6);
  });

  it("keeps the line after generation failure", async () => {
    latest = dayOneBrief();
    generationFailure = new ApiError(500, "boom", null);
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-brief");
    const generateButton = await screen.findByTestId("arrival-brief-generate");
    await act(async () => {
      generateButton.click();
    });
    expect(
      await screen.findByTestId("arrival-brief-generate-failed"),
    ).toHaveTextContent("BRIEF DID NOT GENERATE · HTTP 500");
    expectHandledOrder(section, 6);
  });

  it("keeps the line beside the same-day success receipt", async () => {
    latest = dayOneBrief();
    generated = dayOneBrief();
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-brief");
    const generateButton = await screen.findByTestId("arrival-brief-generate");
    await act(async () => {
      generateButton.click();
    });
    expect(
      await screen.findByTestId("arrival-brief-receipt"),
    ).toHaveTextContent("Brief ready · 6 items");
    expectHandledOrder(section, 6);
  });
});
