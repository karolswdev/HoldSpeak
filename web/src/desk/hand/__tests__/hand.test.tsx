// PHILO-14 C3 — drop to hand (ratified board A-3, A-3 at 393): a work item
// dragged from a drawer (or the screen) onto the Conductor drawer or an
// agent icon. YOLO: the confirm line (preview → Brief ▸ → Hand → receipt);
// Secure / Normal: the launch sheet, on the agent the drop named. A refusal
// reads on the line as the sheet reads it. At 393 there is no drag: the
// drawer's Hand to agent verb reaches the same line.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { EMPTY_ITEMS } from "../../api";
import { useAgentFlights, fromWireSessionRow } from "../../agentFlights";
import { useAgentHand } from "../../agentHand";
import { useChairWindows } from "../../chair/chairWindows";
import { useDesk } from "../../store";
import { DrawerWindow } from "../../drawer/DrawerWindow";
import { useDrawers } from "../../drawer/store";
import { Screen } from "../../screen/Screen";
import { resetScreenMembers } from "../../screen/members";
import { DragLayer, useDropHand, agentOfTarget, handOriginOfRef } from "..";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});
vi.mock("../../shell", async () => {
  const actual = await vi.importActual<typeof import("../../shell")>("../../shell");
  return { ...actual, openProjectRoom: () => undefined, openSurfaceOr: () => undefined };
});

const today = new Date().toISOString();

const ROOM = {
  project_id: "p-ledger",
  revision: 1,
  observed_at: today,
  project: { id: "p-ledger", name: "Payments ledger cutover", is_archived: false, meeting_count: 1, created_at: today, updated_at: today, revision: 1 },
  items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
  meetings: { state: "ok", count: 1, latest: null },
  resources: { state: "ok", count: 0, latest: null },
  changes: { state: "ok", recent: [] },
  review: { state: "absent", reason: "not_yet_built" },
  needsYou: {
    state: "ok",
    count: 1,
    items: [
      { source: "meeting", kind: "action_item", title: "Write the cutover comms", why: "OWNER · UNKNOWN", since: today, url: null, verb: "open", severity: "warning", action_item_id: "a-comms", meeting_id: "m-sync", owner: null },
    ],
  },
  sources: { state: "ok", items: [], count: 0, nextCheckAt: null },
  health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, overdueMilestones: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
  sinceRead: { state: "ok", readAt: null, groups: [] },
  decisions: { state: "ok", items: [] },
  commitments: { state: "ok", items: [] },
  target: { state: "absent", reason: "x" },
  updates: { state: "absent", reason: "x" },
  steward: { state: "absent", reason: "x" },
  receipts: { state: "ok", items: [] },
};

const PREVIEW = {
  text: "Write the cutover comms.\n\nChecks: the comms name the Nov 5 window.",
  refs: ["action:a-comms"],
  bytes: 2048,
  people_cut: 1,
  sources: [{ kind: "action", ref: "action:a-comms", title: "Write the cutover comms", lines: null }],
  acceptance: ["the comms name the Nov 5 window"],
  tracker: null,
  repo: "/Users/me/dev/payments-ledger",
  repo_label: "~/dev/payments-ledger",
  branch: "hs/write-the-cutover-comms",
  worktree: "hs-action-a-comms",
  project_id: "p-ledger",
  control_mode: "yolo",
  profile: "claude-default",
  resume: null,
  refused: [] as string[],
};

const SESSIONS = [
  {
    session: { agent: "codex", session_id: "x1", project_name: "payments-ledger", state: "running" },
    flight: { origin_ref: "action:a2", kind: "action", id: "a2", title: "Shard the reconciliation job", agent: "codex", state: "working", session_key: "codex:x1" },
  },
];

const world = {
  mode: "yolo",
  preview: { ...PREVIEW } as typeof PREVIEW,
  hand: null as null | (() => unknown),
  calls: [] as Array<{ url: string; init?: { method?: string; json?: unknown } }>,
};

function route(url: string, init?: { method?: string; json?: unknown }): unknown {
  world.calls.push({ url, init });
  if (url === "/api/authority/policy") return { control_mode: world.mode };
  if (url === "/api/agent/hand/preview") {
    const profile = String((init?.json as { profile?: string })?.profile ?? "claude-default");
    return { ...world.preview, control_mode: world.mode, profile };
  }
  if (url === "/api/agent/hand") {
    if (world.hand) return world.hand();
    return { status: "launched", launch_id: "launch-1", instruction_state: "sent", profile: (init?.json as { profile?: string })?.profile };
  }
  if (url.includes("/room")) return ROOM;
  if (url.includes("/meetings")) return { meetings: [{ id: "m-sync", title: "Ledger cutover sync", started_at: today }] };
  if (url.includes("/resources")) return { resources: [] };
  if (url === "/api/people/readiness") return { state: "locked" };
  if (url.startsWith("/api/coders/sessions")) return { sessions: SESSIONS, flights: [] };
  return {};
}

function setCompact(on: boolean) {
  window.matchMedia = ((query: string) => ({
    matches: on && query.includes("max-width: 720px"),
    media: query,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}
const realMatchMedia = window.matchMedia;

function transfer() {
  return { setData: vi.fn(), setDragImage: vi.fn(), effectAllowed: "", dropEffect: "" };
}

/** The desk at 1440: the screen, one drawer open over it, the drag layer. */
async function renderDesk() {
  const view = render(
    <>
      <Screen />
      <DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />
      <DragLayer />
    </>,
  );
  await screen.findByRole("button", { name: /^Write the cutover comms, ACTION ITEM/ });
  return view;
}

const comms = () => screen.getByRole("button", { name: /^Write the cutover comms, ACTION ITEM/ });
const conductor = () => screen.getByRole("button", { name: /^Conductor, DRAWER/ });
const drawer = () => document.querySelector<HTMLElement>(".drawer-window")!;

/** Lift `source`, move the pointer, hover `target` and let go on it. */
function dragOnto(source: HTMLElement, target: HTMLElement | null) {
  const data = transfer();
  fireEvent.dragStart(source, { dataTransfer: data });
  act(() => {
    useDropHand.getState().moveDrag({ x: 112, y: 512 });
  });
  if (target) {
    fireEvent.dragOver(target, { dataTransfer: data });
    fireEvent.drop(target, { dataTransfer: data });
  }
  fireEvent.dragEnd(source, { dataTransfer: data });
  return data;
}

beforeEach(() => {
  resetScreenMembers();
  setCompact(false);
  localStorage.clear();
  world.mode = "yolo";
  world.preview = { ...PREVIEW, refused: [] };
  world.hand = null;
  world.calls = [];
  apiFetch.mockReset();
  apiFetch.mockImplementation((url: string, init?: { method?: string; json?: unknown }) => {
    try {
      return Promise.resolve(route(url, init));
    } catch (error) {
      return Promise.reject(error);
    }
  });
  useChairWindows.setState({ closed: { "chair:needs": true, "chair:brief": true, "chair:week": true, "chair:capture": true }, phone: "" });
  useAgentFlights.setState({ sessions: SESSIONS.map(fromWireSessionRow), flights: [], loaded: true });
  useDrawers.setState({ drawers: [], infos: [], revision: 0, receipts: {} });
  useDropHand.setState({ drag: null, pending: null });
  useAgentHand.setState({ origin: null });
  useDesk.setState({
    items: { ...EMPTY_ITEMS, note: [{ kind: "note", id: "n-loose", title: "Questions for Avery", createdAt: today } as never] },
    updatedAt: 1,
    zoneViewPrefs: {},
    panelRects: {},
    panelOrder: [],
    panelMin: [],
  });
});
afterEach(() => {
  window.matchMedia = realMatchMedia;
});

const posts = (url: string) => world.calls.filter((c) => c.url === url && c.init?.method === "POST");

describe("PHILO-14 C3 the drag", () => {
  it("a work item lifts; the ghost and the dotted path follow; the source dims; the target under it lights", async () => {
    await renderDesk();
    const source = comms();
    expect(source).toHaveAttribute("draggable", "true");
    // Not a work item: a person, an agent, the drawers do not lift.
    expect(screen.getByRole("button", { name: /^Codex: reconciliation job, AGENT/ })).not.toHaveAttribute("draggable", "true");
    const data = transfer();
    fireEvent.dragStart(source, { dataTransfer: data });
    expect(data.setData).toHaveBeenCalledWith("application/x-holdspeak-hand", "action:a-comms");
    expect(data.setDragImage).toHaveBeenCalled();
    act(() => useDropHand.getState().moveDrag({ x: 112, y: 512 }));
    const ghost = document.querySelector<HTMLImageElement>(".drag-ghost")!;
    expect(ghost.style.left).toBe("80px");
    expect(document.querySelector(".drag-path line")).toBeTruthy();
    expect(comms()).toHaveAttribute("data-ghost", "true");
    fireEvent.dragOver(conductor(), { dataTransfer: data });
    expect(conductor()).toHaveAttribute("data-drop", "true");
    fireEvent.dragLeave(conductor(), { dataTransfer: data });
    expect(conductor()).not.toHaveAttribute("data-drop");
  });

  it("a drop on a non-target does nothing: the ghost goes, no read, no line", async () => {
    await renderDesk();
    dragOnto(comms(), screen.getByRole("button", { name: /^People, DRAWER/ }));
    expect(document.querySelector(".drag-ghost")).toBeNull();
    expect(comms()).not.toHaveAttribute("data-ghost");
    await act(async () => undefined);
    expect(world.calls.filter((c) => c.url.startsWith("/api/authority") || c.url.startsWith("/api/agent"))).toEqual([]);
    expect(screen.queryByTestId("hand-confirm")).toBeNull();
  });
});

describe("PHILO-14 C3 YOLO: the confirm line", () => {
  it("drop on the Conductor: preview → Brief ▸ → Hand → the receipt, in the drawer head", async () => {
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    const group = within(line).getByRole("group", { name: "Hand: Write the cutover comms" });
    await within(group).findByText("CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    // The line sits under the drawer head, before the icons.
    expect(line.previousElementSibling).toHaveClass("drawer-head");
    expect(posts("/api/agent/hand/preview")[0].init?.json).toEqual({
      kind: "action", id: "a-comms", profile: "claude-default", project_id: "p-ledger",
    });
    // The launch's egress, on the Hand side.
    expect(within(group).getByText("API.ANTHROPIC.COM")).toBeTruthy();
    expect(within(group).getAllByRole("button").map((b) => b.textContent)).toEqual(["Brief ▸", "Cancel", "Hand"]);
    // Nothing launched yet.
    expect(posts("/api/agent/hand")).toEqual([]);
    fireEvent.click(within(group).getByRole("button", { name: "Brief ▸" }));
    const brief = within(line).getByTestId("hand-confirm-brief");
    expect(brief.querySelector("pre")?.textContent).toBe(PREVIEW.text);
    expect(within(brief).getByText("ACCEPTANCE · 1 CHECK")).toBeTruthy();
    fireEvent.click(within(group).getByRole("button", { name: "Hand" }));
    expect(await within(line).findByTestId("hand-confirm-receipt")).toHaveTextContent("LAUNCHED · BRIEF SENT");
    expect(posts("/api/agent/hand")[0].init?.json).toEqual({
      kind: "action", id: "a-comms", profile: "claude-default", project_id: "p-ledger",
    });
    expect(within(group).getAllByRole("button").map((b) => b.textContent)).toEqual(["Close"]);
    fireEvent.click(within(group).getByRole("button", { name: "Close" }));
    expect(screen.queryByTestId("hand-confirm")).toBeNull();
  });

  it("drop on an agent icon hands to that agent's kind (Codex)", async () => {
    await renderDesk();
    dragOnto(comms(), screen.getByRole("button", { name: /^Codex: reconciliation job, AGENT/ }));
    const line = await within(drawer()).findByTestId("hand-confirm");
    await within(line).findByText("CODEX · YOLO · hs/write-the-cutover-comms");
    expect(within(line).getByText("API.OPENAI.COM")).toBeTruthy();
    expect((posts("/api/agent/hand/preview")[0].init?.json as { profile: string }).profile).toBe("codex-default");
  });

  it("a launch cap reads on the line as the sheet reads it; Hand cannot be pressed", async () => {
    world.preview = { ...PREVIEW, refused: ["launch_cap_reached"] };
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    expect(await within(line).findByText("AGENT LIMIT REACHED")).toBeTruthy();
    expect(within(line).getByRole("button", { name: "Hand" })).toBeDisabled();
  });

  it("a refused launch reads NOT LAUNCHED with its name; a brief not sent offers Send again", async () => {
    world.hand = () => {
      throw new ApiError(409, "refused", { code: "launch_cap_reached" });
    };
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    await within(line).findByText("CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    fireEvent.click(within(line).getByRole("button", { name: "Hand" }));
    expect(await within(line).findByTestId("hand-confirm-launch-refused")).toHaveTextContent(
      "NOT LAUNCHED · AGENT LIMIT REACHED",
    );
    world.hand = () => ({ status: "launched", launch_id: "launch-2", instruction_state: "paste_failed" });
    fireEvent.click(within(line).getByRole("button", { name: "Hand" }));
    expect(await within(line).findByTestId("hand-confirm-receipt")).toHaveTextContent("LAUNCHED · BRIEF NOT SENT");
    expect(within(line).getByTestId("hand-confirm-send-again")).toBeTruthy();
  });

  it("a drop from the screen draws the line at the screen's head", async () => {
    await renderDesk();
    const note = await screen.findByRole("button", { name: /^Questions for Avery, NOTE/ });
    dragOnto(note, conductor());
    const line = await screen.findByTestId("hand-confirm");
    expect(line.closest(".desk-screen-hand")).toBeTruthy();
    expect(line).toHaveAttribute("data-host", "screen");
    expect((posts("/api/agent/hand/preview")[0].init?.json as { kind: string }).kind).toBe("note");
  });
});

describe("PHILO-14 C3 Secure and Normal: the sheet", () => {
  it.each(["safe", "neutral"])("%s: the drop opens the launch sheet on the dropped agent; no preview from the line", async (mode) => {
    world.mode = mode;
    await renderDesk();
    dragOnto(comms(), screen.getByRole("button", { name: /^Codex: reconciliation job, AGENT/ }));
    await waitFor(() => expect(useAgentHand.getState().origin).not.toBeNull());
    expect(useAgentHand.getState().origin).toMatchObject({
      kind: "action", id: "a-comms", title: "Write the cutover comms", projectId: "p-ledger", agent: "codex",
    });
    expect(screen.queryByTestId("hand-confirm")).toBeNull();
    expect(posts("/api/agent/hand/preview")).toEqual([]);
  });

  it("an unread mode opens the sheet (it shows everything before the press)", async () => {
    await renderDesk();
    apiFetch.mockImplementation((url: string, init?: { method?: string; json?: unknown }) =>
      url === "/api/authority/policy" ? Promise.reject(new Error("down")) : Promise.resolve(route(url, init)),
    );
    dragOnto(comms(), conductor());
    await waitFor(() => expect(useAgentHand.getState().origin?.agent).toBe("claude"));
  });
});

describe("PHILO-14 C3 at 393: no drag; the verb reaches the line", () => {
  it("icons do not lift; the drawer list's Hand to agent opens the confirm line over the list", async () => {
    setCompact(true);
    render(
      <>
        <Screen />
        <DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />
      </>,
    );
    const row = await within(drawer()).findByText("Write the cutover comms");
    for (const el of document.querySelectorAll(".desk-screen .desk-icon")) expect(el).not.toHaveAttribute("draggable", "true");
    // The verb is withheld until a handable object is selected.
    expect(within(drawer()).queryByRole("button", { name: "Hand to agent" })).toBeNull();
    fireEvent.click(row);
    fireEvent.click(within(drawer()).getByRole("button", { name: "Hand to agent" }));
    const line = await within(drawer()).findByTestId("hand-confirm");
    await within(line).findByText("CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    // Over the list (the line comes before it).
    expect(line.compareDocumentPosition(drawer().querySelector("table, [role='grid'], .object-list")!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});

describe("PHILO-14 C3 pure", () => {
  it("what hands and who takes it", () => {
    expect(handOriginOfRef("action:a1", "T", "p")).toEqual({ kind: "action", id: "a1", title: "T", projectId: "p" });
    expect(handOriginOfRef("issue:w1.PROJ-7", "Fix")).toMatchObject({ kind: "issue", id: "w1.PROJ-7" });
    for (const ref of ["people:p1", "pr:acme#4", "coder:claude:s1", "desk_decision:d1", "repository:r1", "commitment:c1"]) {
      expect(handOriginOfRef(ref, "x")).toBeNull();
    }
    expect(agentOfTarget("drawer:conductor")).toBe("claude");
    expect(agentOfTarget("coder:codex:x1")).toBe("codex");
    expect(agentOfTarget("coder:gemini:x1")).toBeNull();
    expect(agentOfTarget("drawer:people")).toBeNull();
  });
});
