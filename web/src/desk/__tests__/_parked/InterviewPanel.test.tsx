import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { InterviewPanel } from "../components/InterviewPanel";
import { interviewCommand, type InterviewState } from "../interview";

vi.mock("../interview", () => ({ interviewCommand: vi.fn() }));

const state: InterviewState = {
  thread_id: "conversation", revision: 3, section: "goals", status: "exploring",
  sections: [{ id: "goals", name: "Goals", handoff: "" }, { id: "decisions", name: "Decision log", handoff: "" }, { id: "people", name: "People", handoff: "people" }],
  facts: { goal: { id: "goal", section: "goals", text: "Recover decision context", basis: "stated", quote: "I lose decision context", source_message_id: "user-message" } },
  suggestions: { brief: { id: "brief", section: "goals", title: "Decision brief", benefit: "Recover rationale before review", behavior: "Prepare a manual decision brief", basis: "Hypothesis based on your goal", prerequisites: "Relevant decisions", fact_ids: ["goal"], feasibility: "manual", disposition: "proposed" } },
};

afterEach(cleanup);
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(interviewCommand).mockResolvedValue(state);
});

describe("Interview controls", () => {
  it("revisits one section with the current revision before reloading", async () => {
    const reload = vi.fn().mockResolvedValue(undefined);
    render(<InterviewPanel state={state} disabled={false} reload={reload} onTry={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Section"), { target: { value: "decisions" } });
    await waitFor(() => expect(reload).toHaveBeenCalledOnce());
    expect(interviewCommand).toHaveBeenCalledWith(state, { kind: "section", section: "decisions" });
  });

  it("shows provenance and distinguishes keeping an idea from starting work", async () => {
    const onTry = vi.fn();
    render(<InterviewPanel state={state} disabled={false} reload={vi.fn().mockResolvedValue(undefined)} onTry={onTry} />);
    fireEvent.click(screen.getByRole("button", { name: /Context/ }));
    expect(screen.getByText("Your answer")).toBeTruthy();
    expect(screen.getByText("I lose decision context")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Keep idea" }));
    await waitFor(() => expect(interviewCommand).toHaveBeenCalledWith(state, { kind: "disposition", suggestion_id: "brief", disposition: "kept" }));
    expect(onTry).not.toHaveBeenCalled();
  });

  it("starts a manual draft only after persisting the selected suggestion", async () => {
    const onTry = vi.fn();
    render(<InterviewPanel state={state} disabled={false} reload={vi.fn().mockResolvedValue(undefined)} onTry={onTry} />);
    fireEvent.click(screen.getByRole("button", { name: /Context/ }));
    fireEvent.click(screen.getByRole("button", { name: "Try draft" }));
    await waitFor(() => expect(onTry).toHaveBeenCalledOnce());
    expect(interviewCommand).toHaveBeenCalledWith(state, { kind: "disposition", suggestion_id: "brief", disposition: "try" });
    expect(onTry.mock.calls[0][0]).toContain("keep configuration as proposals");
  });

  it("does not start a stale selection after a revision conflict", async () => {
    vi.mocked(interviewCommand).mockRejectedValue(new Error("Interview changed; reload"));
    const onTry = vi.fn();
    const reload = vi.fn().mockResolvedValue(undefined);
    render(<InterviewPanel state={state} disabled={false} reload={reload} onTry={onTry} />);
    fireEvent.click(screen.getByRole("button", { name: /Context/ }));
    fireEvent.click(screen.getByRole("button", { name: "Try draft" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Interview changed");
    expect(onTry).not.toHaveBeenCalled();
    expect(reload).toHaveBeenCalledOnce();
  });

  it("shows unsupported ideas without an execution action", () => {
    const unsupported: InterviewState = { ...state, suggestions: { brief: { ...state.suggestions.brief, feasibility: "unsupported_idea" } } };
    render(<InterviewPanel state={unsupported} disabled={false} reload={vi.fn().mockResolvedValue(undefined)} onTry={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /Context/ }));
    expect(screen.queryByRole("button", { name: "Try draft" })).toBeNull();
    expect(screen.getByText(/Idea · unavailable/)).toBeTruthy();
  });

  it("bounds initial suggestions and retains access to the full set", () => {
    const many = { ...state, suggestions: Object.fromEntries(Array.from({ length: 5 }, (_, i) => [String(i), { ...state.suggestions.brief, id: String(i), title: `Suggestion ${i}` }])) };
    render(<InterviewPanel state={many} disabled={false} reload={vi.fn().mockResolvedValue(undefined)} onTry={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /Context/ }));
    expect(screen.getAllByRole("article")).toHaveLength(3);
    fireEvent.click(screen.getByRole("button", { name: "All suggestions 5" }));
    expect(screen.getAllByRole("article")).toHaveLength(5);
  });

  it("disables configuration controls while the conversation is running", () => {
    render(<InterviewPanel state={state} disabled={true} reload={vi.fn().mockResolvedValue(undefined)} onTry={vi.fn()} />);
    expect(screen.getByLabelText("Section")).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /Context/ }));
    expect(screen.getByRole("button", { name: "Try draft" })).toBeDisabled();
  });
});
