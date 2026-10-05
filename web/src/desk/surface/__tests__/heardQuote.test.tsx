/* HeardQuote (first run C1) — his words at the display step, the facts of
   the take in one token, the verbs under them. */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "../../../components/signal/Signal";
import { HeardQuote, heardDuration, heardFacts, heardWordCount } from "..";

describe("HeardQuote", () => {
  it("plays his words back in quotes with HEARD and one facts token", () => {
    render(
      <HeardQuote
        text=" Send the cutover plan to Priya before Friday. "
        seconds={4.2}
        at="14:03"
        local
        verbs={<Button dense>Again</Button>}
      />,
    );
    const quote = screen.getByTestId("heard-quote");
    expect(quote.querySelector("blockquote")?.textContent).toBe(
      "“Send the cutover plan to Priya before Friday.”",
    );
    expect(quote.getAttribute("data-size")).toBe("display");
    expect(screen.getByRole("status", { name: "HEARD" })).toBeTruthy();
    expect(screen.getByText("8 WORDS · 0:04 · 14:03")).toBeTruthy();
    expect(screen.getByText("LOCAL")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Again" })).toBeTruthy();
  });

  it("says no zero and no unknown fact", () => {
    expect(heardFacts({ text: "", seconds: 0, at: null })).toBe("");
    expect(heardFacts({ text: "Hello", seconds: null, at: "09:00" })).toBe("1 WORD · 09:00");
    expect(heardWordCount("  ")).toBe(0);
    expect(heardDuration(72.4)).toBe("1:12");
  });

  it("has a primary echo size", () => {
    render(<HeardQuote text="Hi" size="primary" />);
    expect(screen.getByTestId("heard-quote").getAttribute("data-size")).toBe("primary");
    expect(screen.queryByText("LOCAL")).toBeNull();
  });
});
