import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { AskPanel } from "../components/AskPanel";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { latchAskSelection } from "../ask";
import { clearEngineCache } from "../hooks/useEngine";
import { durableDraftKey } from "../../lib/durableDraft";

const projectRefresh = vi.hoisted(() => ({ current: null as (() => void) | null }));
vi.mock("../useDeskChangedRefresh", () => ({ useOnDeskChanged: (callback: () => void) => { projectRefresh.current = callback; } }));

// Hold the callback that a real MicButton can retain across stop/transcribe.
// The Ask component and durable draft writer remain real.
const capture = vi.hoisted(() => ({ onText: null as ((text: string) => void) | null }));
vi.mock("../components/MicButton", () => ({
  MicButton: ({ onText, draftScope }: { onText: (text: string) => void; draftScope?: string }) => {
    capture.onText = onText;
    return <span data-testid="ask-voice-capture" data-draft-scope={draftScope} />;
  },
}));

beforeEach(() => {
  localStorage.clear();
  latchAskSelection(null);
  clearEngineCache();
  capture.onText = null;
  useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], askOpen: true, pullouts: [], panelRects: {}, panelSaved: [], panelOrder: [] });
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: () => Promise.resolve({}),
  })));
});

afterEach(() => {
  cleanup();
  latchAskSelection(null);
  vi.unstubAllGlobals();
});

it("empty Ask offers prompt Buttons that prefill and focus the durable editor", () => {
  // Ask D1: the prompts come from this desk (a meeting this week here).
  useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: [{ kind: "meeting", id: "m1", title: "Ledger cutover sync", startedAt: new Date().toISOString() }] as never } });
  render(<AskPanel />);
  expect(screen.getByTestId("ask-empty")).toBeInTheDocument();

  const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
  fireEvent.click(screen.getByRole("button", { name: "What needs my attention today?" }));
  expect(prompt).toHaveValue("What needs my attention today?");
  expect(document.activeElement).toBe(prompt);

  fireEvent.click(screen.getByRole("button", { name: "Summarize this week's meetings" }));
  expect(prompt).toHaveValue("Summarize this week's meetings");
  expect(document.activeElement).toBe(prompt);
});

it("late Ask speech appends to the newest durable draft through one mic", () => {
  render(<AskPanel />);
  const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
  fireEvent.change(prompt, { target: { value: "Question at capture start" } });
  const heldOnText = capture.onText!;
  expect(screen.getAllByTestId("ask-voice-capture")).toHaveLength(1);
  expect(screen.getByTestId("ask-voice-capture")).toHaveAttribute("data-draft-scope", "desk-ask");

  fireEvent.change(prompt, { target: { value: "Newer edited question" } });
  act(() => heldOnText("late speech"));

  expect(prompt).toHaveValue("Newer edited question late speech");
  expect(JSON.parse(localStorage.getItem(durableDraftKey("desk-ask"))!).text).toBe("Newer edited question late speech");
});
