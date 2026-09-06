// HS-111-06 — species smoke locks (audit §4.4): the census fold, the
// shared PaneWell seam, the dossier's named empty-command token, and
// the lifecycle surface-token.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { McSession } from "../missioncontrol";
import { useDeliveryDossier, type StoryDossier } from "../deliveryDossier";
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
    expect(screen.getByText("NO COMMAND RECORDED")).toBeTruthy();
    expect(screen.getByText("uv run pytest -q")).toBeTruthy();
    expect(screen.getByText("EXIT 1")).toBeTruthy();
    expect(screen.getByText("RUNS 1 PASS 1 FAIL")).toBeTruthy();
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
