// Phase 16 — the interior kit: Verb (the library Button as a raised Steel
// plate with ink; primary the selection blue, danger the Workbench red, both
// with paper; pressed it sinks; every plated variant the same plate at the
// same height; the 44 px target at the narrow desk stays).
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { Button } from "../../../components/signal/Signal";

const css = readFileSync(resolve(__dirname, "../../../styles/global.css"), "utf8");

describe("Verb (Phase 16 kit)", () => {
  it("every plated variant is the `.btn` plate; chrome stays the strip's", () => {
    render(
      <>
        <Button>Plate</Button>
        <Button variant="ghost" dense>Ghost</Button>
        <Button variant="primary">Send</Button>
        <Button variant="danger">Stop</Button>
        <Button variant="chrome" className="desk-chip">Chip</Button>
      </>,
    );
    for (const name of ["Plate", "Ghost", "Send", "Stop"]) {
      expect(screen.getByRole("button", { name }).className).toMatch(/(^|\s)btn(\s|$)/);
    }
    expect(screen.getByRole("button", { name: "Chip" }).className).not.toMatch(/(^|\s)btn(\s|$)/);
  });

  it("the plate is raised Steel with ink; pressed it sinks", () => {
    expect(css).toMatch(/:where\(\.btn\) \{[^}]*border: 1px solid var\(--wb-ink\);[^}]*background: var\(--wb-steel\);[^}]*box-shadow: var\(--wb-raised\);[^}]*color: var\(--wb-ink\);/);
    expect(css).toMatch(/:where\(\.btn\):active:not\(:disabled\) \{[^}]*box-shadow: var\(--wb-sunken\);/);
    expect(css).toMatch(/:where\(\.btn--secondary\),\n:where\(\.btn--ghost\) \{[^}]*background: var\(--wb-steel\);/);
  });

  it("primary is the selection blue, danger the red, both with paper", () => {
    expect(css).toMatch(/:where\(\.btn--primary, \.btn\.primary\) \{[^}]*background: var\(--wb-sel, var\(--wb-blue\)\);[^}]*color: var\(--wb-paper\);/);
    expect(css).toMatch(/:where\(\.btn\.danger, \.btn--danger\) \{[^}]*background: var\(--wb-rec\);[^}]*color: var\(--wb-paper\);/);
  });

  it("the 44 px target at the narrow desk stays (the halo)", () => {
    expect(css).toMatch(/@media \(max-width: 420px\) \{\s*:where\(\.btn\) \{[^}]*min-inline-size: var\(--desk-button-hit-size\);/);
  });
});
