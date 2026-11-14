// Real hub recordings: scripts/record_engines_fixture.py settingsChain / claude.
// Every chain edit was recorded on an isolated DB with fake CLIs off the owner's PATH.
import { act, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "../../../lib/api";
import { recordedGet, type Gets } from "../../../test/recordedHub";
import recorded from "./fixtures/engines.recorded.json";
import chainRecorded from "./fixtures/settings-chain.recorded.json";
import speechRecorded from "./fixtures/speech.recorded.json";
import { useRunsOn } from "../useRunsOn";
import { WHAT_ROWS } from "../whatRows";
import { EnginesSection } from "../../../pages/cores/settings/Engines";
vi.mock("../../../lib/api", async (original) => ({ ...(await original<typeof import("../../../lib/api")>()), apiFetch: vi.fn() }));
vi.mock("../../concierge/MeaningSearchRow", () => ({ MeaningSearchRow: () => null }));
vi.mock("../../../desk/firstrun/SpeechSetup", () => ({ useSpeechSetup: () => ({ notSetUp: false, ready: true, ai: { read: { kind: "ok" } } }), SpeechSetup: () => null }));
type Step = { name: string; gets: Gets; editors: Record<string, unknown>; post?: string; body?: Record<string, unknown>; answer?: unknown };
const steps = chainRecorded.steps as unknown as Step[];
function chainHub({ refuse = false } = {}) {
  let at = steps[0];
  const writes: Record<string, unknown>[] = [];
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
    const body = (init?.json ?? {}) as Record<string, unknown>;
    if (path === "/api/inference/assignments/editor") {
      const row = WHAT_ROWS.find((r) => JSON.stringify(r.scope) === JSON.stringify(body.scope))!;
      if (!at.editors[row.id]) throw new Error("not recorded");
      return structuredClone(at.editors[row.id]) as never;
    }
    if (path === "/api/inference/assignments/set") {
      writes.push(body);
      if (refuse) throw new ApiError(409, "assignment_stale", chainRecorded.refusal);
      const next = steps.find((s) => s.body && s.body.expected_revision === body.expected_revision && JSON.stringify(s.body.entries) === JSON.stringify(body.entries));
      if (!next) throw new Error(`Unrecorded chain write ${JSON.stringify(body)}`);
      at = next;
      return structuredClone(at.answer) as never;
    }
    return recordedGet(chainRecorded.gets, String(path).split("?")[0]) as never;
  });
  return writes;
}
beforeEach(() => { vi.mocked(apiFetch).mockReset(); });
async function openDefault() {
  const choice = screen.getByRole("combobox", { name: "Everything else engines" });
  await waitFor(() => expect(within(choice).getByRole("option", { name: "Codex, then Gemini CLI" })).toBeInTheDocument());
  fireEvent.change(choice, { target: { value: "order" } });
  return screen.getByRole("region", { name: "Everything else: engine order" });
}
const order = (editor: HTMLElement) => Array.from(editor.querySelectorAll("[data-object-id]")).map((row) => row.textContent);
function moveGemini(editor: HTMLElement) {
  fireEvent.click(within(editor).getByText("Gemini CLI", { exact: true }));
  fireEvent.click(within(editor).getByRole("button", { name: "Move up" }));
}
describe("Settings > Engines", () => {
  it("shows the whole hub chain in order without writing on open", async () => {
    const writes = chainHub();
    render(<EnginesSection />);
    const editor = await openDefault();
    expect(order(editor)).toEqual(["Codex", "Gemini CLI"]);
    expect(writes).toEqual([]);
    expect(screen.queryByText("Open Engines")).toBeNull();
  });
  it("moves one engine, sends both revisions, and renders the acknowledged order", async () => {
    const writes = chainHub();
    render(<EnginesSection />);
    let editor = await openDefault();
    moveGemini(editor);
    await waitFor(() => expect(order(editor)).toEqual(["Gemini CLI", "Codex"]));
    expect(writes).toEqual([expect.objectContaining({ scope: { kind: "global" }, expected_revision: steps[1].body!.expected_revision, entries: steps[1].body!.entries })]);
    expect(screen.getByTestId("settings-engines-receipt")).toHaveTextContent("Set at");
    fireEvent.click(within(editor).getByRole("button", { name: "Remove from order" }));
    const question = screen.getByRole("region", {name:"Remove Gemini CLI from Everything else?"});
    expect(within(question).getByRole("button", {name:"Cancel"})).toHaveFocus();
    expect(writes).toHaveLength(1);
    fireEvent.click(within(question).getByRole("button", {name:"Remove"}));
    await waitFor(() => expect(screen.getByRole("region", {name:"Everything else: engine order"})).toBeInTheDocument());
    editor = screen.getByRole("region", {name:"Everything else: engine order"});
    await waitFor(() => expect(order(editor)).toEqual(["Codex"]));
    fireEvent.click(within(editor).getByRole("button", { name: "Add engine" }));
    expect(screen.getByRole("menuitem", { name: "Gemini CLI" })).toBeEnabled();
    expect(screen.getByRole("menu")).toHaveClass("is-below");
    fireEvent.click(screen.getByRole("menuitem", { name: "Gemini CLI" }));
    await waitFor(() => expect(order(editor)).toEqual(["Codex", "Gemini CLI"]));
    expect(writes[2].entries).toEqual(steps[3].body!.entries);
  });
  it("a refused reorder keeps the whole chain, editor and useful reason", async () => {
    chainHub({ refuse: true });
    render(<EnginesSection />);
    const editor = await openDefault();
    moveGemini(editor);
    await waitFor(() => expect(screen.getByTestId("settings-engines-receipt")).toHaveTextContent("It changed elsewhere first"));
    expect(order(editor)).toEqual(["Codex", "Gemini CLI"]);
    expect(editor).toBeInTheDocument();
    expect(within(editor).getByRole("button", { name: "Move up" })).toBeEnabled();
  });
  it("opens the library here and Add acknowledges a CLI engine", async () => {
    const recordedSteps = recorded.claude.steps;
    let at = recordedSteps.find((s) => s.name === "found")!;
    const added = recordedSteps.find((s) => s.name === "add")!;
    const writes: unknown[] = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
      if (path === "/api/inference/assignments/editor") throw new Error("not recorded");
      if (path === added.post) { writes.push(init?.json); at = added; return structuredClone(added.answer) as never; }
      return recordedGet(at.gets, String(path).split("?")[0]) as never;
    });
    render(<EnginesSection />);
    fireEvent.click(await screen.findByRole("tab", { name: "Engines" }));
    fireEvent.click(screen.getByRole("button", { name: "Model library" }));
    const library = screen.getByTestId("settings-engines-library");
    fireEvent.click(within(library).getByRole("button", { name: "Add an engine" }));
    expect(within(library).queryByRole("combobox", {name:"Model library category"})).toBeNull();
    expect(within(library).queryByRole("grid", {name:"Model library"})).toBeNull();
    expect(screen.getByRole("region", {name:"Add engine"})).toHaveAttribute("data-pending-choice");
    expect(within(library).getByRole("button", {name:"Done"})).toBeVisible();
    fireEvent.click(document.querySelector('[role="tab"][data-tab="agent"]')!);
    const agents = await screen.findByRole("grid", { name: "Agent engines" });
    fireEvent.click(within(agents).getByText("Claude Code"));
    fireEvent.click(within(agents).getByRole("button", { name: "Add" }));
    await waitFor(() => expect(screen.getByTestId("settings-engines-receipt")).toHaveTextContent("Claude Code"));
    expect(writes).toEqual([expect.objectContaining({ draft: expect.objectContaining({ preset: "claude", profile_id: "agent-claude" }) })]);
    fireEvent.click(within(screen.getByRole("region", { name: "Add engine" })).getByRole("button", { name: "Done" }));
    expect(await screen.findByTestId("settings-engine-agent-claude")).toHaveTextContent("Ready");
    expect(screen.getByRole("tab", { name: "Engines" })).toBeVisible();
    fireEvent.click(within(screen.getByRole("region", { name: "Model library" })).getByRole("button", { name: "Done" }));
    expect(screen.getByRole("tab", {name:"Engines"})).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByTestId("settings-engines-library")).toBeNull();
  });
});

it("offers only candidates the hub admits for the selected job's modality", async () => {
  chainHub();
  render(<EnginesSection />);
  const editor = await openDefault();
  const choice = screen.getByRole("combobox", {name:"Everything else engines"});
  expect(within(choice).queryByRole("option", {name:"Whisper mlx base"})).toBeNull();
  expect(within(editor).getByRole("button", {name:"Add engine"})).toBeDisabled();
});


it("keeps the section tabs available while the library owns the work pane", async () => {
  chainHub();
  render(<EnginesSection />);
  fireEvent.click(await screen.findByRole("tab", {name:"Engines"}));
  fireEvent.click(screen.getByRole("button", {name:"Model library"}));
  expect(screen.getByRole("region", {name:"Model library"})).toBeVisible();
  expect(screen.getByRole("tab", {name:"Jobs"})).toBeVisible();
  expect(screen.getByRole("tab", {name:"Engines"})).toBeVisible();
  expect(screen.queryByRole("grid", {name:"Engines on this desk"})).toBeNull();
  expect(screen.getByRole("grid", {name:"Model library"}).closest(".surface-inspector-form")).toBeNull();
  fireEvent.click(within(screen.getByRole("region", {name:"Model library"})).getByRole("button", {name:"Done"}));
  expect(screen.getByRole("grid", {name:"Engines on this desk"})).toBeVisible();
});


it("does not label a library category with the installed engine count", async () => {
  chainHub();
  const count = vi.fn();
  render(<EnginesSection onCount={count} />);
  await waitFor(() => expect(count.mock.calls.at(-1)?.[0]).toBeGreaterThan(0));
  const installed = count.mock.calls.at(-1)![0];
  fireEvent.click(screen.getByRole("tab", {name:"Engines"}));
  fireEvent.click(screen.getByRole("button", {name:"Model library"}));
  await waitFor(() => expect(count).toHaveBeenLastCalledWith(0));
  fireEvent.click(within(screen.getByRole("region", {name:"Model library"})).getByRole("button", {name:"Done"}));
  await waitFor(() => expect(count).toHaveBeenLastCalledWith(installed));
});


it("clears a previous count when the engine read fails", async () => {
  vi.mocked(apiFetch).mockRejectedValue(new Error("No answer"));
  const count = vi.fn();
  render(<EnginesSection onCount={count} />);
  await screen.findByText("Engines not read", {exact:true});
  expect(count).toHaveBeenLastCalledWith(0);
});


it("keeps an inspected engine name in the shared facts seat", async () => {
  chainHub();
  render(<EnginesSection />);
  fireEvent.click(await screen.findByRole("tab", {name:"Engines"}));
  fireEvent.click(screen.getByRole("button", {name:"Model library"}));
  const library = screen.getByTestId("settings-engines-library");
  fireEvent.click(within(library).getByText("Codex", {exact:true}));
  fireEvent.click(within(library).getByRole("button", {name:"Inspect"}));
  const facts = library.querySelector<HTMLElement>(".surface-inspector-facts")!;
  expect(facts).toHaveAttribute("data-feedback-redact", "true");
  expect(within(facts).getByText("Name", {exact:true}).closest(".gadget-row")).toHaveTextContent("Codex");
});


it("keeps Cancel then Check in the server completion seat", async () => {
  chainHub();
  render(<EnginesSection />);
  fireEvent.click(await screen.findByRole("tab", {name:"Engines"}));
  fireEvent.click(screen.getByRole("button", {name:"Model library"}));
  fireEvent.click(screen.getByRole("button", {name:"Add an engine"}));
  fireEvent.click(document.querySelector('[role="tab"][data-tab="lan"]')!);
  const check = screen.getByTestId("concierge-add-check");
  expect(check).toBeDisabled();
  const actions = check.closest<HTMLElement>(".surface-inspector-actions")!;
  expect(within(actions).getAllByRole("button").map(button => button.textContent)).toEqual(["Cancel", "Check"]);
  expect(screen.getByRole("textbox", {name:"Server address"})).toBeVisible();
});


it("opens a model's facts when Inspect is used from Add on this Mac", async () => {
  chainHub();
  render(<EnginesSection />);
  fireEvent.click(await screen.findByRole("tab", {name:"Engines"}));
  fireEvent.click(screen.getByRole("button", {name:"Model library"}));
  fireEvent.click(screen.getByRole("button", {name:"Add an engine"}));
  fireEvent.click(document.querySelector('[role="tab"][data-tab="local"]')!);
  const models = screen.getByRole("grid", {name:"Model library"});
  fireEvent.click(within(models).getByText("Codex", {exact:true}));
  fireEvent.click(within(screen.getByTestId("settings-engines-library")).getByRole("button", {name:"Inspect"}));
  expect(screen.queryByRole("region", {name:"Add engine"})).toBeNull();
  const facts = screen.getByTestId("settings-engines-library").querySelector<HTMLElement>(".surface-inspector-facts")!;
  expect(within(facts).getByText("Name", {exact:true}).closest(".gadget-row")).toHaveTextContent("Codex");
});

it("publishes a failed engine read and its last successful read to the strip", async () => {
  vi.mocked(apiFetch).mockRejectedValue(new Error("No answer"));
  const status = vi.fn();
  render(<EnginesSection onStatus={status} />);
  await screen.findByText("Engines not read");
  await waitFor(() => expect(status).toHaveBeenLastCalledWith(expect.stringMatching(/Engines not read.*Not read yet/)));
});

it("returns from Add to the library and from the library through the Mast Back port", async () => {
  chainHub();
  const back = vi.fn();
  render(<EnginesSection onBackChange={back} />);
  fireEvent.click(await screen.findByRole("tab", {name:"Engines"}));
  fireEvent.click(screen.getByRole("button", {name:"Model library"}));
  await waitFor(() => expect(back).toHaveBeenLastCalledWith(expect.any(Function)));
  const goBack = back.mock.calls.at(-1)![0] as () => void;
  fireEvent.click(screen.getByRole("button", {name:"Add an engine"}));
  act(goBack);
  expect(screen.queryByTestId("runson-add-kinds")).toBeNull();
  expect(screen.getByRole("grid", {name:"Model library"})).toBeVisible();
  act(goBack);
  expect(screen.getByRole("grid", {name:"Engines on this desk"})).toBeVisible();
  expect(back).toHaveBeenLastCalledWith(null);
});

it("retains the last successful roster read when Retry fails and clears the failure on recovery", async () => {
  chainHub();
  const {result} = renderHook(() => useRunsOn());
  await waitFor(() => expect(result.current.lastRead).toBeInstanceOf(Date));
  const at = result.current.lastRead;
  vi.mocked(apiFetch).mockRejectedValue(new Error("No answer"));
  act(() => result.current.readAgain());
  await waitFor(() => expect(result.current.error).toBe("No answer"));
  expect(result.current.lastRead).toBe(at);
  chainHub();
  act(() => result.current.readAgain());
  await waitFor(() => expect(result.current.error).toBe(""));
  expect(result.current.lastRead!.getTime()).toBeGreaterThanOrEqual(at!.getTime());
});

it("names the last successful read kept by the Settings window after reopening a failed pane", async () => {
  vi.mocked(apiFetch).mockRejectedValue(new Error("No answer"));
  const status = vi.fn();
  render(<EnginesSection onStatus={status} lastRead={new Date(2026, 10, 12, 9, 30)} />);
  await screen.findByText("Engines not read");
  await waitFor(() => expect(status).toHaveBeenLastCalledWith(expect.stringMatching(/Engines not read.*Last read Nov 12/)));
});

it("keeps the five engine kinds visible when they fit their shared strip", async () => {
  chainHub();
  render(<EnginesSection />);
  fireEvent.click(await screen.findByRole("tab", {name:"Engines"}));
  fireEvent.click(screen.getByRole("button", {name:"Model library"}));
  fireEvent.click(screen.getByRole("button", {name:"Add an engine"}));
  fireEvent.click(document.querySelector('[role="tab"][data-tab="lan"]')!);
  expect(within(screen.getByRole("tablist",{name:"Kind of engine"})).getAllByRole("tab")).toHaveLength(5);
  expect(screen.getByTestId("runson-kind-find-lan")).toBeVisible();
  expect(screen.getByRole("checkbox", {name:"My server"})).toBeInTheDocument();
});


it("returns from the library with its Back verb when no engine is selected", async () => {
  chainHub(); render(<EnginesSection />);
  fireEvent.click(await screen.findByRole("tab", {name:"Engines"}));
  fireEvent.click(screen.getByRole("button", {name:"Model library"}));
  const back=within(screen.getByTestId("settings-engines-library")).getByRole("button",{name:"Back"});
  expect(back).toBeEnabled(); fireEvent.click(back);
  expect(screen.getByRole("grid",{name:"Engines on this desk"})).toBeVisible();
});


it("gives the speech roster its list well and returns with Back", async () => {
  chainHub();
  const get=vi.mocked(apiFetch).getMockImplementation()!;
  vi.mocked(apiFetch).mockImplementation(async (path,init) => path === "/api/concierge/speech" ? structuredClone(speechRecorded.start["/api/concierge/speech"]) as never : get(path,init));
  render(<EnginesSection />);
  fireEvent.click(await screen.findByRole("tab", {name:"Engines"}));
  fireEvent.click(screen.getByRole("button", {name:"Model library"}));
  fireEvent.change(screen.getByRole("combobox", {name:"Library"}), {target:{value:"speech"}});
  const roster=await screen.findByRole("grid", {name:"Phone speech"});
  for (const model of speechRecorded.start["/api/concierge/speech"].rows) {
    expect(await within(roster).findByText(model.label,{exact:true})).toBeVisible();
  }
  expect(roster.closest(".surface-inspector-form")).toBeNull();
  fireEvent.click(within(roster.closest<HTMLElement>(".surface-list-pane")!).getByRole("button", {name:"Back"}));
  expect(screen.getByRole("grid", {name:"Engines on this desk"})).toBeVisible();
});
