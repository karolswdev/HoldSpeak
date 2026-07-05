// Mission-control wire normalizers (HS-82-03/04) — pure-logic tests
// in the desk's established style: the wire is the bridge's relay of
// the Delivery Workbench documents; the view shapes are what the
// belt renders. Honest statuses stay honest through normalization.
import { describe, expect, it } from "vitest";
import {
  formatEvent,
  fromWireMcEvents,
  fromWireMcRepo,
  fromWireMcSession,
  offBeltSessions,
  sessionsByStory,
} from "../missioncontrol";

const LIVE_ENTRY = {
  name: "delivery-workbench",
  path: "/repos/dw",
  status: "live",
  feed: {
    feed_schema: 1,
    projects: [
      {
        slug: "work-log-automation",
        prefix: "WLA",
        current_phase: {
          number: 13, title: "Mission control", status: "open",
          stories_done: 5, stories_total: 6,
        },
        next_story: { story_id: "WLA-13-05", title: "Desk proof", status: "backlog" },
        phases: [
          { number: 12, title: "Riders", status: "closed", stories_done: 8, stories_total: 8 },
          { number: 13, title: "Mission control", status: "open", stories_done: 5, stories_total: 6 },
        ],
        stories: [
          { story_id: "WLA-13-06", title: "Telegram", status: "done", phase: 13, evidence_exists: true },
          { story_id: "WLA-13-05", title: "Desk proof", status: "backlog", phase: 13, evidence_exists: false },
        ],
        warnings: 2,
      },
    ],
  },
};

describe("fromWireMcRepo", () => {
  it("normalizes a live feed into belt shapes", () => {
    const repo = fromWireMcRepo(LIVE_ENTRY);
    expect(repo.status).toBe("live");
    const project = repo.projects[0];
    expect(project.slug).toBe("work-log-automation");
    expect(project.currentPhase).toMatchObject({ number: 13, storiesDone: 5, storiesTotal: 6 });
    expect(project.nextStoryId).toBe("WLA-13-05");
    expect(project.phases.map((p) => p.status)).toEqual(["closed", "open"]);
    expect(project.stories[0]).toMatchObject({
      storyId: "WLA-13-06", evidenceExists: true, phase: 13,
    });
    expect(project.warnings).toBe(2);
  });

  it("keeps compatibility honest: no projects invented", () => {
    const repo = fromWireMcRepo({
      name: "dw", path: "/x", status: "compatibility",
      detail: "feed_schema 2 is not the schema this desk was proven against (1)",
    });
    expect(repo.status).toBe("compatibility");
    expect(repo.projects).toEqual([]);
    expect(repo.detail).toContain("proven against");
  });

  it("treats malformed entries as unreachable, not live", () => {
    expect(fromWireMcRepo({}).status).toBe("unreachable");
  });
});

describe("fromWireMcSession", () => {
  it("carries the declared field list and nothing invented", () => {
    const s = fromWireMcSession({
      key: "claude:s1", agent: "claude", correlation: "on_story",
      stories: [{ story_id: "WLA-13-05" }], awaiting_response: true,
      last_assistant_text: "Ship it?", stale: false,
      tmux: { session: "gate" },
    });
    expect(s).toMatchObject({
      key: "claude:s1", correlation: "on_story",
      storyIds: ["WLA-13-05"], awaitingResponse: true,
      stale: false, tmuxSession: "gate",
    });
  });

  it("defaults honestly when tmux is absent", () => {
    const s = fromWireMcSession({ key: "k", agent: "codex", correlation: "off_rails" });
    expect(s.tmuxSession).toBeNull();
    expect(s.storyIds).toEqual([]);
  });
});

describe("the belt's live layer (HS-82-04)", () => {
  const onStory = fromWireMcSession({
    key: "claude:s1", agent: "claude", correlation: "on_story",
    stories: [{ story_id: "WLA-13-05" }], awaiting_response: true,
  });
  const offRails = fromWireMcSession({
    key: "codex:s2", agent: "codex", correlation: "off_rails",
  });
  const ambiguous = fromWireMcSession({
    key: "claude:s3", agent: "claude", correlation: "ambiguous",
    stories: [{ story_id: "A-1-01" }, { story_id: "A-1-02" }],
  });

  it("pins on_story sessions to their stories", () => {
    const pins = sessionsByStory([onStory, offRails, ambiguous]);
    expect(Object.keys(pins)).toEqual(["WLA-13-05"]);
    expect(pins["WLA-13-05"][0].awaitingResponse).toBe(true);
  });

  it("keeps ambiguous sessions off the belt — unknown beats guessed", () => {
    const off = offBeltSessions([onStory, offRails, ambiguous]);
    expect(off.map((s) => s.key)).toEqual(["codex:s2", "claude:s3"]);
  });

  it("formats a refusal with its rule id verbatim", () => {
    const line = formatEvent({
      ts: "2026-07-04T12:00:00Z", event: "gate_refusal",
      story: "WLA-13-05", detail: { rule: "story-evidence" }, repo: "dw",
    });
    expect(line).toBe("12:00:00  gate_refusal  WLA-13-05  rule=story-evidence");
  });
});

describe("fromWireMcEvents", () => {
  it("flattens live events and tags the repo", () => {
    const events = fromWireMcEvents({
      name: "dw", status: "live",
      events: [
        { ts: "2026-07-04T12:00:00Z", event: "gate_refusal", story: "WLA-13-05", detail: { rule: "story-evidence" } },
      ],
    });
    expect(events[0]).toMatchObject({
      event: "gate_refusal", repo: "dw", detail: { rule: "story-evidence" },
    });
  });

  it("yields nothing from an unavailable repo (never fabricates)", () => {
    expect(fromWireMcEvents({ name: "dw", status: "unavailable" })).toEqual([]);
  });
});
