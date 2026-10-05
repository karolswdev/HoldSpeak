// Memory on the Desk (canvas section 2, option B, ratified 2026-10-05): the
// StandingPage species and the standing pages of one scope. Fresh: the
// question, the numbered sentences with refs that open, BUILT. Stale: the
// warn border and `STALE · N NEW SOURCES`. A withheld sentence is simply
// not drawn: no gap, no counter, no marker. No page: the section is absent.
// No verb rewrites a page.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { StandingPage } from "../surface";
import {
  StandingPagesSection,
  builtToken,
  modelToken,
  pageTitle,
  useStandingPages,
  type StandingPageWire,
} from "../standingPages";

vi.mock("../../lib/api", async (original) => ({
  ...await original<typeof import("../../lib/api")>(),
  apiFetch: vi.fn(),
}));

const NOW = new Date(2026, 9, 5, 14, 18);
const iso = (d: Date) => d.toISOString();

const DECIDED: StandingPageWire = {
  slug: "what-we-decided", question: "What did we decide?",
  sentences: [
    { text: "The cutover is on 17 October, after the freeze.", refs: [{ ref: "decision:d-1", token: "DEC 10-01", opens: true }] },
    { text: "The old cluster stays read-only for 14 days.", refs: [{ ref: "meeting:m-1", token: "MTG 10-01 · 14:25", opens: true }] },
  ],
  built_at: iso(new Date(2026, 9, 5, 9, 12)), stale: false, new_sources: 0,
  model: "qwen3.8-27b", boundary: "private_network",
};
const CHANGED: StandingPageWire = {
  slug: "what-changed-this-week", question: "What changed this week?",
  sentences: [{ text: "Priya took the rollback runbook.", refs: [{ ref: "action_item:a-1", token: "CMT 10-01", opens: true }] }],
  built_at: iso(new Date(2026, 9, 5, 8, 2)), stale: true, new_sources: 3,
  model: "qwen3.8-27b", boundary: "private_network",
};

describe("StandingPage", () => {
  it("fresh: the question, the numbered sentences, refs that open, BUILT; no stale chip, no warn border", () => {
    const opened: string[] = [];
    render(<StandingPage title="What did we decide" sentences={DECIDED.sentences} built="BUILT 09:12"
      onOpenRef={(r) => opened.push(r)} />);
    const page = screen.getByTestId("standing-page");
    expect(page.hasAttribute("data-stale")).toBe(false);
    expect(within(page).getByRole("heading", { level: 4 }).textContent).toBe("What did we decide");
    expect(screen.getByTestId("standing-page-built").textContent).toBe("BUILT 09:12");
    expect(screen.queryByTestId("standing-page-stale")).toBeNull();
    const items = screen.getAllByTestId("standing-sentence");
    expect(items.map((li) => li.tagName)).toEqual(["LI", "LI"]);
    expect(items[0].closest("ol")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Open the source: MTG 10-01 · 14:25" }));
    expect(opened).toEqual(["meeting:m-1"]);
    // No verb rewrites a page: the only buttons are the refs.
    expect(screen.getAllByRole("button").map((b) => b.textContent)).toEqual(["DEC 10-01", "MTG 10-01 · 14:25"]);
  });

  it("stale: the warn border and STALE · 3 NEW SOURCES", () => {
    render(<StandingPage title="What changed this week" sentences={CHANGED.sentences} built="BUILT MON 08:02"
      stale newSources={3} onOpenRef={() => {}} />);
    expect(screen.getByTestId("standing-page").hasAttribute("data-stale")).toBe(true);
    expect(screen.getByTestId("standing-page-stale").textContent).toContain("STALE · 3 NEW SOURCES");
  });

  it("stale with no source count: STALE alone, never a counter of zero", () => {
    render(<StandingPage title="What changed this week" sentences={CHANGED.sentences} built="BUILT 08:02"
      stale newSources={0} onOpenRef={() => {}} />);
    const chip = screen.getByTestId("standing-page-stale").textContent ?? "";
    expect(chip).toContain("STALE");
    expect(chip).not.toMatch(/\b0\b/);
  });

  it("a page with no sentence draws nothing", () => {
    const { container } = render(<StandingPage title="Risks and disputes" sentences={[]} built="BUILT 09:12" onOpenRef={() => {}} />);
    expect(container.innerHTML).toBe("");
  });
});

describe("StandingPagesSection", () => {
  it("draws the scope's pages under STANDING PAGES with the engine token", () => {
    render(<StandingPagesSection pages={[DECIDED, CHANGED]} now={NOW} onOpenRef={() => {}} />);
    expect(screen.getByRole("heading", { level: 3 }).textContent).toBe("STANDING PAGES 2");
    expect(screen.getByTestId("standing-pages-model").textContent).toBe("PAGES BY QWEN3.8-27B · LAN");
    expect(screen.getAllByTestId("standing-page").map((p) => p.getAttribute("aria-label"))).toEqual(
      ["What did we decide", "What changed this week"],
    );
    expect(screen.getAllByTestId("standing-page-built").map((b) => b.textContent)).toEqual(
      ["BUILT 09:12", "BUILT 08:02"],
    );
  });

  it("a withheld sentence is simply not drawn: no gap, no counter, no marker", () => {
    // The wire may carry a count of withheld sentences; the face never draws it.
    const wire = { ...DECIDED, withheld: 2 } as StandingPageWire;
    render(<StandingPagesSection pages={[wire]} now={NOW} onOpenRef={() => {}} />);
    const page = screen.getByTestId("standing-page");
    expect(within(page).getAllByTestId("standing-sentence")).toHaveLength(2);
    const section = screen.getByTestId("standing-pages");
    expect(section.textContent).not.toMatch(/withheld|hidden|more|…/i);
    // Nothing draws the count: the only digits are the caption's page count,
    // the BUILT clock and the ref tokens.
    const drawn = (section.textContent ?? "")
      .replace("STANDING PAGES 1", "").replace("QWEN3.8-27B", "").replace(/BUILT \d\d:\d\d/, "")
      .replace(/DEC 10-01|MTG 10-01 · 14:25|read-only for 14 days|17 October/g, "");
    expect(drawn).not.toMatch(/\d/);
    expect(section.querySelectorAll("li")).toHaveLength(2);
  });

  it("no page: the section is absent", () => {
    const { container } = render(<StandingPagesSection pages={[]} onOpenRef={() => {}} />);
    expect(container.innerHTML).toBe("");
  });

  it("the tokens", () => {
    expect(builtToken(DECIDED.built_at, NOW)).toBe("BUILT 09:12");
    expect(builtToken(iso(new Date(2026, 9, 3, 8, 2)), NOW)).toBe("BUILT SAT 08:02");
    expect(builtToken(iso(new Date(2026, 8, 28, 8, 2)), NOW)).toBe("BUILT 09-28");
    expect(pageTitle({ slug: "what-i-owe", question: "What do I owe?" })).toBe("What I owe");
    expect(pageTitle({ slug: "new-slug", question: "Anything new?" })).toBe("Anything new");
    expect(modelToken([{ ...DECIDED, model: "pages", boundary: "local" }])).toBe("PAGES BY PAGES · THIS DEVICE");
  });
});

function Probe({ scope, projectId }: { scope: "desk" | "project"; projectId?: string | null }) {
  const pages = useStandingPages(scope, projectId);
  return <StandingPagesSection pages={pages} now={NOW} onOpenRef={() => {}} />;
}

describe("useStandingPages", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset());

  it("reads one scope: the project's pages by its id, the desk's by scope=desk", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ pages: [DECIDED] });
    render(<Probe scope="project" projectId="atlas" />);
    await screen.findByTestId("standing-page");
    expect(vi.mocked(apiFetch).mock.calls[0][0]).toBe("/api/memory/pages?project_id=atlas");
    vi.mocked(apiFetch).mockClear();
    render(<Probe scope="desk" />);
    await waitFor(() => expect(vi.mocked(apiFetch).mock.calls[0]?.[0]).toBe("/api/memory/pages?scope=desk"));
  });

  it("no engine (no page) and a failed read are both absent, never an error", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce({ pages: [] });
    const first = render(<Probe scope="project" projectId="atlas" />);
    await waitFor(() => expect(apiFetch).toHaveBeenCalled());
    expect(first.container.innerHTML).toBe("");
    first.unmount();
    vi.mocked(apiFetch).mockRejectedValueOnce(new Error("500"));
    const second = render(<Probe scope="desk" />);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(2));
    expect(second.container.innerHTML).toBe("");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("no project: no read at all", () => {
    render(<Probe scope="project" projectId={null} />);
    expect(apiFetch).not.toHaveBeenCalled();
  });
});
