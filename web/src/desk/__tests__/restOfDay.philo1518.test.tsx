/* PHILO-15 lane 18 — the rest of the first afternoon (rehearsal 1B):
 * B31 one sign-in truth (the words), B33 the Settings words read the route,
 * B36 the known-sign-in default, B56 a live aftercare card. The Conductor's B34/B35 fences live in
 * conductor/__tests__/conductor.test.tsx; B36's line in hand/__tests__/hand.test.tsx. */
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => mocks.apiFetch(...args) };
});

import { pickDefaultAgent } from "../agentHand";
import type { AgentsDetect } from "../firstrun/agentsStep";
import { dismissAftercare, publishAftercare, refreshAftercare, useAftercare } from "../intelligenceAttention";
import { PrefsFace, type SettingsHubWire } from "../../pages/cores/settingsPrefs";
import { chipLabel, stateWords } from "../../pages/cores/connections/ConnectionsPane";

const agent = (id: "claude" | "codex", signedIn: "yes" | "unknown", installed = true) => ({
  id, label: id, installed, path: installed ? `/bin/${id}` : null, version: "1", hooks: "installed" as const,
  signed_in: signedIn, ready: installed, verb: null,
});
const detect = (...agents: ReturnType<typeof agent>[]): AgentsDetect => ({
  agents, tmux: { installed: true, path: "/bin/tmux", install_hint: null },
});

describe("B36: the default agent is the first KNOWN sign-in", () => {
  it("Codex when Claude Code's sign-in is unknown, naming Claude Code as passed over", () => {
    expect(pickDefaultAgent(detect(agent("claude", "unknown"), agent("codex", "yes")))).toEqual({ agent: "codex", skipped: "claude" });
  });
  it("Claude Code when it is signed in, or when nobody's sign-in is known, or with no read", () => {
    expect(pickDefaultAgent(detect(agent("claude", "yes"), agent("codex", "yes")))).toEqual({ agent: "claude", skipped: null });
    expect(pickDefaultAgent(detect(agent("claude", "unknown"), agent("codex", "unknown")))).toEqual({ agent: "claude", skipped: null });
    expect(pickDefaultAgent(null)).toEqual({ agent: "claude", skipped: null });
  });
  it("Codex with no Claude Code installed says nothing passed over", () => {
    expect(pickDefaultAgent(detect(agent("claude", "unknown", false), agent("codex", "yes")))).toEqual({ agent: "codex", skipped: null });
  });
});

describe("B31: a gh-file sign-in reads Signed in, with gh's time", () => {
  it("names when gh stored it, never a check", () => {
    const when = new Date(Date.now() - 3 * 3600_000).toISOString();
    expect(chipLabel("signed_in", "github")).toBe("Signed in");
    expect(stateWords("signed_in", "github", { last_checked_at: when })).toBe("Signed in · gh 3 h ago");
    expect(stateWords("signed_in", "github", {})).toBe("Signed in");
  });
});

const hub = (patch: Partial<SettingsHubWire> = {}): SettingsHubWire => ({
  models: { engines: 1, groupsSet: 0, defaultSet: false },
  connections: { connected: 0 },
  voice: { live: true, target: "auto", engineSet: false },
  meetings: { intelligence: true, engineSet: true, summariesOff: false, auto: "every", host: "192.168.1.43" },
  rhythm: { loops: 0 },
  sounds: { on: true },
  system: { host: "this device", mesh: false },
  posture: "neutral",
  writtenAt: null,
  ...patch,
});
const face = (wire: SettingsHubWire) =>
  render(<PrefsFace onOpen={vi.fn()} hub={wire} posture="neutral" onPosture={vi.fn()} precedence={[]} />);

describe("B33: the Settings hub reads the summary route", () => {
  it("summaries on the LAN box with no default: All set, no SUMMARY · NO ENGINE, NO DEFAULT is a quiet fact", () => {
    face(hub());
    expect(screen.getByText("All set")).toBeTruthy();
    expect(screen.queryByText("No default model")).toBeNull();
    expect(screen.queryByText("SUMMARY · NO ENGINE")).toBeNull();
    const noDefault = screen.getByRole("status", { name: "NO DEFAULT" });
    expect(noDefault.getAttribute("data-state")).toBe("idle");
  });
  it("no route and no default: the warning stays", () => {
    face(hub({ meetings: { intelligence: true, engineSet: false, auto: "every" } }));
    expect(screen.getByText("No default model")).toBeTruthy();
    expect(screen.getByText("SUMMARY · NO ENGINE")).toBeTruthy();
    expect(screen.getByRole("status", { name: "NO DEFAULT" }).getAttribute("data-state")).toBe("warning");
  });
  it("the owner's OFF reads SUMMARIES OFF, not a missing engine", () => {
    face(hub({ meetings: { intelligence: true, engineSet: false, summariesOff: true, auto: "every" } }));
    expect(screen.getByText("SUMMARIES OFF")).toBeTruthy();
    expect(screen.queryByText("SUMMARY · NO ENGINE")).toBeNull();
  });
});

function Probe() {
  const signal = useAftercare();
  return <span data-testid="probe">{signal ? `${signal.proposalTotal}/${signal.openTotal}` : "none"}</span>;
}

describe("B56: the aftercare card's counts are the hub's", () => {
  beforeEach(() => {
    mocks.apiFetch.mockReset();
    dismissAftercare();
  });
  const frame = { meeting_id: "m-1", title: "Payments ledger sync", proposal_total: 2, open_total: 1, decided_total: 0 };

  it("a card with proposals leaves when the hub's to-review count reaches zero", async () => {
    render(<Probe />);
    publishAftercare(frame);
    mocks.apiFetch.mockResolvedValueOnce({ proposal_total: 1, open_items: { total: 1 }, decisions: [] });
    await refreshAftercare();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/meetings/m-1/aftercare");
    expect(await screen.findByText("1/1")).toBeTruthy();
    mocks.apiFetch.mockResolvedValueOnce({ proposal_total: 0, open_items: { total: 0 }, decisions: [] });
    await refreshAftercare();
    expect(await screen.findByText("none")).toBeTruthy();
  });

  it("an unread answer keeps the card as it was", async () => {
    render(<Probe />);
    publishAftercare(frame);
    mocks.apiFetch.mockRejectedValueOnce(new Error("hub down"));
    await refreshAftercare();
    expect(screen.getByTestId("probe").textContent).toBe("2/1");
  });
});
