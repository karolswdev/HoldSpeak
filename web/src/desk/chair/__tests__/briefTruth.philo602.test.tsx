// PHILO-6-02 — the brief's truth: the rendered links of the fences.
//
// The fixture is the REAL producer's brief (tests/unit/test_philo6_02_brief_truth.py
// writes it and holds it equal to the wire): the hub's clock is in
// Etc/GMT+11 (generated_at carries -11:00, the hub's own label reads 07:19),
// and it holds a real summary run call, a real observed failure, a THIS WEEK
// item and one shelved row.
//
// (a) ONE clock: the browser here is in Europe/Warsaw (UTC+2), a different
//     zone from the hub. The caption and the receipt must tell ONE time, the
//     producer's instant in the viewer's zone. Before the repair the caption
//     read the hub's 07:19 and the receipt the browser's 8:19 PM.
// (b) Each count equals what its label claims: the head counts the Arrival
//     rows still waiting (decisions, changed, broke, waiting; not shelved;
//     THIS WEEK outside); the receipt counts the generated snapshot. Before
//     the repair the raw `Service.method` rows were waiting but hidden, so
//     the head claimed fewer than were waiting.
const tz = vi.hoisted(() => {
  const previous = process.env.TZ;
  process.env.TZ = "Europe/Warsaw";
  return { previous };
});

import { render, screen, within } from "@testing-library/react";
import { afterAll, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));

import brief from "./fixtures/philo6/brief-truth.json";
import { ChairHome } from "../ChairHome";

const STAMP = /[A-Z]{3} \d{2} \d{2}:\d{2}|\d{1,2}:\d{2}\s?[AP]M/;
const RAW = /[A-Z][A-Za-z]*(?:Service|Manager|Handler|Provider)\.[a-z_]+/;

type Row = { id: string; text: string };
const sections = brief.sections as unknown as Record<string, Row[]>;
const shelf = brief.shelf as Record<string, string>;
const ARRIVAL = ["decisions", "changed", "broke", "waiting"];
const waiting = ARRIVAL.flatMap((name) => sections[name] ?? []).filter((row) => !shelf[row.id]);
const snapshot = Object.values(sections).reduce((total, rows) => total + rows.length, 0);

describe("PHILO-6-02 the brief tells one time and counts what its labels say", () => {
  afterAll(() => {
    if (tz.previous === undefined) delete process.env.TZ;
    else process.env.TZ = tz.previous;
  });

  beforeEach(() => {
    mocks.apiFetch.mockReset();
    mocks.apiFetch.mockImplementation(async (path: string) =>
      String(path) === "/api/brief/latest" ? brief : null,
    );
  });

  it("the fixture is the cross-zone case: the hub's own label is not the viewer's time", () => {
    expect(brief.generated_at.endsWith("-11:00")).toBe(true);
    expect(brief.generated_label).toBe("GENERATED SEP 25 07:19");
    expect(new Date(brief.generated_at).getHours()).toBe(20);
  });

  it("(a) the caption and the receipt tell ONE time: the producer's instant in the viewer's zone", async () => {
    render(<ChairHome />);
    const receipt = await screen.findByTestId("arrival-brief-receipt");
    const caption = screen.getByTestId("arrival-brief-date");
    const captionTime = caption.textContent?.match(STAMP)?.[0];
    const receiptTime = receipt.textContent?.match(STAMP)?.[0];
    expect(receiptTime).toBe(captionTime);
    expect(captionTime).toBe("SEP 25 20:19");
  });

  it("(b) the head counts the rows waiting; the receipt counts the generated snapshot", async () => {
    render(<ChairHome />);
    const receipt = await screen.findByTestId("arrival-brief-receipt");
    // The snapshot: every row the producer generated, THIS WEEK and the
    // shelved row included. The historical snapshot is not rewritten.
    expect(receipt.textContent).toContain(`Brief ready · ${snapshot} items`);
    // The head: the Arrival rows still waiting, nothing hidden.
    const section = screen.getByTestId("arrival-brief");
    expect(section.textContent).toContain(`BRIEF · ${waiting.length} THINGS WAITING`);
    const shown = within(section).getAllByTestId("arrival-brief-row").length;
    const folded = Number(
      within(section).queryByTestId("arrival-brief-more")?.textContent?.match(/^(\d+) more$/)?.[1] ?? 0,
    );
    expect(shown + folded).toBe(waiting.length);
    // Distinct meanings, never conflated: THIS WEEK and the shelved row.
    expect(snapshot - waiting.length).toBe(
      (sections.this_week?.length ?? 0) + Object.keys(shelf).length,
    );
  });

  it("(c) no raw Service.method name renders on the Arrival", async () => {
    const { container } = render(<ChairHome />);
    await screen.findByTestId("arrival-brief-receipt");
    expect(container.textContent ?? "").not.toMatch(RAW);
    for (const row of waiting) expect(row.text).not.toMatch(RAW);
  });
});
