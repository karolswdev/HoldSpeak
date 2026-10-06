// Memory on the Desk (canvas section 2, option B, ratified 2026-10-05):
// a belief is one more kind of recall card. CURRENT (accented, its old text
// struck through under HISTORY), DISPUTED (a contradicting ref reads
// `AGAINST · MTG 09-29 · 10:05`), SUPERSEDED (dimmed, `SINCE 10-01`); every
// evidence ref is a library Button that opens its window; the Desk memory
// face draws beliefs in their state's section, CURRENT · DISPUTED ·
// SUPERSEDED, and no section of zero.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../../lib/api";
import { BeliefCard } from "../BeliefCard";
import { RecallFace } from "../RecallFace";
import type { BeliefCardData } from "../model";

vi.mock("../../../../lib/api", async (original) => ({
  ...await original<typeof import("../../../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../../../../desk/shell", async (original) => ({
  ...await original<typeof import("../../../../desk/shell")>(),
  openSurfaceOr: vi.fn(),
  openProjectRoom: vi.fn(),
}));
vi.mock("../../../../desk/components/MicButton", () => ({
  MicButton: ({ label }: { label: string }) => <button type="button" className="desk-mic" aria-label={label} />,
}));
vi.mock("../../../../desk/surface/SurfaceFooter", () => ({
  SurfaceFooter: ({ receipt }: { receipt?: React.ReactNode }) => <footer>{receipt}</footer>,
}));

const ATLAS = { id: "atlas", name: "Atlas cutover" };
const CURRENT: BeliefCardData = {
  id: "obs-1", kind: "belief", text: "The Atlas cutover is on 17 October, after the freeze.", state: "current",
  proof_count: 3, source_count: 3, seen: "10-01", since: "", project: ATLAS,
  evidence: [
    { ref: "meeting:m-1001", token: "MTG 10-01 · 14:20", opens: true, against: false },
    { ref: "decision:d-1", token: "DEC 10-01", opens: true, against: false },
    { ref: "note:n-0930", token: "NOTE 09-30", opens: true, against: false },
  ],
  history: [{ at: "10-01", text: "The Atlas cutover is on 10 October.", word: "SUPERSEDED", reason: "freeze moved" }],
};
const DISPUTED: BeliefCardData = {
  id: "obs-2", kind: "belief", text: "Priya owns the rollback plan.", state: "disputed",
  proof_count: 1, source_count: 1, seen: "10-01", since: "", project: ATLAS,
  evidence: [
    { ref: "meeting:m-1001", token: "MTG 10-01 · 14:31", opens: true, against: false },
    { ref: "meeting:m-0929", token: "MTG 09-29 · 10:05", opens: true, against: true },
  ],
  history: [],
};
const SUPERSEDED: BeliefCardData = {
  id: "obs-3", kind: "belief", text: "The Atlas cutover is on 10 October.", state: "superseded",
  proof_count: 2, source_count: 2, seen: "09-24", since: "10-01", project: ATLAS,
  evidence: [{ ref: "meeting:m-0924", token: "MTG 09-24 · 15:00", opens: true, against: false }],
  history: [],
};

describe("BeliefCard", () => {
  it("current: the accented kind, its chips, evidence that opens, and the old text struck through", () => {
    const opened: string[] = [];
    render(<BeliefCard belief={CURRENT} onOpenRef={(r) => opened.push(r)} />);
    const card = screen.getByTestId("recall-belief");
    expect(card.className).toContain("recall-card");
    expect(card.getAttribute("data-state")).toBe("current");
    expect(screen.getByTestId("recall-belief-state").textContent).toBe("CURRENT");
    expect(screen.getByTestId("recall-belief-state").getAttribute("data-tone")).toBe("ok");
    expect(screen.getByText("BELIEF")).toBeTruthy();
    expect(screen.getByText("3 SOURCES")).toBeTruthy();
    expect(screen.getByText("SEEN 10-01")).toBeTruthy();
    const refs = within(screen.getByTestId("recall-belief-evidence")).getAllByTestId("memory-ref");
    expect(refs.map((r) => r.textContent)).toEqual(["MTG 10-01 · 14:20", "DEC 10-01", "NOTE 09-30"]);
    for (const r of refs) expect(r.tagName).toBe("BUTTON");
    fireEvent.click(refs[1]);
    expect(opened).toEqual(["decision:d-1"]);
    // History is open on a current belief; the old text is struck through.
    const old = screen.getByTestId("recall-belief-old");
    expect(old.tagName).toBe("S");
    expect(old.textContent).toBe("The Atlas cutover is on 10 October.");
    expect(screen.getByText("SUPERSEDED · FREEZE MOVED")).toBeTruthy();
    expect(screen.queryByTestId("recall-belief-since")).toBeNull();
  });

  it("disputed: the contradicting ref reads AGAINST in the danger ink and still opens", () => {
    const opened: string[] = [];
    render(<BeliefCard belief={DISPUTED} onOpenRef={(r) => opened.push(r)} />);
    expect(screen.getByTestId("recall-belief-state").textContent).toBe("DISPUTED");
    expect(screen.getByTestId("recall-belief-state").getAttribute("data-tone")).toBe("danger");
    const against = screen.getByRole("button", { name: "Open the source: AGAINST · MTG 09-29 · 10:05" });
    expect(against.getAttribute("data-tone")).toBe("danger");
    fireEvent.click(against);
    expect(opened).toEqual(["meeting:m-0929"]);
    expect(screen.getByText("1 SOURCE")).toBeTruthy();
    expect(screen.queryByTestId("recall-belief-history")).toBeNull();
  });

  it("superseded: SINCE the day it was replaced; a ref with no window is plain text, never a verb", () => {
    render(<BeliefCard belief={{ ...SUPERSEDED, evidence: [
      ...SUPERSEDED.evidence, { ref: "send:s-1", token: "SEND", opens: false, against: false },
    ] }} />);
    expect(screen.getByTestId("recall-belief-since").textContent).toBe("SINCE 10-01");
    expect(screen.getByTestId("recall-belief-state").getAttribute("data-tone")).toBe("warn");
    expect(screen.getByTestId("memory-ref-plain").tagName).toBe("SPAN");
    expect(screen.getAllByTestId("memory-ref")).toHaveLength(1);
  });

  it("SOURCES counts distinct sources, never facts: one note with two facts is 1 SOURCE", () => {
    render(<BeliefCard belief={{ ...CURRENT, proof_count: 2, source_count: 1,
      evidence: [{ ref: "note:n1", token: "NOTE 10-05", opens: true, against: false }] }} />);
    expect(screen.getByText("1 SOURCE")).toBeTruthy();
    expect(screen.queryByText("2 SOURCES")).toBeNull();
  });

  it("no counter of zero: a belief with no live source draws no SOURCES chip", () => {
    render(<BeliefCard belief={{ ...SUPERSEDED, proof_count: 0, source_count: 0, evidence: [] }} />);
    expect(screen.queryByText(/0 SOURCES?/)).toBeNull();
    expect(screen.queryByTestId("recall-belief-evidence")).toBeNull();
  });
});

describe("Desk memory draws beliefs as one more kind of card", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    localStorage.clear();
  });

  function wire(beliefs: BeliefCardData[]) {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/memory/recall")) {
        return {
          query: "cutover", filter: "all", searched_at: "2026-10-05T14:18:00", projects_searched: 2,
          current: [], superseded: [], disputed: [], owed: [], meetings: [], briefs: [], also: [],
          beliefs, remembered: beliefs.length,
        };
      }
      return null;
    });
  }

  it("CURRENT, then DISPUTED, then SUPERSEDED, each with its beliefs", async () => {
    wire([CURRENT, DISPUTED, { ...DISPUTED, id: "obs-4", text: "Marek owns the rollback plan." }, SUPERSEDED]);
    render(<RecallFace initialQuery="cutover" />);
    await screen.findByTestId("recall-results");
    const heads = screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent);
    expect(heads).toEqual(["CURRENT 1", "DISPUTED 2", "SUPERSEDED 1"]);
    expect(screen.getAllByTestId("recall-belief").map((c) => c.getAttribute("data-state"))).toEqual(
      ["current", "disputed", "disputed", "superseded"],
    );
    expect(screen.getByTestId("recall-display").textContent).toBe("4 remembered");
  });

  it("only disputed beliefs: no CURRENT or SUPERSEDED section of zero", async () => {
    wire([DISPUTED]);
    render(<RecallFace initialQuery="rollback" />);
    await screen.findByTestId("recall-results");
    expect(screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent)).toEqual(["DISPUTED 1"]);
  });

  it("a wire with no beliefs key draws the face as before", async () => {
    vi.mocked(apiFetch).mockImplementation(async () => ({
      query: "cutover", filter: "all", searched_at: "2026-10-05T14:18:00", projects_searched: 2,
      current: [], superseded: [], disputed: [], owed: [], meetings: [], briefs: [], also: [], remembered: 0,
    }));
    render(<RecallFace initialQuery="cutover" />);
    await screen.findByTestId("recall-miss");
    expect(screen.queryByTestId("recall-belief")).toBeNull();
  });
});
