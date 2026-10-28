// HS-111-06 — species smoke locks (audit §4.4): the census fold, the
// shared PaneWell seam, the dossier's named empty-command token, and
// the lifecycle surface-token.
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { McSession } from "../missioncontrol";
import { fromWirePhaseDossier, fromWireStoryDossier, useDeliveryDossier, type StoryDossier } from "../deliveryDossier";
import phaseFixture from "../../../../apple/Tests/ContractsTests/Fixtures/delivery_phase_dossier.json";
import storyFixture from "../../../../apple/Tests/ContractsTests/Fixtures/delivery_story_dossier.json";
import { PaneWell } from "../surface/Surface";
import { censusByAgent } from "./MissionControlConveyor";
import { DeliveryDossierWindow } from "./DeliveryDossierWindow";
import { LifecycleChip } from "../../pages/cores/ProjectMemoryCore";

function session(over: Partial<McSession>): McSession {
  return {
    key: "claude:s1",
    agent: "claude",
    correlation: "off_rails",
    storyIds: [],
    storyRefs: [],
    awaitingResponse: false,
    lastAssistantText: "",
    stale: false,
    tmuxSession: null,
    ...over,
  };
}

describe("censusByAgent (the pin-flood fold)", () => {
  it("folds off-belt sessions into one line per agent; needs-you stays out", () => {
    const sessions: McSession[] = [
      session({ key: "claude:1", correlation: "off_rails" }),
      session({ key: "claude:2", correlation: "off_rails" }),
      session({ key: "claude:3", correlation: "ambiguous" }),
      session({ key: "claude:4", correlation: "off_rails", stale: true }),
      // Awaiting: the needs-you layer renders this one individually.
      session({ key: "claude:5", awaitingResponse: true }),
      // On-story: pins to its story cell, never censused.
      session({ key: "claude:6", correlation: "on_story" }),
      session({ key: "codex:1", agent: "codex", correlation: "off_rails" }),
    ];
    const census = censusByAgent(sessions);
    expect(census.map((row) => `${row.agent} ${row.total}`)).toEqual([
      "claude 4",
      "codex 1",
    ]);
    const claude = census[0];
    expect(claude.buckets).toEqual([
      { token: "OFF RAILS", count: 2 },
      { token: "AMBIGUOUS", count: 1 },
      { token: "IDLE", count: 1 },
    ]);
  });
});

describe("PaneWell (the one terminal seam)", () => {
  it("mounts the sunken mono pane while live", () => {
    const { container } = render(
      <PaneWell live lines={["$ uv run pytest", "ok"]} />,
    );
    const pre = container.querySelector("pre.desk-session-pane");
    expect(pre?.textContent).toBe("$ uv run pytest\nok");
  });

  it("renders the honest absence face otherwise", () => {
    const { container } = render(
      <PaneWell live={false} lines={[]} absence={<>✕ target gone</>} />,
    );
    expect(container.querySelector("pre.desk-session-pane")).toBeNull();
    expect(screen.getByText(/target gone/)).toBeTruthy();
  });
});

describe("DeliveryDossierWindow captured runs", () => {
  it("names an empty command as a token, never a bare mark", () => {
    const dossier: StoryDossier = {
      kind: "story",
      bundleId: "bun_1",
      bundleChanged: false,
      freshness: "live",
      detail: "",
      sourceId: "src_a",
      project: "holdspeak",
      storyId: "HS-109-01",
      phase: 109,
      status: "done",
      headSha: "4ad164dd0000",
      indexTree: "tree_1",
      summary: { assets: 0, passing: 1, failing: 1 },
      members: [],
      capturedRuns: [
        {
          timestamp: "2026-07-30T10:00:00Z",
          command: "uv run pytest -q",
          exitCode: 0,
          passed: true,
        },
        { timestamp: "2026-07-30T10:05:00Z", command: "", exitCode: 1, passed: false },
      ],
      storyMarkdown: null,
      evidenceMarkdown: null,
    };
    useDeliveryDossier.setState({ dossier, loading: false, refusal: null });
    render(<DeliveryDossierWindow />);
    expect(screen.getByText("No command recorded")).toBeTruthy();
    expect(screen.getByText("uv run pytest -q")).toBeTruthy();
    expect(screen.getByText("Exit 1")).toBeTruthy();
    expect(screen.getByText("Runs 1 pass 1 fail")).toBeTruthy();
    useDeliveryDossier.setState({ dossier: null });
  });

  it("a story dossier window is named by the story's title, not `Dossier <id>`", () => {
    const dossier = {
      kind: "story", bundleId: "bun_1", bundleChanged: false, freshness: "live", detail: "", sourceId: "src_a",
      project: "holdspeak", storyId: "HS-109-01", phase: 109, status: "done", headSha: "4ad164dd0000", indexTree: "tree_1",
      summary: { assets: 0, passing: 0, failing: 0 }, members: [], capturedRuns: [],
      storyMarkdown: "# The long memory keeps its receipts\n\nStatus: done\n", evidenceMarkdown: null,
    } as StoryDossier;
    useDeliveryDossier.setState({ dossier, loading: false, refusal: null });
    render(<DeliveryDossierWindow />);
    expect(screen.getByRole("region", { name: "The long memory keeps its receipts" })).toBeTruthy();
    expect(screen.queryByRole("region", { name: /^Dossier / })).toBeNull();
    useDeliveryDossier.setState({ dossier: null });
  });
});

describe("LifecycleChip (pill → token)", () => {
  it("wears the surface-token species with an honest tone", () => {
    const { container } = render(
      <LifecycleChip row={{ lifecycle: "accepted" }} />,
    );
    const token = container.querySelector(".surface-token");
    expect(token?.textContent).toBe("Accepted");
    expect(token?.getAttribute("data-tone")).toBe("ok");
    expect(container.querySelector(".signal-status")).toBeNull();
  });
});

describe("Delivery phase Story control", () => {
  it.each([
    { passing: 0, failing: 0, expected: null },
    { passing: 2, failing: 0, expected: "2 pass" },
    { passing: 0, failing: 3, expected: "3 fail" },
    { passing: 2, failing: 1, expected: "2 pass · 1 fail" },
  ])("shows only positive phase facts for $passing pass and $failing fail", ({ passing, failing, expected }) => {
    const saved = useDeliveryDossier.getState();
    try {
      const dossier = fromWirePhaseDossier(phaseFixture);
      dossier.stories[0] = { ...dossier.stories[0], passing, failing };
      useDeliveryDossier.setState({ dossier, loading: false, refusal: null });
      const { container } = render(<DeliveryDossierWindow />);
      expect(screen.getByRole("button", { name: "HS-94-05 · Evidence dossiers and safe assets" })).toBeTruthy();
      const facts = container.querySelector(".desk-dlv-phase-stories small");
      if (expected === null) expect(facts).toBeNull();
      else expect(facts?.textContent).toBe(expected);
      expect(screen.queryByRole("button", { name: /HS-94-10/ })).toBeNull();
    } finally {
      cleanup();
      useDeliveryDossier.setState(saved, true);
    }
  });

  it("opens only the ready Story by its exact project and id through the library Button", async () => {
    const saved = useDeliveryDossier.getState();
    const openStory = vi.fn(async () => useDeliveryDossier.setState({ dossier: fromWireStoryDossier(storyFixture) }));
    const user = userEvent.setup();
    try {
      useDeliveryDossier.setState({ dossier: fromWirePhaseDossier(phaseFixture), loading: false, refusal: null, openStory });
      render(<DeliveryDossierWindow />);
      const ready = screen.getByRole("button", { name: "HS-94-05 · Evidence dossiers and safe assets" });
      expect(ready).toHaveClass("btn", "btn--ghost", "btn--sm");
      expect(screen.queryByRole("button", { name: /HS-94-10/ })).toBeNull();
      expect(screen.getByText("HS-94-10 · not found")).toBeTruthy();
      ready.focus();
      await user.keyboard(" ");
      expect(openStory).toHaveBeenCalledOnce();
      expect(openStory).toHaveBeenCalledWith("holdspeak", "HS-94-05");
      expect(screen.queryByRole("button", { name: "HS-94-05 · Evidence dossiers and safe assets" })).toBeNull();
      expect(screen.getByText("Runs 1 pass 1 fail")).toBeTruthy();
    } finally {
      cleanup();
      useDeliveryDossier.setState(saved, true);
    }
  });
});
