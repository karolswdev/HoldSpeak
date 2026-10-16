/** Thread mode uses the shared measured filter strip and keeps unbind semantics. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ModeTabs, resetModeCache, type ModeTabItem } from "../components/ModeTabs";

const SEED_MODES: ModeTabItem[] = [
  { id: "hs-seed-mode-plan", name: "Plan", avatar: "#059669" },
  { id: "hs-seed-mode-desk", name: "Desk", avatar: "#6B7280" },
  { id: "hs-seed-mode-chase", name: "Chase", avatar: "#2563EB" },
  { id: "hs-seed-mode-draft", name: "Draft", avatar: "#9333EA" },
];
beforeEach(() => {
  resetModeCache();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true, status: 200, headers: { get: () => "application/json" },
    json: () => Promise.resolve({ recipes: SEED_MODES }),
  }));
});
afterEach(() => { vi.unstubAllGlobals(); resetModeCache(); });

describe("ModeTabs", () => {
  it("renders ordered library FilterTokens in a named group", async () => {
    render(<ModeTabs activeMode={null} onSelect={() => {}} />);
    await screen.findByRole("button", { name: "Desk" });
    expect(screen.getByRole("group", { name: "Thread mode" })).toBeTruthy();
    const tokens = screen.getAllByRole("button");
    expect(tokens.map((token) => token.textContent)).toEqual(["Desk", "Chase", "Draft", "Plan"]);
    expect(tokens.every((token) => token.classList.contains("btn--ghost"))).toBe(true);
    expect(tokens.every((token) => token.getAttribute("aria-pressed") === "false")).toBe(true);
  });
  it("leaves modes unselected when the bound recipe is absent", async () => {
    render(<ModeTabs activeMode={{ id: "parked", name: "Parked", avatar: "#666" }} onSelect={() => {}} />);
    await screen.findByRole("button", { name: "Desk" });
    expect(screen.getAllByRole("button").every((token) => token.getAttribute("aria-pressed") === "false")).toBe(true);
  });
  it("marks the active mode and toggles it to unbind", async () => {
    const onSelect = vi.fn();
    render(<ModeTabs activeMode={SEED_MODES[3]} onSelect={onSelect} />);
    const draft = await screen.findByRole("button", { name: "Draft" });
    expect(draft.getAttribute("aria-pressed")).toBe("true");
    expect(draft.classList.contains("btn--secondary")).toBe(true);
    fireEvent.click(draft);
    expect(onSelect).toHaveBeenCalledExactlyOnceWith("");
  });
  it("selects another recipe by id", async () => {
    const onSelect = vi.fn();
    render(<ModeTabs activeMode={null} onSelect={onSelect} />);
    fireEvent.click(await screen.findByRole("button", { name: "Draft" }));
    expect(onSelect).toHaveBeenCalledExactlyOnceWith("hs-seed-mode-draft");
  });
  it("disables every mode while a turn is running", async () => {
    const onSelect = vi.fn();
    render(<ModeTabs activeMode={null} onSelect={onSelect} disabled />);
    const desk = await screen.findByRole("button", { name: "Desk" });
    fireEvent.click(desk);
    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.getAllByRole("button").every((token) => (token as HTMLButtonElement).disabled)).toBe(true);
  });
});
