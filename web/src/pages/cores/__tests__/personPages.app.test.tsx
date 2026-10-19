import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { PersonPages, personPages, type StandingPageWire } from "../../../desk/standingPages";
import WIRE from "../../../test/wire/memory.desk-pages.wire.json";

vi.mock("../../../lib/api", async (original) => ({
  ...await original<typeof import("../../../lib/api")>(),
  apiFetch: vi.fn(),
}));

const ref = { ref: "meeting:one-on-one-mira", token: "1:1 WITH MIRA", opens: true };
const page = (slug: string, question: string, sentences: StandingPageWire["sentences"]): StandingPageWire => ({
  slug,
  question,
  sentences,
  built_at: "2026-10-19T09:10:00Z",
  stale: false,
  new_sources: 0,
  model: "pages",
  boundary: "local",
});

const DESK_PAGES: StandingPageWire[] = [
  page("what-i-owe", "What do I owe?", [
    { text: "You owe Mira feedback on her cutover design doc by Friday.", refs: [ref] },
    { text: "You owe Theo the on-call handbook.", refs: [ref] },
  ]),
  page("what-they-owe-me", "What do others owe me?", [
    { text: "Mira owes you the rollback runbook by Thursday.", refs: [ref] },
    { text: "Theo owes you a status update.", refs: [ref] },
  ]),
  page("what-changed-this-week", "What changed this week?", [
    { text: "Mira moved the cutover review to Friday.", refs: [ref] },
  ]),
];

describe("Q11 person memory pages", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockResolvedValue({ pages: DESK_PAGES });
  });

  it("selects Mira's two pages and removes sentences about other people", () => {
    const selected = personPages(DESK_PAGES, "Mira Kovacs");
    expect(selected.map((p) => p.slug)).toEqual(["person:what-i-owe", "person:what-they-owe-me"]);
    expect(selected.map((p) => p.question)).toEqual(["What I owe Mira", "What Mira owes me"]);
    expect(selected.flatMap((p) => p.sentences).map((s) => s.text)).toEqual([
      "You owe Mira feedback on her cutover design doc by Friday.",
      "Mira owes you the rollback runbook by Thursday.",
    ]);
  });

  it("renders the two answers first, with source links, without an Ask field", async () => {
    render(<PersonPages displayName="Mira Kovacs" onOpenRef={() => {}} />);
    const face = await screen.findByTestId("person-pages");
    expect(within(face).getAllByTestId("standing-page").map((p) => p.getAttribute("aria-label"))).toEqual([
      "What I owe Mira",
      "What Mira owes me",
    ]);
    expect(within(face).getByText("You owe Mira feedback on her cutover design doc by Friday.")).toBeTruthy();
    expect(within(face).getByText("Mira owes you the rollback runbook by Thursday.")).toBeTruthy();
    expect(within(face).queryByRole("searchbox")).toBeNull();
    await waitFor(() => expect(within(face).getAllByTestId("memory-ref")).toHaveLength(2));
  });

  it("keeps the real producer's two directions and opens the cited 1:1", async () => {
    vi.mocked(apiFetch).mockResolvedValue(WIRE.pages);
    const open = vi.fn();
    render(<PersonPages displayName="Mira Kovacs" onOpenRef={open} />);
    const face = await screen.findByTestId("person-pages");
    const answers = within(face).getAllByTestId("standing-page");
    expect(answers[0].textContent).toContain("You owe Mira feedback on the cutover design document, due Friday.");
    expect(answers[1].textContent).toContain("Mira owes you the rollback runbook, due Thursday.");
    expect(answers[1].textContent).not.toContain("You owe Mira");
    fireEvent.click(within(answers[0]).getByTestId("memory-ref"));
    expect(open).toHaveBeenCalledWith("meeting:m-mira-1on1");
  });
});
