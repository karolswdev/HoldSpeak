// Phase 16 — the interior kit: FilterBar (COMPOSITOR.md §11). The filter
// tokens (the FilterTokens species, restyled to the kit cell) on one rail,
// and a trailing verb group at the rail's right. No third filter species.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { FilterBar } from "..";
import { Button } from "../../../components/signal/Signal";

describe("FilterBar (Phase 16 kit)", () => {
  it("is the FilterTokens strip on a rail, with the trailing verbs after the spacer", () => {
    const onChange = vi.fn();
    const { container } = render(
      <FilterBar
        label="Drawer view"
        value="icons"
        onChange={onChange}
        options={[{ value: "icons", label: "Icons" }, { value: "list", label: "List" }]}
        trailing={<><Button dense variant="ghost">Room</Button><Button dense variant="ghost">History</Button></>}
      />,
    );
    const rail = container.querySelector(".kit-filterbar") as HTMLElement;
    const group = within(rail).getByRole("group", { name: "Drawer view" });
    expect(group.className).toContain("surface-filter-tokens");
    expect(within(group).getByRole("button", { name: "Icons" }).getAttribute("aria-pressed")).toBe("true");
    expect(within(group).getByRole("button", { name: "List" }).getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(within(group).getByRole("button", { name: "List" }));
    expect(onChange).toHaveBeenCalledWith("list");
    const kids = [...rail.children].map((c) => c.className);
    expect(kids).toEqual(["surface-filter-tokens", "kit-filterbar-sp", "kit-filterbar-trailing"]);
    expect(within(rail.lastElementChild as HTMLElement).getAllByRole("button").map((b) => b.textContent)).toEqual(["Room", "History"]);
  });

  it("without options the rail holds only its trailing verbs", () => {
    const { container } = render(<FilterBar label="x" trailing={<Button dense>Retry</Button>} />);
    expect(container.querySelector(".surface-filter-tokens")).toBeNull();
    expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy();
  });

  it("the token is the kit cell: Steel at rest; the active one the selection blue, sunken", () => {
    const css = readFileSync(resolve(__dirname, "../filter-tokens.css"), "utf8");
    expect(css).toMatch(/\.surface-filter-token\.btn \{[^}]*background: var\(--wb-steel\)/);
    expect(css).toMatch(/\[data-filter-active\] \{[^}]*box-shadow: var\(--wb-sunken\);[^}]*background: var\(--wb-sel, var\(--wb-blue\)\);[^}]*color: var\(--wb-paper\)/);
  });
});
