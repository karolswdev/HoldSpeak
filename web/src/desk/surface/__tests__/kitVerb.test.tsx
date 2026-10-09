// Phase 16 — the interior kit: Verb (the library Button as a raised Steel
// plate with ink; primary the selection blue, danger the Workbench red, both
// with paper; pressed it sinks). Here: every plated variant IS the `.btn`
// plate. The heights are RENDERED in a real browser, not read from the
// stylesheet: tests/e2e/test_p16_kit_verb_glass.py (28 px at 1440, a 44 px
// target at 393).
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "../../../components/signal/Signal";

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
});
