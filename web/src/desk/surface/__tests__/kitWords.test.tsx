/** STATECHIP (2026-10-29): the kit draws every state and token in sentence
 *  case. The species send their words through `stateWords`, so a caller that
 *  passes a caps token draws sentence case; acronyms, units and names keep
 *  their spelling; a code token stays exact. */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { stateWords } from "../words";
import { Token } from "../Token";
import { StateChip } from "../patterns/StateChip";
import { FoldGadget } from "../gadgets";
import { StatusStrip } from "../kit";

describe("stateWords", () => {
  it.each([
    ["NOT LAUNCHED", "Not launched"],
    ["NOT ADDED", "Not added"],
    ["WAITING ON BEA · OVERDUE", "Waiting on Bea · Overdue"],
    ["3 MORE", "3 more"],
    ["LAST SEND OCT 28 14:02", "Last send Oct 28 14:02"],
    ["CLONES FROM GITHUB", "Clones from GitHub"],
    ["PR OPEN", "PR open"],
    ["3 PRS", "3 PRs"],
    ["(FAILED),", "(Failed),"],
    ["MLX · 4 GB", "MLX · 4 GB"],
    ["SET · hooks.slack.com", "Set · hooks.slack.com"],
    ["HS-175 OPEN", "HS-175 open"],
    ["SEND_REFUSED", "SEND_REFUSED"],
    ["Prepared", "Prepared"],
    ["CANT CHECK", "Cannot check"],
    ["REFUSED · BY OWNER", "Refused · By owner"],
    ["SUPERSEDED BY DEC 09-07", "Superseded by DEC 09-07"],
    ["DUE DEC 12", "Due Dec 12"],
    ["CLAUDE CODE · HOOKS IN", "Claude Code · Hooks in"],
    // WORDS-LEFTOVERS: the one-letter article in a caps wire is a word too.
    ["NEEDS A DECISION", "Needs a decision"],
    ["WAITING ON A REVIEW", "Waiting on a review"],
    ["WAITS FOR A FREE AGENT", "Waits for a free agent"],
    ["A NEW SESSION", "A new session"],
    ["Plan A", "Plan A"],
  ])("%s → %s", (caps, words) => {
    expect(stateWords(caps)).toBe(words);
  });
});

describe("the kit species", () => {
  it("Token draws its caps words in sentence case; a run after text takes no lead capital", () => {
    render(<Token className="surface-token" data-testid="t">{3}{" PARKED · DUE TODAY"}</Token>);
    expect(screen.getByTestId("t").textContent).toBe("3 parked · Due today");
  });

  it("a code Token keeps its text exact and says so", () => {
    render(<Token code className="surface-token" data-testid="t">{"ABC DEF"}</Token>);
    const token = screen.getByTestId("t");
    expect(token.textContent).toBe("ABC DEF");
    expect(token.hasAttribute("data-literal")).toBe(true);
  });

  it("StateChip draws a caps label and its name in sentence case", () => {
    render(<StateChip state="failure" label="NOT LAUNCHED" data-testid="c" />);
    const chip = screen.getByTestId("c");
    expect(chip.textContent).toContain("Not launched");
    expect(chip.getAttribute("aria-label")).toBe("Not launched");
  });

  it("FoldGadget's title and StatusStrip's words draw in sentence case", () => {
    render(
      <>
        <FoldGadget title="PARKED SOURCES" token="2 PARKED"><p>body</p></FoldGadget>
        <StatusStrip items={[{ text: "ENGINE READY", lamp: "ok" }]} data-testid="s" />
      </>,
    );
    expect(screen.getByText("Parked sources")).toBeTruthy();
    expect(screen.getByText("2 parked")).toBeTruthy();
    expect(screen.getByTestId("s").textContent).toContain("Engine ready");
  });
});
