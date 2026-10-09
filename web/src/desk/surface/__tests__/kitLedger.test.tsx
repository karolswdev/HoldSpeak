// Phase 16 — the interior kit: Ledger + LedgerRow (SurfaceLedger restyled as
// the sunken paper well; SurfaceLedgerRow's `kind` plate and `meta`). The
// 52 px lead slot and `wrap` stay; hover verbs stay in `trailing`.
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { SurfaceLedger, SurfaceLedgerRow } from "..";
import { Button } from "../../../components/signal/Signal";

describe("Ledger + LedgerRow (Phase 16 kit)", () => {
  it("a kit ledger draws no head (its count is on the Section); its rows wear the kind plate and the meta", () => {
    const { container } = render(
      <SurfaceLedger label="Sources" cols="kit">
        <ul className="surface-ledger-rows">
          <SurfaceLedgerRow kind="GH" kindTitle="GITHUB" primary="karolswdev/payments-ledger" meta="CHECKED 10 MIN AGO" metaTone="ok" />
          <SurfaceLedgerRow kind="MTG" primary="Meetings" meta="CHECKED 09:02"
            trailing={<Button dense variant="ghost">Pause</Button>} />
        </ul>
      </SurfaceLedger>,
    );
    expect(container.querySelector(".surface-ledger-head")).toBeNull();
    expect(screen.getByRole("group", { name: "Sources" }).className).toBe("surface-ledger");
    const rows = container.querySelectorAll(".surface-ledger-line");
    const plate = rows[0].querySelector(".surface-ledger-lead [data-testid='kit-kind']") as HTMLElement;
    expect(plate.textContent).toBe("GH");
    expect(plate.getAttribute("title")).toBe("GITHUB");
    expect(rows[0].querySelector(".surface-ledger-meta")?.getAttribute("data-tone")).toBe("ok");
    // name, then meta, then the verbs (the row's own grid slot)
    expect([...rows[1].children].map((c) => c.className)).toEqual([
      "surface-ledger-lead", "surface-ledger-primary", "surface-ledger-meta", "surface-ledger-trailing",
    ]);
    expect(within(rows[1] as HTMLElement).getByRole("button", { name: "Pause" })).toBeTruthy();
  });

  it("a given `lead` wins over `kind`; a machine ledger keeps its count head", () => {
    const { container } = render(
      <SurfaceLedger count="TODAY 2">
        <ul className="surface-ledger-rows">
          <SurfaceLedgerRow lead="09:14" kind="DEC" primary="x" />
        </ul>
      </SurfaceLedger>,
    );
    expect(container.querySelector(".surface-ledger-count")?.textContent).toBe("TODAY 2");
    expect(container.querySelector("[data-testid='kit-kind']")).toBeNull();
    expect(container.querySelector(".surface-ledger-lead")?.textContent).toBe("09:14");
  });

  it("the well is sunken paper with an ink border; a row's name is sans 15/500; the hover tints at 12 %", () => {
    const css = readFileSync(resolve(__dirname, "../surface.css"), "utf8");
    expect(css).toMatch(/\.surface-ledger \{[^}]*background: var\(--wb-well, var\(--wb-paper\)\);[^}]*border: 1px solid var\(--wb-ink\);[^}]*box-shadow: var\(--wb-sunken\);/);
    expect(css).toMatch(/\.surface-ledger-primary \{[^}]*font: 500 15px \/ 1\.3 var\(--font-sans\);/);
    expect(css).toMatch(/\.surface-ledger-line:hover \{[^}]*12%/);
    const kit = readFileSync(resolve(__dirname, "../kit.css"), "utf8");
    expect(kit).toMatch(/\.kit-kind \{[^}]*width: 44px;[^}]*background: var\(--wb-steel\);[^}]*box-shadow: var\(--wb-raised-soft\);[^}]*font: 700 10px/);
  });
});
