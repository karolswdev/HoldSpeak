/* First run, option A "One screen" (owner ratified 2026-10-05): the lit
   state on ChoiceCardShell. ReadyStrip and StartVerb are parked (2026-11-08,
   no face draws them). */
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChoiceCardShell } from "..";


describe("ChoiceCardShell lit", () => {
  it("stamps data-lit only when lit", () => {
    const { rerender } = render(<ChoiceCardShell data-testid="card" label="Calendar" lit />);
    expect(screen.getByTestId("card").getAttribute("data-lit")).toBe("true");
    rerender(<ChoiceCardShell data-testid="card" label="Calendar" />);
    expect(screen.getByTestId("card").getAttribute("data-lit")).toBeNull();
  });
});
