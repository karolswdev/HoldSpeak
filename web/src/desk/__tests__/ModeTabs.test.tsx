/** HS-153-01 -- ModeTabs component tests.
 *
 * Tests: renders tabs from cached modes, active tab is marked,
 * clicking selects/deselects, arrow-key navigation works,
 * disabled state. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ModeTabs, resetModeCache, type ModeTabItem } from "../components/ModeTabs";
import type { ThreadMode } from "../threads";

// Stub fetch to return four seed modes.
const SEED_MODES: ModeTabItem[] = [
  { id: "hs-seed-mode-desk", name: "Desk", avatar: "#6B7280" },
  { id: "hs-seed-mode-chase", name: "Chase", avatar: "#2563EB" },
  { id: "hs-seed-mode-draft", name: "Draft", avatar: "#9333EA" },
  { id: "hs-seed-mode-plan", name: "Plan", avatar: "#059669" },
];

beforeEach(() => {
  resetModeCache();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: () => Promise.resolve({ recipes: SEED_MODES }),
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
  resetModeCache();
});

describe("ModeTabs", () => {
  it("renders four seed tabs", async () => {
    const onSelect = vi.fn();
    render(<ModeTabs activeMode={null} onSelect={onSelect} />);
    await waitFor(() => {
      expect(screen.getByTestId("mode-tab-desk")).toBeTruthy();
    });
    expect(screen.getByTestId("mode-tab-chase")).toBeTruthy();
    expect(screen.getByTestId("mode-tab-draft")).toBeTruthy();
    expect(screen.getByTestId("mode-tab-plan")).toBeTruthy();
  });

  it("marks the active tab with aria-selected", async () => {
    const activeMode: ThreadMode = { id: "hs-seed-mode-chase", name: "Chase", avatar: "#2563EB" };
    render(<ModeTabs activeMode={activeMode} onSelect={() => {}} />);
    await waitFor(() => {
      expect(screen.getByTestId("mode-tab-chase")).toBeTruthy();
    });
    const chaseTab = screen.getByTestId("mode-tab-chase");
    const deskTab = screen.getByTestId("mode-tab-desk");
    expect(chaseTab.getAttribute("aria-selected")).toBe("true");
    expect(deskTab.getAttribute("aria-selected")).toBe("false");
  });

  it("calls onSelect with recipe id on click", async () => {
    const onSelect = vi.fn();
    render(<ModeTabs activeMode={null} onSelect={onSelect} />);
    await waitFor(() => {
      expect(screen.getByTestId("mode-tab-draft")).toBeTruthy();
    });
    fireEvent.click(screen.getByTestId("mode-tab-draft"));
    expect(onSelect).toHaveBeenCalledWith("hs-seed-mode-draft");
  });

  it("calls onSelect with empty string to unbind active mode", async () => {
    const activeMode: ThreadMode = { id: "hs-seed-mode-draft", name: "Draft", avatar: "#9333EA" };
    const onSelect = vi.fn();
    render(<ModeTabs activeMode={activeMode} onSelect={onSelect} />);
    await waitFor(() => {
      expect(screen.getByTestId("mode-tab-draft")).toBeTruthy();
    });
    fireEvent.click(screen.getByTestId("mode-tab-draft"));
    // Clicking the active tab unbinds
    expect(onSelect).toHaveBeenCalledWith("");
  });

  it("arrow keys move focus between tabs", async () => {
    render(<ModeTabs activeMode={null} onSelect={() => {}} />);
    await waitFor(() => {
      expect(screen.getByTestId("mode-tab-desk")).toBeTruthy();
    });
    const container = screen.getByTestId("mode-tabs");
    const deskTab = screen.getByTestId("mode-tab-desk");
    deskTab.focus();
    fireEvent.keyDown(container, { key: "ArrowRight" });
    // After ArrowRight from Desk, Chase should be focused
    expect(document.activeElement?.getAttribute("data-testid")).toBe("mode-tab-chase");
  });

  it("disabled tabs cannot be clicked", async () => {
    const onSelect = vi.fn();
    render(<ModeTabs activeMode={null} onSelect={onSelect} disabled />);
    await waitFor(() => {
      expect(screen.getByTestId("mode-tab-desk")).toBeTruthy();
    });
    fireEvent.click(screen.getByTestId("mode-tab-desk"));
    // The button is disabled, so onSelect should not be called
    // (HTML disabled buttons don't fire click events)
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("has role=tablist on the container", async () => {
    render(<ModeTabs activeMode={null} onSelect={() => {}} />);
    await waitFor(() => {
      expect(screen.getByTestId("mode-tabs")).toBeTruthy();
    });
    expect(screen.getByTestId("mode-tabs").getAttribute("role")).toBe("tablist");
  });

  it("each tab has role=tab", async () => {
    render(<ModeTabs activeMode={null} onSelect={() => {}} />);
    await waitFor(() => {
      expect(screen.getByTestId("mode-tab-desk")).toBeTruthy();
    });
    const tabs = screen.getByTestId("mode-tabs").querySelectorAll("[role=tab]");
    expect(tabs.length).toBe(4);
  });

  it("colored dot has the avatar color", async () => {
    render(<ModeTabs activeMode={null} onSelect={() => {}} />);
    await waitFor(() => {
      expect(screen.getByTestId("mode-tab-chase")).toBeTruthy();
    });
    const dot = screen.getByTestId("mode-tab-chase").querySelector(".thread-mode-dot");
    expect(dot).toBeTruthy();
    expect((dot as HTMLElement).style.backgroundColor).toContain("37, 99, 235");
  });
});
