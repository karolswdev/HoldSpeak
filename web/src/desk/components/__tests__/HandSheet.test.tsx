/* Hand to agent (the Conductor canvas K2/K3, ratified 2026-10-06): the
 * launch sheet with the hub faked in the shape of
 * POST /api/agent/hand/preview and POST /api/agent/hand; the row origin
 * rules; the registry verb (Object menu, context menu, ⌘K). */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { HandSheet, kb, modeWord, refusalToken, sourceFact, type HandPreview } from "../HandSheet";
import { handKindOf, handOriginOfRow, handRefOf, useAgentHand } from "../../agentHand";
import { HandRowVerb } from "../HandRowVerb";
import { VERBS } from "../../verbRegistry";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";

const ORIGIN = { kind: "action" as const, id: "ai_1", title: "Write the rollback runbook", projectId: "p-ledger" };

function preview(patch: Partial<HandPreview> = {}): HandPreview {
  return {
    text: "HoldSpeak hands you one item: action:ai_1 \"Write the rollback runbook\".",
    refs: ["action:ai_1", "meeting:m1"],
    bytes: 4300,
    people_cut: 3,
    sources: [
      { kind: "action", ref: "ai_1", title: "Write the rollback runbook", lines: null },
      { kind: "meeting", ref: "m1", title: "Ledger cutover sync", lines: null },
      { kind: "project_commitments", ref: "p-ledger", title: "Open commitments", lines: 3 },
      { kind: "memory", ref: "p-ledger", title: "Memory", lines: 2 },
    ],
    acceptance: ["a", "b", "c", "d", "e", "f"],
    repo: "/Users/someone/dev/payments-ledger",
    branch: "hs/action-ai_1",
    worktree: "hs-action-ai_1",
    project_id: "p-ledger",
    control_mode: "yolo",
    profile: "claude-default",
    refused: [],
    ...patch,
  };
}

const DETECT = {
  agents: [
    { id: "claude", label: "Claude Code", installed: true, path: "/x/claude", version: "2.1.4", hooks: "installed", signed_in: "yes", ready: true, verb: "Use it" },
    { id: "codex", label: "Codex", installed: true, path: "/x/codex", version: "0.46.0", hooks: "missing", signed_in: "unknown", ready: false, verb: "Use it" },
  ],
  tmux: { installed: true, path: "/x/tmux", version: "3.5a", install_hint: null },
};

type Answer = { status: number; body: unknown };
let previewAnswer: (profile: string) => Answer;
let handAnswer: Answer;
let calls: { url: string; body: Record<string, unknown> | null }[];

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
  localStorage.clear();
  useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], pullouts: [], panelRects: {}, panelSaved: [], panelOrder: [] });
  useAgentHand.setState({ origin: null });
  calls = [];
  previewAnswer = () => ({ status: 200, body: preview() });
  handAnswer = { status: 202, body: { status: "launched", launch_id: "l1" } };
  vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
    const body = init?.body ? JSON.parse(String(init.body)) : null;
    calls.push({ url: String(url), body });
    let answer: Answer = { status: 200, body: {} };
    if (String(url).endsWith("/api/onboarding/agents")) answer = { status: 200, body: DETECT };
    else if (String(url).endsWith("/api/agent/hand/preview")) answer = previewAnswer(String(body?.profile));
    else if (String(url).endsWith("/api/agent/hand")) answer = handAnswer;
    return Promise.resolve({
      ok: answer.status < 400,
      status: answer.status,
      headers: new Headers({ "content-type": "application/json" }),
      json: () => Promise.resolve(answer.body),
      text: () => Promise.resolve(JSON.stringify(answer.body)),
    });
  }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function openSheet() {
  render(<HandSheet />);
  act(() => useAgentHand.getState().open(ORIGIN));
}

describe("the launch sheet", () => {
  it("K3a: opens on Claude Code with the brief, WHERE, the Control mode and the Anthropic egress", async () => {
    openSheet();
    const sheet = await screen.findByTestId("hand-sheet");
    await within(sheet).findByText("Ledger cutover sync");
    const first = calls.find((c) => c.url.endsWith("/api/agent/hand/preview"))!;
    expect(first.body).toMatchObject({ kind: "action", id: "ai_1", profile: "claude-default", project_id: "p-ledger" });
    expect(screen.getByText("BRIEF · 4 SOURCES · 4.2 KB")).toBeTruthy();
    expect(within(sheet).getByTestId("hand-brief-tokens").textContent).toBe("PEOPLE CUT · 3 PARTSACCEPTANCE · 6 CHECKS");
    expect(within(sheet).getByText("3 OPEN")).toBeTruthy();
    const where = within(sheet).getByTestId("hand-where").textContent ?? "";
    expect(where).toContain("~/dev/payments-ledger");
    expect(where).toContain("NEW WORKTREE");
    expect(where).toContain("hs/action-ai_1");
    expect(where).toContain("CONTROL · YOLO");
    const footer = document.querySelector(".desk-hand-footer")!;
    expect(footer.querySelector(".gadget-chip-egress")!.textContent).toContain("API.ANTHROPIC.COM");
    expect(footer.textContent).toContain("CLAUDE CODE · YOLO");
    expect((screen.getByTestId("hand-launch") as HTMLButtonElement).disabled).toBe(false);
    // The agent cards carry the hub's facts.
    expect(within(sheet).getByText("HOOKS IN · 2.1.4")).toBeTruthy();
    expect(within(sheet).getByText("NO HOOKS · 0.46.0")).toBeTruthy();
  });

  it("K3b: picking Codex reads the preview again for codex-default; the egress chip follows the pick", async () => {
    openSheet();
    const sheet = await screen.findByTestId("hand-sheet");
    await within(sheet).findByText("Ledger cutover sync");
    fireEvent.click(within(sheet).getByRole("radio", { name: /Codex/ }));
    await waitFor(() => expect(calls.some((c) => c.body?.profile === "codex-default")).toBe(true));
    const footer = document.querySelector(".desk-hand-footer")!;
    await waitFor(() => expect(footer.querySelector(".gadget-chip-egress")!.textContent).toContain("API.OPENAI.COM"));
    expect(footer.textContent).toContain("CODEX");
  });

  it("a refusal the launch would meet is a named token, and Launch is withheld from the press", async () => {
    previewAnswer = () => ({ status: 200, body: preview({ repo: null, refused: ["no_repository", "executable_absent"] }) });
    openSheet();
    const refused = await screen.findByTestId("hand-refused");
    expect(refused.textContent).toContain("NO REPOSITORY");
    expect(refused.textContent).toContain("CLAUDE CODE NOT INSTALLED");
    expect((screen.getByTestId("hand-launch") as HTMLButtonElement).disabled).toBe(true);
  });

  it("an item the brief cannot carry says so by name", async () => {
    previewAnswer = () => ({ status: 404, body: { error: "item_unknown", code: "item_unknown" } });
    openSheet();
    const refused = await screen.findByTestId("hand-preview-refused");
    expect(refused.textContent).toContain("ITEM NOT FOUND");
  });

  it("Launch posts the hand-off with the picked profile and closes the sheet", async () => {
    openSheet();
    const sheet = await screen.findByTestId("hand-sheet");
    await within(sheet).findByText("Ledger cutover sync");
    fireEvent.click(screen.getByTestId("hand-launch"));
    await waitFor(() => expect(useAgentHand.getState().origin).toBeNull());
    const hand = calls.find((c) => c.url.endsWith("/api/agent/hand"))!;
    expect(hand.body).toMatchObject({ kind: "action", id: "ai_1", profile: "claude-default", project_id: "p-ledger" });
  });

  it("a refused launch keeps the sheet and names the refusal in the footer", async () => {
    handAnswer = { status: 409, body: { error: "worktree_duplicate", code: "worktree_duplicate" } };
    openSheet();
    const sheet = await screen.findByTestId("hand-sheet");
    await within(sheet).findByText("Ledger cutover sync");
    fireEvent.click(screen.getByTestId("hand-launch"));
    const line = await screen.findByTestId("hand-launch-refused");
    expect(line.textContent).toBe("NOT LAUNCHED · WORKTREE EXISTS");
    expect(useAgentHand.getState().origin).not.toBeNull();
  });

  it("Cancel closes the sheet", async () => {
    openSheet();
    await screen.findByTestId("hand-sheet");
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(useAgentHand.getState().origin).toBeNull();
  });
});

describe("the words", () => {
  it("modes, sizes, facts and refusals are tokens", () => {
    expect([modeWord("safe"), modeWord("neutral"), modeWord("yolo")]).toEqual(["SECURE", "NORMAL", "YOLO"]);
    expect(kb(4300)).toBe("4.2 KB");
    expect(sourceFact({ kind: "decision", ref: "d", title: "", lines: null })).toBe("DECISION");
    expect(sourceFact({ kind: "project_decisions", ref: "p", title: "", lines: 1 })).toBe("1 DECISION");
    expect(sourceFact({ kind: "memory", ref: "p", title: "", lines: 0 })).toBeNull();
    expect(refusalToken("executable_absent", "codex")).toBe("CODEX NOT INSTALLED");
    expect(refusalToken("some_new_reason", "claude")).toBe("SOME NEW REASON");
  });
});

describe("Hand to agent: where the verb reaches", () => {
  it("the kinds agent.hand takes, and the row origins", () => {
    expect(handKindOf("decision")).toBe("decision");
    expect(handKindOf("note")).toBe("note");
    expect(handKindOf("project")).toBeNull();
    expect(handRefOf("action_item:ai_1")).toEqual({ kind: "action", id: "ai_1" });
    expect(handRefOf("thought:t1")).toBeNull();
    // The Door card's declared verb wins.
    expect(handOriginOfRow({
      title: "Write the rollback runbook", projectId: "p",
      _doorCard: { lawful_verbs: [{ name: "follow_through.complete", arguments: { verb: "done" } }, { name: "agent.hand", arguments: { kind: "action", id: "c1" } }] },
    })).toEqual({ kind: "action", id: "c1", title: "Write the rollback runbook", projectId: "p" });
    expect(handOriginOfRow({ title: "T", source: "commitment", actionItemId: "a9" })).toMatchObject({ kind: "action", id: "a9" });
    expect(handOriginOfRow({ title: "Freeze", source: "decision", openRef: "decision:d-freeze" })).toMatchObject({ kind: "decision", id: "d-freeze" });
    // A GitHub issue is not a kind agent.hand takes: no verb.
    expect(handOriginOfRow({ title: "#418 Reconciliation job slow", source: "github" })).toBeNull();
  });

  it("the row verb opens the sheet for its item, and is withheld when the item cannot be handed", () => {
    const { container } = render(<>
      <HandRowVerb item={{ title: "Write the rollback runbook", source: "commitment", actionItemId: "ai_1" }} />
      <HandRowVerb item={{ title: "#418", source: "github" }} />
    </>);
    expect(container.querySelectorAll("[data-testid=hand-row-verb]").length).toBe(1);
    fireEvent.click(screen.getByRole("button", { name: "Hand to agent: Write the rollback runbook" }));
    expect(useAgentHand.getState().origin).toMatchObject({ kind: "action", id: "ai_1" });
  });

  it("one registry verb in the Object menu (and so the context menu and ⌘K), with agent keywords", () => {
    const verb = VERBS.find((v) => v.id === "object.hand-to-agent")!;
    expect(verb).toBeTruthy();
    expect(verb.menu).toBe("object");
    expect(verb.scope).toBe("object");
    expect(verb.keywords).toEqual(expect.arrayContaining(["agent", "claude", "codex"]));
    expect(verb.ghost?.({ selectedRef: null } as never)).toBe("Select an object");
  });
});
