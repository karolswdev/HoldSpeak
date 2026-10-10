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
import { HandSheet } from "../../components/HandSheet";
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

const LAUNCHED_SESSION = {
  session: { agent: "claude", session_id: "new1", project_name: "payments-ledger", state: "running" },
  flight: { origin_ref: "action:a-comms", kind: "action", id: "a-comms", title: "Write the cutover comms", agent: "claude", state: "working", session_key: "claude:new1", launch_id: "launch-1" },
};

const world = {
  sessionReads: 0,
  launchedAfter: null as number | null,
  mode: "yolo",
  preview: { ...PREVIEW } as typeof PREVIEW,
  hand: null as null | (() => unknown),
  calls: [] as Array<{ url: string; init?: { method?: string; json?: unknown } }>,
  agents: { agents: [] } as { agents: Array<Record<string, unknown>> },
};

function route(url: string, init?: { method?: string; json?: unknown }): unknown {
  world.calls.push({ url, init });
  if (url.startsWith("/api/onboarding/agents")) return world.agents;
  if (url === "/api/authority/policy") return { control_mode: world.mode };
  if (url === "/api/agent/hand/preview") {
    const profile = String((init?.json as { profile?: string })?.profile ?? "claude-default");
    return { ...world.preview, control_mode: world.mode, profile };
  }
  if (url === "/api/agent/hand") {
    world.launchedAfter = world.sessionReads;
    if (world.hand) return world.hand();
    return { status: "launched", launch_id: "launch-1", instruction_state: "sent", profile: (init?.json as { profile?: string })?.profile };
  }
  if (url.includes("/room")) return ROOM;
  if (url.includes("/meetings")) return { meetings: [{ id: "m-sync", title: "Ledger cutover sync", started_at: today }] };
  if (url.includes("/resources")) return { resources: [] };
  if (url === "/api/people/readiness") return { state: "locked" };
  if (url.startsWith("/api/coders/sessions")) {
    world.sessionReads += 1;
    // The launched agent registers a beat after Hand (its hook arrives late).
    const launched = world.launchedAfter !== null && world.sessionReads > world.launchedAfter + 1;
    return { sessions: launched ? [...SESSIONS, LAUNCHED_SESSION] : SESSIONS, flights: [] };
  }
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
  world.agents = { agents: [] };
  world.sessionReads = 0;
  world.launchedAfter = null;
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

/** PHILO-15 16: the fact line reads `<AGENT> · <MODE> · <branch>`; the agent
 *  is the line's flip token (a library Button) inside it. */
const factIs = (root: HTMLElement, text: string) =>
  waitFor(() => expect(root.querySelector(".confirm-line-fact")?.textContent).toBe(text));

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
    await factIs(group, "CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    // The line sits under the drawer head, before the icons. Phase 16 A3
    // (the interior kit): the head is AppHead then the FilterBar, so the
    // line follows the FilterBar.
    expect(line.previousElementSibling).toHaveAttribute("data-testid", "drawer-filter");
    expect(line.previousElementSibling?.previousElementSibling).toHaveAttribute("data-testid", "drawer-facts");
    expect(posts("/api/agent/hand/preview")[0].init?.json).toEqual({
      kind: "action", id: "a-comms", profile: "claude-default", project_id: "p-ledger",
    });
    // The launch's egress, on the Hand side.
    expect(within(group).getByText("API.ANTHROPIC.COM")).toBeTruthy();
    expect(within(group).getAllByRole("button").map((b) => b.textContent)).toEqual(["CLAUDE CODE", "Brief ▸", "Cancel", "Hand"]);
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
    expect(within(group).getAllByRole("button").map((b) => b.textContent)).toEqual(["CLAUDE CODE", "Close"]);
    fireEvent.click(within(group).getByRole("button", { name: "Close" }));
    expect(screen.queryByTestId("hand-confirm")).toBeNull();
  });

  it("drop on an agent icon hands to that agent's kind (Codex)", async () => {
    await renderDesk();
    dragOnto(comms(), screen.getByRole("button", { name: /^Codex: reconciliation job, AGENT/ }));
    const line = await within(drawer()).findByTestId("hand-confirm");
    await factIs(line, "CODEX · YOLO · hs/write-the-cutover-comms");
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
    await factIs(line, "CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
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

describe("PHILO-14 C3 Astra r1 on #946", () => {
  it("P1: after Hand the flights are re-read until the launched agent is drawn, with no other desk action", async () => {
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    await factIs(line, "CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    expect(screen.queryByRole("button", { name: /^Claude Code: cutover comms, AGENT/ })).toBeNull();
    fireEvent.click(within(line).getByRole("button", { name: "Hand" }));
    // The session registers on the second read after the launch: the poll waits for it.
    expect(
      await screen.findByRole("button", { name: /^Claude Code: cutover comms, AGENT/ }, { timeout: 6000 }),
    ).toBeTruthy();
    const reads = world.sessionReads;
    await new Promise((r) => setTimeout(r, 2500));
    expect(world.sessionReads).toBe(reads); // bounded: it stops once the agent is drawn
  }, 15000);

  it("P2: Secure, a second drop on Codex retargets the open sheet", async () => {
    world.mode = "safe";
    render(
      <>
        <Screen />
        <DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />
        <HandSheet />
      </>,
    );
    await screen.findByRole("button", { name: /^Write the cutover comms, ACTION ITEM/ });
    dragOnto(comms(), conductor());
    await screen.findByTestId("hand-sheet");
    expect(screen.getByRole("radio", { name: /Claude Code/ })).toBeChecked();
    dragOnto(comms(), screen.getByRole("button", { name: /^Codex: reconciliation job, AGENT/ }));
    await waitFor(() => expect(screen.getByRole("radio", { name: /Codex/ })).toBeChecked());
  });

  it("P2: Escape cancels the hand and the drawer stays open", async () => {
    useDrawers.setState({ drawers: [{ projectId: "p-ledger", origin: null }] as never });
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    expect(document.activeElement).toBe(line);
    fireEvent.keyDown(line, { key: "Escape" });
    expect(screen.queryByTestId("hand-confirm")).toBeNull();
    expect(useDrawers.getState().drawers.map((d) => d.projectId)).toEqual(["p-ledger"]);
    expect(drawer()).toBeTruthy();
  });

  it("P3: at 393 the drawer's Icons view does not lift either", async () => {
    setCompact(true);
    useDesk.setState({ zoneViewPrefs: { "project:p-ledger": { view: "icons" } } as never });
    render(<DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />);
    await screen.findByRole("button", { name: /^Write the cutover comms, ACTION ITEM/ });
    expect(document.querySelectorAll(".drawer-window .desk-icon").length).toBeGreaterThan(0);
    expect(document.querySelectorAll(".drawer-window .desk-icon[draggable='true']")).toHaveLength(0);
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

describe("PHILO-15 16 the sheet carries the clone through a launch refusal", () => {
  it("Secure: CLONES before Launch, CLONED · owner/name · hh:mm after a refused launch", async () => {
    world.mode = "safe";
    world.preview = {
      ...PREVIEW, repo: null as unknown as string,
      clone: { repository: "acme/ledger", host: "github.com", state: "to_clone" },
    } as typeof PREVIEW;
    world.hand = () => {
      throw new ApiError(409, "refused", {
        code: "launch_cap_reached",
        clone: { repository: "acme/ledger", host: "github.com", state: "cloned", cloned_at: "2026-10-07T09:05:00" },
      });
    };
    render(<HandSheet />);
    act(() => useAgentHand.getState().open({ kind: "action", id: "a-comms", title: "Write the cutover comms", projectId: "p-ledger" }));
    const before = await screen.findByTestId("hand-clone");
    expect(before).toHaveAttribute("data-state", "to_clone");
    expect(before).toHaveTextContent("CLONES acme/ledger");
    fireEvent.click(await screen.findByTestId("hand-launch"));
    expect(await screen.findByTestId("hand-launch-refused")).toHaveTextContent("NOT LAUNCHED · AGENT LIMIT REACHED");
    const after = screen.getByTestId("hand-clone");
    expect(after).toHaveAttribute("data-state", "cloned");
    expect(after).toHaveTextContent("CLONED · acme/ledger · 09:05");
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
    const row = await within(drawer()).findByRole("button", { name: /^Write the cutover comms, ACTION ITEM/ });
    for (const el of document.querySelectorAll(".desk-screen .desk-icon")) expect(el).not.toHaveAttribute("draggable", "true");
    // The verb is withheld until a handable object is selected.
    expect(within(drawer()).queryByRole("button", { name: "Hand to agent" })).toBeNull();
    fireEvent.click(row);
    fireEvent.click(within(drawer()).getByRole("button", { name: "Hand to agent" }));
    const line = await within(drawer()).findByTestId("hand-confirm");
    await factIs(line, "CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    // Over the list (the line comes before it).
    expect(line.compareDocumentPosition(drawer().querySelector("table, [role='grid'], .object-list")!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});

describe("PHILO-15 16 B39: the line's agent is a token the owner flips", () => {
  it("1440: CLAUDE CODE ⇄ CODEX; the preview, the egress and Hand follow the flip", async () => {
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    await factIs(line, "CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    const token = within(line).getByTestId("hand-confirm-agent");
    expect(token).toHaveAttribute("data-agent", "claude");
    expect(token).toHaveAccessibleName("Agent: Claude Code. Press to hand to Codex");
    fireEvent.click(token);
    await factIs(line, "CODEX · YOLO · hs/write-the-cutover-comms");
    expect(within(line).getByTestId("hand-confirm-agent")).toHaveAttribute("data-agent", "codex");
    expect(within(line).getByText("API.OPENAI.COM")).toBeTruthy();
    const previews = posts("/api/agent/hand/preview").map((c) => (c.init?.json as { profile: string }).profile);
    expect(previews).toEqual(["claude-default", "codex-default"]);
    fireEvent.click(within(line).getByRole("button", { name: "Hand" }));
    expect(await within(line).findByTestId("hand-confirm-receipt")).toHaveTextContent("LAUNCHED · BRIEF SENT");
    expect(posts("/api/agent/hand")[0].init?.json).toEqual({
      kind: "action", id: "a-comms", profile: "codex-default", project_id: "p-ledger",
    });
    // After the press the agent is the launch's: the token no longer flips.
    expect(within(line).getByTestId("hand-confirm-agent")).toBeDisabled();
  });

  it("393: the drawer's Hand to agent verb reaches the same token", async () => {
    setCompact(true);
    render(<DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />);
    fireEvent.click(await within(drawer()).findByRole("button", { name: /^Write the cutover comms, ACTION ITEM/ }));
    fireEvent.click(within(drawer()).getByRole("button", { name: "Hand to agent" }));
    const line = await within(drawer()).findByTestId("hand-confirm");
    await factIs(line, "CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    fireEvent.click(within(line).getByTestId("hand-confirm-agent"));
    await factIs(line, "CODEX · YOLO · hs/write-the-cutover-comms");
    fireEvent.click(within(line).getByRole("button", { name: "Hand" }));
    await within(line).findByTestId("hand-confirm-receipt");
    expect((posts("/api/agent/hand")[0].init?.json as { profile: string }).profile).toBe("codex-default");
  });
});

describe("pi spike #1020: pi is the third agent on the line", () => {
  it("the flip turns CLAUDE CODE → CODEX → PI → CLAUDE CODE; pi's egress is the engine for coding", async () => {
    world.preview = { ...PREVIEW, engine: { host: "192.168.1.43:8080", model: "qwen3.8-27b", boundary: "private_network" } };
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    await factIs(line, "CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    fireEvent.click(within(line).getByTestId("hand-confirm-agent"));
    await factIs(line, "CODEX · YOLO · hs/write-the-cutover-comms");
    expect(within(line).getByTestId("hand-confirm-agent")).toHaveAccessibleName("Agent: Codex. Press to hand to pi");
    fireEvent.click(within(line).getByTestId("hand-confirm-agent"));
    await factIs(line, "PI · YOLO · hs/write-the-cutover-comms");
    expect(within(line).getByTestId("hand-confirm-agent")).toHaveAttribute("data-agent", "pi");
    expect(within(line).getByText("LAN · 192.168.1.43:8080")).toBeTruthy();
    const previews = posts("/api/agent/hand/preview").map((c) => (c.init?.json as { profile: string }).profile);
    expect(previews).toEqual(["claude-default", "codex-default", "pi-default"]);
    fireEvent.click(within(line).getByRole("button", { name: "Hand" }));
    expect(await within(line).findByTestId("hand-confirm-receipt")).toHaveTextContent("LAUNCHED · BRIEF SENT");
    expect((posts("/api/agent/hand")[0].init?.json as { profile: string }).profile).toBe("pi-default");
  });

  it("no engine for coding: the route's own word, and Hand cannot be pressed", async () => {
    world.preview = { ...PREVIEW, refused: ["no_assignment"], engine: null };
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    fireEvent.click(within(line).getByTestId("hand-confirm-agent"));
    fireEvent.click(within(line).getByTestId("hand-confirm-agent"));
    await factIs(line, "PI · YOLO · hs/write-the-cutover-comms");
    expect(await within(line).findByText("NO ASSIGNMENT")).toBeTruthy();
    expect(within(line).getByRole("button", { name: "Hand" })).toBeDisabled();
  });
});

describe("PHILO-15 16 (Astra r1 on #1000): the default and the owner's flip", () => {
  const agent = (id: string, signedIn: string) => ({
    id, label: id, installed: true, path: `/bin/${id}`, version: "1", hooks: "installed", signed_in: signedIn, ready: true, verb: null,
  });

  it("the Conductor's default is the agent whose sign-in is known; the line says why", async () => {
    world.agents = { agents: [agent("claude", "unknown"), agent("codex", "yes")] };
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    await factIs(line, "CODEX · YOLO · hs/write-the-cutover-comms");
    expect(within(line).getByTestId("hand-confirm-skipped")).toHaveTextContent("CLAUDE CODE · SIGN-IN UNKNOWN");
  });

  it("a remembered flip keeps lane 18's warning for the agent it shows", async () => {
    world.agents = { agents: [agent("claude", "unknown"), agent("codex", "unknown")] };
    localStorage.setItem("hs.hand.agent.p-ledger", "codex");
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    await factIs(line, "CODEX · YOLO · hs/write-the-cutover-comms");
    expect(within(line).getByTestId("hand-confirm-selected-unknown")).toHaveTextContent("CODEX · SIGN-IN UNKNOWN");
    // pi spike #1020: the flip turns through pi (no sign-in of its own: no warning).
    fireEvent.click(within(line).getByTestId("hand-confirm-agent"));
    await factIs(line, "PI · YOLO · hs/write-the-cutover-comms");
    expect(within(line).queryByTestId("hand-confirm-selected-unknown")).toBeNull();
    fireEvent.click(within(line).getByTestId("hand-confirm-agent"));
    await factIs(line, "CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    expect(within(line).getByTestId("hand-confirm-selected-unknown")).toHaveTextContent("CLAUDE CODE · SIGN-IN UNKNOWN");
    expect(localStorage.getItem("hs.hand.agent.p-ledger")).toBe("claude");
  });

  it("the owner's flip is this Project's next default (the verb and the drop)", async () => {
    await renderDesk();
    dragOnto(comms(), conductor());
    let line = await within(drawer()).findByTestId("hand-confirm");
    await factIs(line, "CLAUDE CODE · YOLO · hs/write-the-cutover-comms");
    fireEvent.click(within(line).getByTestId("hand-confirm-agent"));
    await factIs(line, "CODEX · YOLO · hs/write-the-cutover-comms");
    fireEvent.click(within(line).getByRole("button", { name: "Cancel" }));
    expect(screen.queryByTestId("hand-confirm")).toBeNull();
    dragOnto(comms(), conductor());
    line = await within(drawer()).findByTestId("hand-confirm");
    await factIs(line, "CODEX · YOLO · hs/write-the-cutover-comms");
    expect(within(line).queryByTestId("hand-confirm-skipped")).toBeNull();
  });
});

describe("PHILO-15 16 B38: the first hand clones the Project's repository", () => {
  it("a clone the hand made stays CLONED when the launch after it refuses (Astra r1 on #1000)", async () => {
    world.preview = {
      ...PREVIEW, repo: null as unknown as string,
      clone: { repository: "karolswdev/holdspeak-dayone-rehearsal-1558", host: "github.com", state: "to_clone" },
    } as typeof PREVIEW;
    world.hand = () => {
      throw new ApiError(409, "refused", {
        code: "launch_cap_reached",
        clone: { repository: "karolswdev/holdspeak-dayone-rehearsal-1558", host: "github.com", state: "cloned",
                 cloned_at: "2026-10-07T18:06:00",
                 folder: "~/.holdspeak/repositories/karolswdev/holdspeak-dayone-rehearsal-1558/holdspeak-dayone-rehearsal-1558" },
      });
    };
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    expect(await within(line).findByTestId("hand-confirm-clone")).toHaveAttribute("data-state", "to_clone");
    fireEvent.click(within(line).getByRole("button", { name: "Hand" }));
    expect(await within(line).findByTestId("hand-confirm-launch-refused")).toHaveTextContent("NOT LAUNCHED · AGENT LIMIT REACHED");
    const clone = within(line).getByTestId("hand-confirm-clone");
    expect(clone).toHaveAttribute("data-state", "cloned");
    expect(clone).toHaveTextContent("CLONED · karolswdev/holdspeak-dayone-rehearsal-1558 · 18:06");
    expect(within(line).queryByText(/^CLONES /)).toBeNull();
    // Where the clone lives, so the owner finds it after the refusal (Astra r2).
    expect(within(line).getByTestId("hand-confirm-clone-folder")).toHaveTextContent(
      "~/.holdspeak/repositories/karolswdev/holdspeak-dayone-rehearsal-1558/holdspeak-dayone-rehearsal-1558",
    );
  });

  it("the line names the clone's egress before the press and CLONED after it; never NO REPOSITORY", async () => {
    world.preview = {
      ...PREVIEW, repo: null as unknown as string, repo_label: "~/.holdspeak/repositories/karolswdev/r/r",
      clone: { repository: "karolswdev/holdspeak-dayone-rehearsal-1558", host: "github.com", state: "to_clone" },
    } as typeof PREVIEW;
    world.hand = () => ({
      status: "launched", launch_id: "launch-1", instruction_state: "sent", profile: "codex-default",
      clone: { repository: "karolswdev/holdspeak-dayone-rehearsal-1558", host: "github.com", state: "cloned" },
    });
    await renderDesk();
    dragOnto(comms(), conductor());
    const line = await within(drawer()).findByTestId("hand-confirm");
    const before = await within(line).findByTestId("hand-confirm-clone");
    expect(before).toHaveAttribute("data-state", "to_clone");
    expect(within(before).getByText("GITHUB.COM")).toBeTruthy();
    expect(within(before).getByText("CLONES karolswdev/holdspeak-dayone-rehearsal-1558")).toBeTruthy();
    expect(within(line).queryByText("NO REPOSITORY")).toBeNull();
    expect(within(line).getByRole("button", { name: "Hand" })).toBeEnabled();
    fireEvent.click(within(line).getByRole("button", { name: "Hand" }));
    await within(line).findByTestId("hand-confirm-receipt");
    const after = within(line).getByTestId("hand-confirm-clone");
    expect(after).toHaveAttribute("data-state", "cloned");
    expect(within(after).getByText("CLONED · karolswdev/holdspeak-dayone-rehearsal-1558")).toBeTruthy();
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
