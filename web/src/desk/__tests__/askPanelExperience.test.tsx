import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { AskPanel } from "../components/AskPanel";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { latchAskSelection } from "../ask";
import { clearEngineCache } from "../hooks/useEngine";
import { durableDraftKey } from "../../lib/durableDraft";

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
