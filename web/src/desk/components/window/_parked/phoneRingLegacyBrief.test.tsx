// Parked by Betterment daily D5 (Brief and The week retired into Today): the
// "restored legacy Chair Brief" depth cases from
// web/src/desk/components/window/phoneRing.test.tsx. A restored chair:brief
// row now closes and opens Today in its place (compositor/hubWindows.ts), so
// no Chair Brief pane is ever drawn to send back. Not run (vitest excludes
// _parked).

/*
  it("depth on a restored legacy Chair Brief restores Today before other ring panes", () => {
    openDeskWindow("surface-meetings", "Meetings");
    openDeskWindow("pullout:intelligence:desk", "Today");
    act(() => openChairWindow("chair:brief"));
    expect(phoneCurrent()).toBe("chair:brief");
    expect(phoneRing().map((entry) => entry.id)).not.toContain("chair:brief");
    expect(useDesk.getState().panelMin).toContain("pullout:intelligence:desk");

    act(() => sendWindowToBack("chair:brief"));

    expect(phoneCurrent()).toBe("pullout:intelligence:desk");
    expect(useDesk.getState().panelMin).not.toContain("pullout:intelligence:desk");
    expect(useDesk.getState().panelOrder.at(-1)).toBe("pullout:intelligence:desk");
    expect(useDesk.getState().panelMin).toContain("surface-meetings");
    expect(useChairWindows.getState().closed["chair:brief"]).toBe(false);
  });

  it("depth on a restored legacy Chair Brief uses the first ring pane when Today is absent", () => {
    openDeskWindow("surface-meetings", "Meetings");
    act(() => openChairWindow("chair:brief"));
    expect(phoneCurrent()).toBe("chair:brief");

    act(() => sendWindowToBack("chair:brief"));

    expect(phoneCurrent()).toBe("chair:needs");
    expect(useChairWindows.getState().closed["chair:brief"]).toBe(false);
    expect(useDesk.getState().panelMin).toContain("surface-meetings");
  });

  it("depth on a restored legacy Chair Brief leaves it open when the canonical ring is empty", () => {
    useChairWindows.setState({ closed: { "chair:needs": true, "chair:week": true, "chair:capture": true } });
    act(() => openChairWindow("chair:brief"));
    expect(phoneRing()).toEqual([]);

    act(() => sendWindowToBack("chair:brief"));

    expect(phoneCurrent()).toBe("chair:brief");
    expect(useChairWindows.getState().closed["chair:brief"]).toBe(false);
    expect(phoneRing()).toEqual([]);
  });
*/
