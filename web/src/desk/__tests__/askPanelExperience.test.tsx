import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { AskPanel } from "../components/AskPanel";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { latchAskSelection } from "../ask";
import { clearEngineCache } from "../hooks/useEngine";
import { durableDraftKey } from "../../lib/durableDraft";
import recordedProjects from "./fixtures/people-wire/projects.json";
import emptyProjects from "./fixtures/settings-wire/projects.json";
import recordedNote from "../../test/wire/note.start-here.wire.json";

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

it.each(["transport", "HTTP"])("a %s failed Projects read is distinct from the recorded empty list and Retry retains the question", async (failure) => {
  let failed = true;
  const reads: string[] = [];
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const path = String(input);
    reads.push(path);
    if (path === "/api/projects" && failed) {
      if (failure === "transport") throw new TypeError("Projects offline");
      return { ok: false, status: 503, headers: { get: () => "application/json" }, json: async () => ({ error: "Projects offline" }) };
    }
    return { ok: true, status: 200, headers: { get: () => "application/json" }, json: async () => path === "/api/projects" ? emptyProjects : {} };
  }));
  render(<AskPanel />);
  const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
  fireEvent.change(prompt, { target: { value: "Which migration needs me?" } });
  expect(await screen.findByLabelText("Projects unavailable")).toBeInTheDocument();
  expect(screen.queryByLabelText("No projects")).toBeNull();
  const prior = reads.length;
  failed = false;
  fireEvent.click(screen.getByRole("button", { name: "Retry Projects" }));
  await waitFor(() => expect(screen.queryByLabelText("Projects unavailable")).toBeNull());
  expect(screen.queryByLabelText("No projects")).toBeNull();
  expect(reads.slice(prior)).toEqual(["/api/projects"]);
  expect(prompt).toHaveValue("Which migration needs me?");
});

it("a failed Projects refresh retains known choices, the question, selected passage and Note context", async () => {
  let failed = false;
  const reads: string[] = [];
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const path = String(input);
    reads.push(path);
    if (path === "/api/projects" && failed) throw new TypeError("Projects offline");
    return { ok: true, status: 200, headers: { get: () => "application/json" }, json: async () => path === "/api/projects" ? recordedProjects : {} };
  }));
  const note = recordedNote.wire.note;
  const noteRef = `note:${note.id}`;
  useDesk.setState({ items: { ...EMPTY_ITEMS, note: [{ kind: "note", id: note.id, title: note.title, bodyMarkdown: note.body_markdown, tags: note.tags, createdAt: note.created_at }] }, selectedIds: [noteRef] });
  latchAskSelection({ noteRef, text: "HoldSpeak does three jobs for you." });
  render(<AskPanel />);
  fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "Explain these jobs" } });
  fireEvent.click(screen.getByText("Add to About"));
  expect(await screen.findByRole("checkbox", { name: "Payments ledger cutover" })).toBeInTheDocument();
  failed = true;
  act(() => projectRefresh.current!());
  expect(await screen.findByLabelText("Projects unavailable")).toBeInTheDocument();
  expect(screen.getByLabelText("Last read")).toBeInTheDocument();
  expect(screen.getByRole("checkbox", { name: "Payments ledger cutover" })).toBeInTheDocument();
  expect(screen.getByTestId("ask-context")).toHaveTextContent("Start here");
  expect(screen.getByText("HoldSpeak does three jobs for you.")).toBeInTheDocument();
  expect(screen.getByRole("textbox", { name: "Ask about your work" })).toHaveValue("Explain these jobs");
  const prior = reads.length;
  failed = false;
  fireEvent.click(screen.getByRole("button", { name: "Retry Projects" }));
  await waitFor(() => expect(screen.queryByLabelText("Projects unavailable")).toBeNull());
  expect(reads.slice(prior)).toEqual(["/api/projects"]);
  expect(screen.getByRole("checkbox", { name: "Payments ledger cutover" })).toBeInTheDocument();
  expect(screen.getByTestId("ask-context")).toHaveTextContent("Start here");
  expect(screen.getByText("HoldSpeak does three jobs for you.")).toBeInTheDocument();
});
