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
    kind: "action",
    id: "ai_1",
    requested_profile: "claude-default",
    resume: null,
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
let launchAnswer: () => Answer;
let calls: { url: string; body: Record<string, unknown> | null }[];

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
  localStorage.clear();
  useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], pullouts: [], panelRects: {}, panelSaved: [], panelOrder: [] });
  useAgentHand.setState({ origin: null });
  calls = [];
  previewAnswer = (profile) => ({ status: 200, body: preview({ requested_profile: profile, profile }) });
  handAnswer = { status: 202, body: { status: "launched", launch_id: "l1", instruction_state: "sent" } };
  launchAnswer = () => ({ status: 200, body: { launch_id: "l1", instruction_state: "sent" } });
  vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
    const body = init?.body ? JSON.parse(String(init.body)) : null;
    calls.push({ url: String(url), body });
    let answer: Answer = { status: 200, body: {} };
    if (String(url).endsWith("/api/onboarding/agents")) answer = { status: 200, body: DETECT };
    else if (String(url).endsWith("/api/agent/hand/preview")) answer = previewAnswer(String(body?.profile));
    else if (String(url).endsWith("/api/agent/hand")) answer = handAnswer;
    else if (String(url).includes("/api/agent/launches/")) answer = launchAnswer();
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

  it("Launch posts the hand-off with the picked profile and keeps the sheet with its receipt", async () => {
    openSheet();
    const sheet = await screen.findByTestId("hand-sheet");
    await within(sheet).findByText("Ledger cutover sync");
    fireEvent.click(screen.getByTestId("hand-launch"));
    await screen.findByTestId("hand-launch-receipt");
    const hand = calls.find((c) => c.url.endsWith("/api/agent/hand"))!;
    expect(hand.body).toMatchObject({ kind: "action", id: "ai_1", profile: "claude-default", project_id: "p-ledger" });
    expect(useAgentHand.getState().origin).not.toBeNull();
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


/* Astra round 1 on #905: producer-generated answers (tests/unit/test_agent_hand.py rig,
 * POST /api/agent/hand), copied verbatim. */
const REAL_PENDING = {"status": "launched", "resumed": false, "instruction_state": "pending", "trust_state": null, "launch_id": "launch_36a3edc2f02f4e4a", "attempt_id": "att_baa54b04afce4eec", "operation_id": "op_002c5938d18448619f0942907ee7f75f", "state": "launched", "failure": null, "gate": "gated", "session": "hs-action-ai_1-99c0e7", "worktree": {"name": "hs-action-ai_1", "branch": "hs/action-ai_1"}, "source_id": "src_0b0084a8db9b697a", "story_ref": {"project": "proj-0123456789ab", "story_id": "action-ai_1"}, "origin_ref": {"kind": "action", "id": "ai_1"}, "project_id": "proj-0123456789ab", "control_mode": "yolo", "brief": {"bytes": 1270, "refs": ["action:ai_1", "meeting:m1"], "people_cut": 1}};
const REAL_BRANCH_FAILURE = {"status": "failed", "resumed": false, "instruction_state": null, "trust_state": null, "launch_id": "launch_f680316c0b82405a", "attempt_id": null, "operation_id": "op_5d25ab64f2564d549b063b79e29fd277", "state": "failed", "failure": {"stage": "worktree_create", "outcome": "worktree_duplicate"}, "gate": "gated", "session": "hs-action-ai_1-d2028c", "worktree": {"name": "hs-action-ai_1", "branch": "hs/action-ai_1"}, "source_id": "src_02aa836a975cc7b2", "story_ref": {"project": "proj-0123456789ab", "story_id": "action-ai_1"}, "origin_ref": {"kind": "action", "id": "ai_1"}, "project_id": "proj-0123456789ab", "control_mode": "yolo", "brief": {"bytes": 1270, "refs": ["action:ai_1", "meeting:m1"], "people_cut": 1}};

describe("the launch sheet follows the real answers (Astra #905)", () => {
  it("a pending delivery keeps its receipt and follows the launch until the brief is sent", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      handAnswer = { status: 202, body: REAL_PENDING };
      let state = "pending";
      launchAnswer = () => ({ status: 200, body: { launch_id: REAL_PENDING.launch_id, instruction_state: state } });
      openSheet();
      await screen.findByText("Ledger cutover sync");
      fireEvent.click(screen.getByTestId("hand-launch"));
      const receipt = await screen.findByTestId("hand-launch-receipt");
      expect(receipt.textContent).toBe("LAUNCHED · BRIEF PENDING");
      expect(useAgentHand.getState().origin).not.toBeNull();
      expect(screen.queryByTestId("hand-launch")).toBeNull();
      await act(async () => { await vi.advanceTimersByTimeAsync(2100); });
      expect(calls.some((c) => c.url.endsWith(`/api/agent/launches/${REAL_PENDING.launch_id}`))).toBe(true);
      expect(screen.getByTestId("hand-launch-receipt").textContent).toBe("LAUNCHED · BRIEF PENDING");
      state = "sent";
      await act(async () => { await vi.advanceTimersByTimeAsync(2100); });
      await waitFor(() => expect(screen.getByTestId("hand-launch-receipt").textContent).toBe("LAUNCHED · BRIEF SENT"));
    } finally {
      vi.useRealTimers();
    }
  });

  it("a brief not sent names the reason, keeps the brief, and Send again delivers it on the same launch", async () => {
    handAnswer = { status: 202, body: { ...REAL_PENDING, instruction_state: "session_gone" } };
    openSheet();
    await screen.findByText("Ledger cutover sync");
    fireEvent.click(screen.getByTestId("hand-launch"));
    const receipt = await screen.findByTestId("hand-launch-receipt");
    expect(receipt.textContent).toBe("LAUNCHED · BRIEF NOT SENT · SESSION GONE · KEPT ON THE HUB · SEND AGAIN");
    const stub = globalThis.fetch;
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (String(url).endsWith(`/api/agent/launches/${REAL_PENDING.launch_id}/deliver`)) {
        calls.push({ url: String(url), body: null });
        return Promise.resolve({ ok: true, status: 202, headers: new Headers({ "content-type": "application/json" }),
          json: () => Promise.resolve({ launch_id: REAL_PENDING.launch_id, instruction_state: "sent" }) });
      }
      return stub(url, init);
    }));
    fireEvent.click(screen.getByTestId("hand-send-again"));
    await waitFor(() => expect(screen.getByTestId("hand-launch-receipt").textContent).toBe("LAUNCHED · BRIEF SENT"));
  });

  it("a real worktree-create failure is named WORKTREE EXISTS, never HUB UNREACHABLE", async () => {
    handAnswer = { status: 409, body: REAL_BRANCH_FAILURE };
    openSheet();
    await screen.findByText("Ledger cutover sync");
    fireEvent.click(screen.getByTestId("hand-launch"));
    const line = await screen.findByTestId("hand-launch-refused");
    expect(line.textContent).toBe("NOT LAUNCHED · WORKTREE EXISTS");
  });

  it("HUB UNREACHABLE only when no answer came", async () => {
    const stub = globalThis.fetch;
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) =>
      String(url).endsWith("/api/agent/hand") ? Promise.reject(new TypeError("Failed to fetch")) : stub(url, init)));
    openSheet();
    await screen.findByText("Ledger cutover sync");
    fireEvent.click(screen.getByTestId("hand-launch"));
    expect((await screen.findByTestId("hand-launch-refused")).textContent).toBe("NOT LAUNCHED · HUB UNREACHABLE");
  });

  it("a pick whose preview has not come back keeps Launch withheld (a late answer never arms it)", async () => {
    let release: (() => void) | null = null;
    const stub = globalThis.fetch;
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (String(url).endsWith("/api/agent/hand/preview") && JSON.parse(String(init?.body)).profile === "codex-default") {
        return new Promise((resolve) => { release = () => resolve(stub(url, init)); });
      }
      return stub(url, init);
    }));
    openSheet();
    await screen.findByText("Ledger cutover sync");
    expect((screen.getByTestId("hand-launch") as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(screen.getByRole("radio", { name: /Codex/ }));
    expect((screen.getByTestId("hand-launch") as HTMLButtonElement).disabled).toBe(true);
    // Back to Claude Code before Codex answers; then the late Codex answer lands.
    fireEvent.click(screen.getByRole("radio", { name: /Claude Code/ }));
    await waitFor(() => expect((screen.getByTestId("hand-launch") as HTMLButtonElement).disabled).toBe(false));
    await act(async () => { release?.(); await Promise.resolve(); });
    expect((screen.getByTestId("hand-launch") as HTMLButtonElement).disabled).toBe(false);
    expect(document.querySelector(".desk-hand-footer .gadget-chip-egress")!.textContent).toContain("API.ANTHROPIC.COM");
  });

  it("a held Claude launch: picking Codex shows the held agent, its egress, RESUMES, and withholds Launch", async () => {
    previewAnswer = (profile) => ({
      status: 200,
      body: preview({
        requested_profile: profile, profile: "claude-default",
        resume: { launch_id: "l9", profile: "claude-default", instruction_state: "pending" },
        refused: profile === "claude-default" ? [] : ["launch_profile_mismatch"],
      }),
    });
    openSheet();
    await screen.findByText("Ledger cutover sync");
    expect(screen.getByTestId("hand-resume").textContent).toBe("RESUMES · BRIEF PENDING");
    fireEvent.click(screen.getByRole("radio", { name: /Codex/ }));
    await waitFor(() => expect(screen.getByTestId("hand-refused").textContent).toContain("HELD FOR CLAUDE CODE"));
    expect((screen.getByTestId("hand-launch") as HTMLButtonElement).disabled).toBe(true);
    // The egress is the agent that really runs: Anthropic, not OpenAI.
    expect(document.querySelector(".desk-hand-footer .gadget-chip-egress")!.textContent).toContain("API.ANTHROPIC.COM");
  });
});
