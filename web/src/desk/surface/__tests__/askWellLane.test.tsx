/** PHILO-14 C2b — the AskWell props the agent's lane composes:
 *  `listenSignal`, `draftScope`, `inputRef`, `disabled`, `data-testid`
 *  (contract.md "AskWell"). */
import { createRef } from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AskWell, FilesChanged, PRCard, StationTrack, TimelineRail } from "..";

vi.mock("../../components/MicButton", () => ({
  MicButton: (props: { label?: string; startSignal?: number; draftScope?: string }) => (
    <span
      data-testid="mic"
      data-label={props.label}
      data-signal={String(props.startSignal ?? 0)}
      data-scope={props.draftScope ?? ""}
    />
  ),
}));

const base = {
  agent: "Claude Code",
  question: "Jordan or Avery?",
  onChange: () => undefined,
};

describe("AskWell lane props", () => {
  it("listenSignal and draftScope reach the field's mic; inputRef holds the field", () => {
    const ref = createRef<HTMLInputElement>();
    render(<AskWell {...base} value="" onAnswer={() => undefined} listenSignal={3} draftScope="steer:abc" inputRef={ref} />);
    const mic = screen.getByTestId("mic");
    expect(mic.getAttribute("data-signal")).toBe("3");
    expect(mic.getAttribute("data-scope")).toBe("steer:abc");
    expect(ref.current).toBe(screen.getByRole("textbox", { name: "Answer" }));
  });

  it("disabled: Answer is disabled without the spinner; the field stays open; Enter sends nothing", () => {
    const onAnswer = vi.fn();
    render(<AskWell {...base} value="Jordan" onAnswer={onAnswer} disabled data-testid="ask" />);
    const answer = within(screen.getByTestId("ask")).getByRole("button", { name: "Answer" });
    expect(answer).toBeDisabled();
    expect(answer.getAttribute("aria-busy")).toBeNull();
    const field = screen.getByRole("textbox", { name: "Answer" });
    expect(field).not.toBeDisabled();
    fireEvent.keyDown(field, { key: "Enter" });
    expect(onAnswer).not.toHaveBeenCalled();
  });

  it("arm: the hand's gate sits in the answer row, after Answer", () => {
    const { container } = render(
      <AskWell {...base} value="" onAnswer={() => undefined} arm={<span data-testid="arm">NORMAL · ARM FIRST</span>} />,
    );
    const row = container.querySelector(".ask-well-answer") as HTMLElement;
    expect(within(row).getByTestId("arm").textContent).toBe("NORMAL · ARM FIRST");
    expect(row.lastElementChild).toBe(screen.getByTestId("arm"));
  });

  it("busy: Answer spins and cannot be pressed; the draft stays editable; Enter sends nothing", () => {
    const onAnswer = vi.fn();
    const onChange = vi.fn();
    render(<AskWell {...base} onChange={onChange} value="Jordan" onAnswer={onAnswer} busy />);
    const button = screen.getByRole("button", { name: "Answer" });
    expect(button.getAttribute("aria-busy")).toBe("true");
    expect(button).toBeDisabled();
    const field = screen.getByRole("textbox", { name: "Answer" });
    expect(field).not.toBeDisabled();
    fireEvent.change(field, { target: { value: "Jordan owns it." } });
    expect(onChange).toHaveBeenCalledWith("Jordan owns it.");
    fireEvent.keyDown(field, { key: "Enter" });
    expect(onAnswer).not.toHaveBeenCalled();
  });
});

describe("species data-testid pass-through", () => {
  it("TimelineRail, StationTrack, PRCard and FilesChanged carry the caller's test id", () => {
    render(
      <>
        <TimelineRail label="Lane" entries={[{ word: "BRIEF", text: "x" }]} data-testid="rail" />
        <StationTrack label="Stations" stations={[{ word: "BRIEF", state: "reached" }]} data-testid="track" />
        <PRCard number={413} title="Freeze" data-testid="pr" />
        <FilesChanged files={[{ path: "a.py" }]} data-testid="files" />
      </>,
    );
    expect(screen.getByTestId("rail").tagName).toBe("OL");
    expect(screen.getByTestId("track").tagName).toBe("OL");
    expect(screen.getByTestId("pr").tagName).toBe("ARTICLE");
    expect(screen.getByTestId("files").textContent).toContain("a.py");
  });
});
