// Real hub recordings: scripts/record_engines_fixture.py settingsChain / claude.
// Every chain edit was recorded on an isolated DB with fake CLIs off the owner's PATH.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "../../../lib/api";
import { recordedGet, type Gets } from "../../../test/recordedHub";
import recorded from "./fixtures/engines.recorded.json";
import chainRecorded from "./fixtures/settings-chain.recorded.json";
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
const order = (editor: HTMLElement) => within(editor).getAllByRole("row").slice(1).map((row) => row.textContent);
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
    const editor = await openDefault();
    moveGemini(editor);
    await waitFor(() => expect(order(editor)).toEqual(["Gemini CLI", "Codex"]));
    expect(writes).toEqual([expect.objectContaining({ scope: { kind: "global" }, expected_revision: steps[1].body!.expected_revision, entries: steps[1].body!.entries })]);
    expect(screen.getByTestId("settings-engines-receipt")).toHaveTextContent("Set at");
    fireEvent.click(within(editor).getByRole("button", { name: "Remove from order" }));
    await waitFor(() => expect(order(editor)).toEqual(["Codex"]));
    fireEvent.click(within(editor).getByRole("button", { name: "Add engine" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Model library" }));
    const library = screen.getByTestId("settings-engines-library");
    fireEvent.click(within(library).getByRole("button", { name: "Add an engine" }));
    fireEvent.click(within(library).getByTestId("runson-kind-agent"));
    const agents = await screen.findByRole("grid", { name: "Agent engines" });
    fireEvent.click(within(agents).getByText("Claude Code"));
    fireEvent.click(within(agents).getByRole("button", { name: "Add" }));
    await waitFor(() => expect(screen.getByTestId("settings-engines-receipt")).toHaveTextContent("Claude Code"));
    expect(writes).toEqual([expect.objectContaining({ draft: expect.objectContaining({ preset: "claude", profile_id: "agent-claude" }) })]);
    fireEvent.click(within(library).getByRole("region", { name: "Add engine" }).querySelector("button")!);
    expect(await screen.findByTestId("settings-engine-agent-claude")).toHaveTextContent("Ready");
    fireEvent.click(screen.getByRole("region", { name: "Model library" }).querySelector("button")!);
    expect(screen.queryByTestId("settings-engines-library")).toBeNull();
  });
});
