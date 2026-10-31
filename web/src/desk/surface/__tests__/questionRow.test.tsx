// PG-LANG §9.4 (LANG10): the QuestionRow pattern and the round strip's token lamps.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FilterTokens } from "../FilterTokens";
import { QuestionFold, QuestionRow } from "../QuestionRow";

describe("QuestionRow", () => {
  it("draws one question, its why, the offered answers and his own words; every verb a library Button", () => {
    const onAnswer = vi.fn();
    const onSkip = vi.fn();
    const { rerender } = render(<QuestionRow question="Where does the recap run?" why="It decides what step 1 owns."
      choices={["In the aftercare", "As its own job"]} value="" onChange={() => undefined} onAnswer={onAnswer} onSkip={onSkip} />);
    const row = screen.getByRole("region", { name: "Question" });
    expect(within(row).getByText("Where does the recap run?")).toHaveClass("kit-question-text");
    for (const button of within(row).getAllByRole("button")) expect(button.className).toContain("btn");
    fireEvent.click(within(row).getByRole("button", { name: "As its own job" }));
    expect(onAnswer).toHaveBeenLastCalledWith("As its own job", "As its own job");
    expect(within(row).getByTestId("kit-question-answer")).toBeDisabled();
    rerender(<QuestionRow question="Where does the recap run?" value="In the hub" onChange={() => undefined}
      onAnswer={onAnswer} onSkip={onSkip} />);
    fireEvent.keyDown(screen.getByRole("textbox", { name: "Your answer" }), { key: "Enter" });
    expect(onAnswer).toHaveBeenLastCalledWith("In the hub");
    fireEvent.click(screen.getByTestId("kit-question-skip"));
    expect(onSkip).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("group", { name: "Offered answers" })).toBeNull();
  });

  it("folds an answered question to one line with what it became", () => {
    render(<QuestionFold question="Where does it run?" answer="In the hub" became={["step 1 owns", "R+ measure"]} data-testid="fold" />);
    expect(screen.getByTestId("fold").textContent).toBe("?Where does it run?= In the hub→ step 1 owns, R+ measure");
  });
});

describe("FilterTokens with lamps (the round strip)", () => {
  it("gives a token a lamp, a live breath, a struck label and an aside", () => {
    render(<FilterTokens label="Rounds" value="Product" onChange={() => undefined} options={[
      { value: "Architecture", label: "Architecture", lamp: "ok", aside: "· 2 changes" },
      { value: "Product", label: "Product", lamp: "ask", live: true },
      { value: "Stack", label: "Stack", struck: true },
      { value: "Delivery", label: "Delivery" },
    ]} />);
    const arch = screen.getByRole("button", { name: /Architecture/ });
    expect(arch.querySelector(".surface-filter-lamp")).toHaveAttribute("data-tone", "ok");
    expect(within(arch).getByText("· 2 changes")).toHaveClass("surface-filter-aside");
    expect(screen.getByRole("button", { name: /Product/ }).querySelector(".surface-filter-lamp")).toHaveAttribute("data-live");
    expect(within(screen.getByRole("button", { name: /Stack/ })).getByText("Stack")).toHaveClass("surface-filter-struck");
    // A plain token is drawn as before: its label alone.
    expect(screen.getByRole("button", { name: "Delivery" }).innerHTML).toBe("Delivery");
  });
});
