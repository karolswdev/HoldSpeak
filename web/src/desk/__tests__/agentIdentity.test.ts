// PHILO-14 A0c r2 (Astra on #956): one rule, fenced once. Every face that
// draws an agent draws THAT agent: a Codex object wears the Codex sprite on
// the screen, in a Project drawer, in the Conductor, in Needs you, in the
// hand-off confirm line and in its lane's title, at 64 and at 32. A size-only
// check accepts the wrong agent's art, so this checks identity.
import { describe, expect, it } from "vitest";
import { EMPTY_ITEMS } from "../api";
import type { AgentFlight, CoderSessionRow } from "../agentFlights";
import { conductorMembers } from "../conductor/members";
import { drawerMembers } from "../drawer/members";
import { agentSprite } from "../hand/HandConfirm";
import { laneTitleSprite } from "../lane/LaneWindow";
import { needsRowSprite } from "../needs/NeedsDrawer";
import { composeScreen } from "../screen/compose";
import { SPRITE_BASE, listSprite } from "../sprites";

const flight = (agent: "claude" | "codex"): AgentFlight => ({
  originRef: `action:${agent}-1`, kind: "action", id: `${agent}-1`, title: `${agent} item`,
  projectId: "p-ledger", projectName: "Ledger", agent, state: "working",
  sessionKey: `${agent}:s1`, pr: null, close: null, sessionCleanup: null, mergedAt: null,
  launchId: `launch-${agent}`,
});

const session = (agent: "claude" | "codex"): CoderSessionRow => ({
  key: `${agent}:s1`, agent, sessionId: "s1", name: "payments-ledger", state: "working",
  blocked: false, question: "", flight: flight(agent),
}) as CoderSessionRow;

const file = (url: string | undefined) => String(url ?? "").slice(SPRITE_BASE.length);

/** The URL, and its 32 px list sibling, both name the agent's own sprite. */
function wears(url: string | undefined, agent: "claude" | "codex", where: string) {
  const name = agent === "codex" ? "agent-codex" : "agent-claude-code";
  expect(file(url), where).toMatch(new RegExp(`^(32/)?${name}(_sel|_stale)?\\.png$`));
  expect(file(listSprite(String(url))), `${where} at 32`).toMatch(new RegExp(`^32/${name}(_sel|_stale)?\\.png$`));
}

describe.each(["codex", "claude"] as const)("a %s agent keeps its face on every face", (agent) => {
  it("the screen (compose)", () => {
    const objects = composeScreen({
      items: { ...EMPTY_ITEMS } as never, projectCounts: {}, needsCount: 0, needsRefs: new Set(), heldCalls: 0,
      sessions: [session(agent)], flights: [flight(agent)], filed: new Set(), persons: [], membersLoaded: true,
    });
    const o = objects.find((x) => x.key === `coder:${agent}:s1`);
    expect(o, "the agent object").toBeTruthy();
    wears(o?.sprite, agent, "screen rest");
    wears(o?.spriteSelected, agent, "screen selected");
  });

  it("a Project drawer's members", () => {
    const members = drawerMembers({
      projectId: "p-ledger", projectName: "Ledger", room: null, meetings: [], decisions: [], artifacts: [],
      people: [], resources: [], flights: [flight(agent)], sessions: [session(agent)], items: EMPTY_ITEMS,
    });
    const m = members.find((x) => x.ref === `coder:${agent}:s1`);
    expect(m, "the agent member").toBeTruthy();
    wears(m?.sprite, agent, "drawer rest");
    wears(m?.spriteSelected, agent, "drawer selected");
  });

  it("the Conductor's rows", () => {
    const members = conductorMembers({
      detect: null, sessions: [session(agent)], flights: [flight(agent)], launchedAt: {},
    });
    expect(members.length).toBeGreaterThan(0);
    for (const m of members) {
      wears(m.sprite, agent, "conductor rest");
      wears(m.spriteSelected, agent, "conductor selected");
    }
  });

  it("a Needs you row", () => {
    wears(needsRowSprite({ id: `coder:${agent}:s1`, agent }), agent, "needs row");
  });

  it("the hand-off confirm line", () => {
    wears(agentSprite(agent), agent, "confirm line");
  });

  it("the lane's title", () => {
    const url = laneTitleSprite(agent, `${agent}:s1`);
    expect(file(url)).toBe(agent === "codex" ? "32/agent-codex.png" : "32/agent-claude-code.png");
  });
});
