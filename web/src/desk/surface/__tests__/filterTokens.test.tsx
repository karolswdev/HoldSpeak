// HS-176-03 — the promoted FilterTokens species (ruling R6).
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FilterTokens } from "../FilterTokens";

const OPTIONS = [
  { value: "", label: "ALL" },
  { value: "dictation", label: "DICTATION" },
  { value: "browser", label: "BROWSER" },
  { value: "hotkey", label: "HOTKEY" },
];

describe("FilterTokens", () => {
  it("renders every token as a library Button inside a named group", () => {
    render(
      <FilterTokens
        options={OPTIONS}
        value=""
        onChange={() => undefined}
        label="Source filter"
      />,
    );
    const group = screen.getByRole("group", { name: "Source filter" });
    expect(group).toBeInTheDocument();
    for (const option of OPTIONS)
      expect(screen.getByRole("button", { name: option.label })).toBeInTheDocument();
    // UX-CANON A.1: every verb is the library Button — no raw <button>.
    for (const button of screen.getAllByRole("button"))
      expect(button.className).toContain("btn");
  });

  it("marks exactly one token active with aria-pressed and data-filter-active", () => {
    render(
      <FilterTokens
        options={OPTIONS}
        value="dictation"
        onChange={() => undefined}
        label="Source filter"
      />,
    );
    const active = screen.getByRole("button", { name: "DICTATION" });
    expect(active).toHaveAttribute("aria-pressed", "true");
    expect(active).toHaveAttribute("data-filter-active");
    expect(active.className).toContain("btn--primary");

    const resting = screen.getByRole("button", { name: "ALL" });
    expect(resting).toHaveAttribute("aria-pressed", "false");
    expect(resting).not.toHaveAttribute("data-filter-active");
    expect(resting.className).toContain("btn--ghost");

    expect(
      screen.getAllByRole("button").filter((b) => b.hasAttribute("data-filter-active")),
    ).toHaveLength(1);
  });

  it("hands the tapped value back", () => {
    const onChange = vi.fn();
    render(
      <FilterTokens
        options={OPTIONS}
        value=""
        onChange={onChange}
        label="Source filter"
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "HOTKEY" }));
    expect(onChange).toHaveBeenCalledWith("hotkey");
  });

  it("has NO sparse rule: it never returns null", () => {
    // LedgerFilterBar returns null below SPARSE_THRESHOLD (sparse.ts:4); this
    // species must render over an empty stream so the view can be widened.
    const { container, rerender } = render(
      <FilterTokens
        options={OPTIONS}
        value=""
        onChange={() => undefined}
        label="Source filter"
      />,
    );
    expect(container.querySelector(".surface-filter-tokens")).not.toBeNull();
    rerender(
      <FilterTokens
        options={[]}
        value=""
        onChange={() => undefined}
        label="Source filter"
      />,
    );
    expect(container.querySelector(".surface-filter-tokens")).not.toBeNull();
  });

  it("carries no count", () => {
    const { container } = render(
      <FilterTokens
        options={OPTIONS}
        value=""
        onChange={() => undefined}
        label="Source filter"
      />,
    );
    // matchCount/total would be a second count on the face (A.7/A.8).
    expect(container.textContent).toBe("ALLDICTATIONBROWSERHOTKEY");
  });
});
