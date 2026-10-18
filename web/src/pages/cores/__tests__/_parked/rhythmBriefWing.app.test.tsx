// Parked by Betterment daily D4 (Today is one page): the Brief wing's case
// from web/src/pages/cores/__tests__/rhythm.app.test.tsx. The wing is parked
// in web/src/desk/pullouts/_parked/BriefWing.tsx. Not run.

/*
describe("The Brief detail the Rhythm row names", () => {
  it("shows changed work before THIS WEEK, one period, no headline, counted rows and NEXT inside MEETINGS", async () => {
    // replaces: tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmWeeklyBrief::test_brief_this_week_section
    // (all but the ONE GUTTER check, which measures left edges: real layout)
    hub({ brief: brief(THIS_WEEK) });
    const { container } = render(<BriefView header={<div>Header</div>} />);
    const thisWeek = await screen.findByTestId("brief-this-week");
    const since = screen.getByTestId("brief-since-friday");
    expect(since.compareDocumentPosition(thisWeek) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    expect(container.querySelectorAll(".intelligence-brief-period")).toHaveLength(1);
    expect(container.querySelector(".intelligence-brief-headline")).toBeNull();

    for (const id of ["brief-tw-meetings", "brief-tw-armed", "brief-tw-due"]) {
      const row = screen.getByTestId(id);
      const primary = row.querySelectorAll(".intelligence-brief-tw-primary");
      expect(primary).toHaveLength(1);
      expect(primary[0].textContent?.trim()).toMatch(/^[1-9]\d* /);
    }
    expect(screen.getByTestId("brief-tw-meetings").textContent).toContain("4 MEETINGS");
    const next = within(screen.getByTestId("brief-tw-meetings")).getByTestId("brief-tw-next");
    expect(next.textContent).toContain("NEXT");
    const day = screen.queryByTestId("brief-tw-due-day");
    if (day) expect(day.textContent).toHaveLength(3);

    for (const p of Array.from(container.querySelectorAll(".intelligence-brief-tw-primary, .intelligence-brief-sf-primary"))) {
      expect((p.textContent || "").trim().endsWith(".")).toBe(false);
    }
    for (const kind of screen.queryAllByTestId("brief-sf-kind")) {
      expect(kind.textContent).toBe(kind.textContent?.toUpperCase());
    }
    for (const emblem of screen.queryAllByTestId("brief-source-emblem")) {
      const t = emblem.textContent || "";
      expect(t === t.toUpperCase() && t.length >= 1 && t.length <= 4).toBe(true);
    }
    const clone = container.cloneNode(true) as HTMLElement;
    clone.querySelectorAll(".send-preview-body").forEach((n) => n.remove());
    expect(clone.textContent).not.toMatch(/\d{4}-\d{2}-\d{2}/);
  });
});

*/
