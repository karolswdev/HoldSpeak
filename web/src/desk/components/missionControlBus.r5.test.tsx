// Conductor R5: the conveyor listened for a DOM `hs-broadcast` event that
// nothing sends, so a coder or belt frame never moved it before the next poll.
// It now reads the one runtime bus (useOnCoderFrame for `scope:"coder"`).
import { act, cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fromWireMcRepo, fromWireMcSession, useMissionControl } from "../missioncontrol";
import { useProjections } from "../projections";
import { useSteering } from "../steering";
import { MissionControlConveyor } from "./MissionControlConveyor";

const bus = vi.hoisted(() => ({ handlers: new Map<string, Set<(frame: unknown) => void>>() }));

vi.mock("../../runtime/RuntimeBus", () => {
  const value = {
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      const set = bus.handlers.get(type) ?? new Set();
      set.add(handler);
      bus.handlers.set(type, set);
      return () => set.delete(handler);
    },
  };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

// Control-boundary tests seed the view store directly. The real hub and
// browser observation cover the wire and session window beyond these seams.
describe("Rails conditional action controls", () => {
  const openSession = vi.fn((key: string) => useSteering.setState({ openKey: key }));
  const openEvidence = vi.fn(async (_repo: string, _project: string, story: string) => {
    useMissionControl.setState({ evidence: { storyId: story, path: "checkpoint-evidence.md", text: "Exact checkpoint evidence" } });
  });
  let savedMc: ReturnType<typeof useMissionControl.getState>;
  let savedSteering: ReturnType<typeof useSteering.getState>;
  let savedProjections: ReturnType<typeof useProjections.getState>;

  beforeEach(() => {
    savedMc = useMissionControl.getState();
    savedSteering = useSteering.getState();
    savedProjections = useProjections.getState();
    openSession.mockClear();
    openEvidence.mockClear();
    const phase = { number: 12, title: "Migration", status: "open", stories_done: 1, stories_total: 2 };
    useMissionControl.setState({
      repos: [fromWireMcRepo({ name: "architecture", status: "live", feed: { projects: [{
        slug: "migration", prefix: "ARC", current_phase: phase, phases: [phase],
        stories: [
          { story_id: "ARC-12-01", title: "Checkpoints", phase: 12, status: "in-progress", evidence_exists: true },
          { story_id: "ARC-12-02", title: "Rollback", phase: 12, status: "ready", evidence_exists: false },
        ],
      }] } })],
      sessions: [
        fromWireMcSession({ key: "claude:on-belt", agent: "claude", correlation: "on_story", stories: [{ story_id: "ARC-12-01", project: "migration" }], awaiting_response: true }),
        fromWireMcSession({ key: "codex:manual", agent: "codex", correlation: "off_rails", stories: [] }),
        fromWireMcSession({ key: "claude:awaiting-review", agent: "claude", correlation: "off_rails", stories: [], awaiting_response: true }),
      ],
      updatedAt: 1, open: true, events: [], evidence: null, evidenceDetail: "", proposal: null,
      refresh: vi.fn(async () => {}), openEvidence,
    });
    useSteering.setState({
      openKey: null, openSession, armedKeys: {}, manualPins: { "codex:manual": "ARC-12-02" }, refreshGrants: vi.fn(async () => {}),
    });
    useProjections.setState({ ambientTotal: 0, refreshAmbient: vi.fn(async () => {}) });
  });

  afterEach(() => {
    cleanup();
    useMissionControl.setState(savedMc, true);
    useSteering.setState(savedSteering, true);
    useProjections.setState(savedProjections, true);
  });

  it("Story selection toggles the rendered exact Story without opening another control", async () => {
    const user = userEvent.setup();
    render(<MissionControlConveyor />);
    const story = screen.getByRole("button", { name: "ARC-12-01" });
    expect(story).toHaveClass("btn", "btn--ghost", "btn--sm");
    expect(screen.getByRole("button", { name: "ARC-12-02" })).toHaveAttribute("aria-pressed", "false");
    await user.click(story);
    expect(story).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("FLIP ARC-12-01")).toBeTruthy();
    expect(screen.getByRole("button", { name: "ARC-12-02" })).toHaveAttribute("aria-pressed", "false");
    await user.click(story);
    expect(story).toHaveAttribute("aria-pressed", "false");
    expect(screen.queryByText("FLIP ARC-12-01")).toBeNull();
    expect(openSession).not.toHaveBeenCalled();
    expect(openEvidence).not.toHaveBeenCalled();
  });

  it("duplicate Story ids keep repo and project selection distinct and route the exact target", async () => {
    const user = userEvent.setup();
    const repoA = useMissionControl.getState().repos[0];
    const proposeFlip = vi.fn(async () => {});
    useMissionControl.setState({
      repos: [repoA, {
        ...repoA,
        name: "architecture-copy",
        projects: [{ ...repoA.projects[0], slug: "migration-copy" }],
      }],
      sessions: [],
      proposeFlip,
    });
    render(<MissionControlConveyor />);
    const [storyA, storyB] = screen.getAllByRole("button", { name: "ARC-12-01" });
    await user.click(storyA);
    expect(storyA).toHaveAttribute("aria-pressed", "true");
    expect(storyB).toHaveAttribute("aria-pressed", "false");
    await user.click(storyB);
    expect(storyA).toHaveAttribute("aria-pressed", "false");
    expect(storyB).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("FLIP ARC-12-01")).toBeTruthy();
    await user.click(storyB);
    expect(storyB).toHaveAttribute("aria-pressed", "false");
    expect(screen.queryByText("FLIP ARC-12-01")).toBeNull();
    await user.click(storyB);
    await user.click(screen.getByText("READY"));
    expect(screen.getByRole("radio", { name: "READY" })).toBeChecked();
    await user.click(screen.getByRole("button", { name: "PROPOSE" }));
    await user.click(screen.getByRole("button", { name: "PROPOSE?" }));
    expect(proposeFlip).toHaveBeenCalledOnce();
    expect(proposeFlip).toHaveBeenCalledWith("architecture-copy", "migration-copy", "ARC-12-01", "ready");
  });

  it("pins and evidence keep exact record identities and stop the Story click", async () => {
    const user = userEvent.setup();
    const parentClick = vi.fn();
    render(<div onClick={parentClick}><MissionControlConveyor /></div>);
    const pin = screen.getByRole("button", { name: /claude NEEDS YOU/ });
    expect(pin).toHaveClass("btn", "btn--ghost", "btn--sm", "awaiting");
    await user.click(pin);
    expect(openSession).toHaveBeenLastCalledWith("claude:on-belt");
    expect(useSteering.getState().openKey).toBe("claude:on-belt");
    const manualPin = screen.getByRole("button", { name: "⌁codex" });
    expect(manualPin).toHaveClass("btn", "manual");
    await user.click(manualPin);
    expect(openSession).toHaveBeenLastCalledWith("codex:manual");
    expect(useSteering.getState().openKey).toBe("codex:manual");
    const evidence = screen.getByRole("button", { name: "Open evidence for ARC-12-01" });
    expect(evidence).toHaveClass("btn", "btn--ghost", "btn--sm");
    await user.click(evidence);
    expect(openEvidence).toHaveBeenCalledOnce();
    expect(openEvidence).toHaveBeenCalledWith("architecture", "migration", "ARC-12-01");
    expect(screen.getByText("Exact checkpoint evidence")).toBeTruthy();
    expect(screen.getByText("Evidence ARC-12-01")).toBeTruthy();
    expect(parentClick).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "ARC-12-01" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.queryByText("FLIP ARC-12-01")).toBeNull();
  });

  it("waiting session uses native keyboard activation for its exact key once", async () => {
    const user = userEvent.setup();
    render(<MissionControlConveyor />);
    const waiting = screen.getByRole("button", { name: "NEEDS YOU · claude · awaiting" });
    expect(waiting).toHaveClass("btn", "btn--ghost", "btn--sm", "desk-mc-needs");
    waiting.focus();
    await user.keyboard("{Enter}");
    expect(openSession).toHaveBeenCalledOnce();
    expect(openSession).toHaveBeenCalledWith("claude:awaiting-review");
    expect(useSteering.getState().openKey).toBe("claude:awaiting-review");
    expect(openEvidence).not.toHaveBeenCalled();
  });
});

function emit(frame: { type: string; data: unknown }) {
  for (const handler of bus.handlers.get(frame.type) ?? []) handler(frame);
}

describe("Mission Control follows the runtime bus (Conductor R5)", () => {
  const mcRefresh = vi.fn(async () => {});
  const grants = vi.fn(async () => {});
  const ambient = vi.fn(async () => {});
  const projRefresh = vi.fn(async () => {});
  let saved: {
    mc: ReturnType<typeof useMissionControl.getState>["refresh"];
    grants: ReturnType<typeof useSteering.getState>["refreshGrants"];
    ambient: ReturnType<typeof useProjections.getState>["refreshAmbient"];
    proj: ReturnType<typeof useProjections.getState>["refresh"];
  };

  beforeEach(() => {
    bus.handlers.clear();
    for (const fn of [mcRefresh, grants, ambient, projRefresh]) fn.mockClear();
    saved = {
      mc: useMissionControl.getState().refresh,
      grants: useSteering.getState().refreshGrants,
      ambient: useProjections.getState().refreshAmbient,
      proj: useProjections.getState().refresh,
    };
    useMissionControl.setState({ refresh: mcRefresh });
    useSteering.setState({ refreshGrants: grants });
    useProjections.setState({ refreshAmbient: ambient, refresh: projRefresh });
  });

  afterEach(() => {
    useMissionControl.setState({ refresh: saved.mc });
    useSteering.setState({ refreshGrants: saved.grants });
    useProjections.setState({ refreshAmbient: saved.ambient, refresh: saved.proj });
  });

  it("re-reads the pins and the belt on a coder frame", () => {
    render(<MissionControlConveyor />);
    expect(mcRefresh).toHaveBeenCalledTimes(1); // the mount tick
    expect(grants).toHaveBeenCalledTimes(1);

    act(() => emit({ type: "intel_status", data: { state: "ready", scope: "coder" } }));

    expect(mcRefresh).toHaveBeenCalledTimes(2);
    expect(grants).toHaveBeenCalledTimes(2);
    expect(ambient).toHaveBeenCalledTimes(2);
    expect(projRefresh).toHaveBeenCalledWith(true);
  });

  it("re-reads the belt only on a belt frame", () => {
    render(<MissionControlConveyor />);
    act(() => emit({ type: "intel_status", data: { scope: "belt" } }));
    expect(mcRefresh).toHaveBeenCalledTimes(2);
    expect(grants).toHaveBeenCalledTimes(1);
    expect(projRefresh).not.toHaveBeenCalled();
  });
});
