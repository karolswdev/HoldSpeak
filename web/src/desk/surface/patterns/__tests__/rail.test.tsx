import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Rail, type RailItem } from "../Rail";
import css from "../rail.css?raw";
import { BackSlotContext, type WindowBack } from "../../back";

const items: RailItem[] = [
  { id: "first", label: "Alpha", count: 0 },
  { id: "held", label: "Disabled", disabled: true },
  { id: "second", label: "Beta", count: 3, state: "Waits on you", spine: { tone: "brass" } },
  { id: "third", label: "Gamma" },
];
afterEach(cleanup);
describe("Rail", () => {
  it("marks the picked item, omits zero and says the state", () => {
    render(<Rail label="Work" items={items} picked="second" onPick={() => {}} />);
    const picked = screen.getByRole("button", { name: "Beta Waits on you 3" });
    expect(picked.getAttribute("aria-current")).toBe("true");
    expect(picked.tabIndex).toBe(0);
    expect(screen.queryByText("0")).toBeNull();
    expect(picked.querySelector('.surface-spine-part[data-tone="brass"]')).toBeTruthy();
  });
  it("roves across groups, skips disabled rows and activates only on a press", () => {
    const pick = vi.fn();
    render(<Rail label="Work" groups={[{ id: "active", label: "Active", items: items.slice(0, 2) }, { id: "done", label: "Done", items: items.slice(2) }]} picked="first" onPick={pick} />);
    const first = screen.getByRole("button", { name: "Alpha" });
    first.focus();
    fireEvent.keyDown(first, { key: "ArrowDown" });
    expect(document.activeElement?.textContent).toContain("Beta");
    fireEvent.keyDown(document.activeElement!, { key: "End" });
    expect(document.activeElement?.textContent).toBe("Gamma");
    fireEvent.keyDown(document.activeElement!, { key: "Home" });
    expect(document.activeElement).toBe(first);
    fireEvent.keyDown(first, { key: "g" });
    expect(document.activeElement?.textContent).toBe("Gamma");
    expect(pick).not.toHaveBeenCalled();
    fireEvent.click(document.activeElement!);
    expect(pick).toHaveBeenCalledWith("third");
  });
  it("uses one 393 posture: pick opens the pane and Back restores the list", () => {
    render(<div className="surface-rail-layout"><Rail label="Work" items={items} picked="first" onPick={() => {}} /><div>Pane</div></div>);
    const rail = screen.getByRole("navigation");
    expect(rail.classList.contains("surface-rail--fold")).toBe(true);
    expect(rail.hasAttribute("data-pane-open")).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Alpha" }));
    expect(rail.hasAttribute("data-pane-open")).toBe(true);
    fireEvent.click(document.querySelector<HTMLButtonElement>(".surface-rail-back button")!);
    expect(rail.hasAttribute("data-pane-open")).toBe(false);
    expect(css).toContain("@container surface (max-width: 520px)");
    expect(css).toContain("min-height: 48px");
  });
  it("gives a hosted phone one title-bar Back that returns to the rail", () => {
    const matchMedia = window.matchMedia;
    window.matchMedia = (() => ({ matches: true, addEventListener() {}, removeEventListener() {} })) as unknown as typeof window.matchMedia;
    const publish = vi.fn();
    try {
      render(<BackSlotContext.Provider value={publish}><Rail label="Work" items={items} picked="first" onPick={() => {}} /></BackSlotContext.Provider>);
      fireEvent.click(screen.getByRole("button", { name: "Alpha" }));
      const back = publish.mock.calls.at(-1)?.[0] as WindowBack;
      expect(back.testId).toBe("rail-back");
      expect(document.querySelector(".surface-rail-back")).toBeNull();
      act(() => back.onBack());
      expect(screen.getByRole("navigation").hasAttribute("data-pane-open")).toBe(false);
    } finally {
      window.matchMedia = matchMedia;
    }
  });

});
