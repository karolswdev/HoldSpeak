// Mission-control wire normalizers (HS-82-03/04) — pure-logic tests
// in the desk's established style: the wire is the bridge's relay of
// the Delivery Workbench documents; the view shapes are what the
// belt renders. Honest statuses stay honest through normalization.
import { describe, expect, it } from "vitest";
import {
  flipTargetForStory,
  formatEvent,
  fromWireMcEvents,
  fromWireMcRepo,
  fromWireMcSession,
  offBeltSessions,
  sessionsByStory,
} from "../missioncontrol";
import { manualPinsByStory } from "../components/MissionControlConveyor";

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
          number: 13,
          title: "Mission control",
          status: "open",
          stories_done: 5,
          stories_total: 6,
        },
        next_story: {
          story_id: "WLA-13-05",
          title: "Desk proof",
          status: "backlog",
        },
        phases: [
          {
            number: 12,
            title: "Riders",
            status: "closed",
            stories_done: 8,
            stories_total: 8,
          },
          {
            number: 13,
            title: "Mission control",
            status: "open",
            stories_done: 5,
            stories_total: 6,
          },
        ],
        stories: [
          {
            story_id: "WLA-13-06",
            title: "Telegram",
            status: "done",
            phase: 13,
            evidence_exists: true,
          },
          {
            story_id: "WLA-13-05",
            title: "Desk proof",
            status: "backlog",
            phase: 13,
            evidence_exists: false,
          },
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
    expect(project.currentPhase).toMatchObject({
      number: 13,
      storiesDone: 5,
      storiesTotal: 6,
    });
    expect(project.nextStoryId).toBe("WLA-13-05");
    expect(project.phases.map((p) => p.status)).toEqual(["closed", "open"]);
    expect(project.stories[0]).toMatchObject({
      storyId: "WLA-13-06",
      evidenceExists: true,
      phase: 13,
    });
    expect(project.warnings).toBe(2);
  });

  it("keeps compatibility honest: no projects invented", () => {
    const repo = fromWireMcRepo({
      name: "dw",
      path: "/x",
      status: "compatibility",
      detail:
        "feed_schema 2 is not the schema this desk was proven against (1)",
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
      key: "claude:s1",
      agent: "claude",
      correlation: "on_story",
      stories: [{ story_id: "WLA-13-05" }],
      awaiting_response: true,
      last_assistant_text: "Ship it?",
      stale: false,
      tmux: { session: "gate" },
    });
    expect(s).toMatchObject({
      key: "claude:s1",
      correlation: "on_story",
      storyIds: ["WLA-13-05"],
      awaitingResponse: true,
      stale: false,
      tmuxSession: "gate",
    });
  });

  it("defaults honestly when tmux is absent", () => {
    const s = fromWireMcSession({
      key: "k",
      agent: "codex",
      correlation: "off_rails",
    });
    expect(s.tmuxSession).toBeNull();
    expect(s.storyIds).toEqual([]);
  });

  it("carries story refs with their project for flip-from-here (HS-87-05)", () => {
    const s = fromWireMcSession({
      key: "claude:s1",
      agent: "claude",
      correlation: "on_story",
      stories: [{ story_id: "HS-87-05", project: "holdspeak" }],
    });
    expect(s.storyRefs).toEqual([
      { storyId: "HS-87-05", project: "holdspeak" },
    ]);
  });
});

describe("the belt's live layer (HS-82-04)", () => {
  const onStory = fromWireMcSession({
    key: "claude:s1",
    agent: "claude",
    correlation: "on_story",
    stories: [{ story_id: "WLA-13-05" }],
    awaiting_response: true,
  });
  const offRails = fromWireMcSession({
    key: "codex:s2",
    agent: "codex",
    correlation: "off_rails",
  });
  const ambiguous = fromWireMcSession({
    key: "claude:s3",
    agent: "claude",
    correlation: "ambiguous",
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
      ts: "2026-07-04T12:00:00Z",
      event: "gate_refusal",
      story: "WLA-13-05",
      detail: { rule: "story-evidence" },
      repo: "dw",
    });
    expect(line).toBe("12:00:00  gate_refusal  WLA-13-05  rule=story-evidence");
  });
});

describe("fromWireMcEvents", () => {
  it("flattens live events and tags the repo", () => {
    const events = fromWireMcEvents({
      name: "dw",
      status: "live",
      events: [
        {
          ts: "2026-07-04T12:00:00Z",
          event: "gate_refusal",
          story: "WLA-13-05",
          detail: { rule: "story-evidence" },
        },
      ],
    });
    expect(events[0]).toMatchObject({
      event: "gate_refusal",
      repo: "dw",
      detail: { rule: "story-evidence" },
    });
  });

  it("yields nothing from an unavailable repo (never fabricates)", () => {
    expect(fromWireMcEvents({ name: "dw", status: "unavailable" })).toEqual([]);
  });
});

// ── HS-86-04: receipts, station lights, belt frames ──────────────

import {
  ciLight,
  gateLightFor,
  isBeltFrame,
  mergeReceipts,
} from "../missioncontrol";

describe("ciLight", () => {
  it("any failure-shaped conclusion wins", () => {
    expect(
      ciLight([{ conclusion: "SUCCESS" }, { conclusion: "FAILURE" }, {}]),
    ).toBe("fail");
    expect(
      ciLight([{ conclusion: "SUCCESS" }, { conclusion: "CANCELLED" }]),
    ).toBe("fail");
  });
  it("pending beats pass; all green is pass; no checks is none, never a fake green", () => {
    expect(ciLight([{ conclusion: "SUCCESS" }, { conclusion: "" }])).toBe(
      "pending",
    );
    expect(
      ciLight([{ conclusion: "SUCCESS" }, { conclusion: "SUCCESS" }]),
    ).toBe("pass");
    expect(ciLight([])).toBe("none");
  });
});

describe("mergeReceipts", () => {
  const repo = fromWireMcRepo(LIVE_ENTRY);
  it("folds live receipts into the repo by name", () => {
    const merged = mergeReceipts([repo], {
      repos: [
        {
          name: "delivery-workbench",
          status: "live",
          prs: [
            {
              number: 7,
              title: "flagship",
              url: "https://x/pr/7",
              headRefName: "flagship-tree",
              statusCheckRollup: [{ conclusion: "SUCCESS" }],
            },
          ],
        },
      ],
    });
    expect(merged[0].receipts).toBe("live");
    expect(merged[0].prs[0]).toEqual({
      number: 7,
      title: "flagship",
      url: "https://x/pr/7",
      branch: "flagship-tree",
      ci: "pass",
    });
  });
  it("keeps absence typed: unavailable receipts and unknown repos stay honest", () => {
    const merged = mergeReceipts([repo], {
      repos: [
        { name: "delivery-workbench", status: "unavailable", detail: "no gh" },
      ],
    });
    expect(merged[0].receipts).toBe("unavailable");
    expect(merged[0].prs).toEqual([]);
    expect(mergeReceipts([repo], null)[0].receipts).toBe("unknown");
  });
});

describe("gateLightFor", () => {
  const events = [
    {
      ts: "t3",
      event: "gate_refusal",
      story: "A-1-01",
      detail: { rule: "story-evidence" },
      repo: "hs",
    },
    { ts: "t2", event: "gate_pass", story: "A-1-01", detail: {}, repo: "hs" },
    { ts: "t1", event: "gate_pass", story: "B-1-01", detail: {}, repo: "dw" },
  ];
  it("the newest gate event for the repo speaks, refusals carry their rule", () => {
    expect(gateLightFor(events as any, "hs")).toEqual({
      state: "refusal",
      rule: "story-evidence",
    });
    expect(gateLightFor(events as any, "dw")).toEqual({
      state: "pass",
      rule: "",
    });
    expect(gateLightFor(events as any, "other")).toEqual({
      state: "none",
      rule: "",
    });
  });
});

describe("isBeltFrame", () => {
  it("matches only intel_status frames with scope belt", () => {
    expect(isBeltFrame({ type: "intel_status", data: { scope: "belt" } })).toBe(
      true,
    );
    expect(isBeltFrame({ type: "intel_status", data: { scope: "run" } })).toBe(
      false,
    );
    expect(isBeltFrame({ type: "segment", data: { scope: "belt" } })).toBe(
      false,
    );
    expect(isBeltFrame(null)).toBe(false);
  });
});

describe("classify verbs (HS-87-05)", () => {
  const repos = [
    {
      name: "code",
      status: "live",
      projects: [{ slug: "holdspeak" }, { slug: "other" }],
    },
    { name: "dw", status: "unavailable", projects: [] },
  ] as any;

  it("flipTargetForStory resolves the repo whose live project owns the story", () => {
    expect(flipTargetForStory(repos, "HS-87-05", "holdspeak")).toEqual({
      repo: "code",
      project: "holdspeak",
      story: "HS-87-05",
    });
  });

  it("flipTargetForStory is null when no live belt claims the project", () => {
    expect(flipTargetForStory(repos, "X-1-01", "ghost")).toBeNull();
    expect(flipTargetForStory(repos, "", "holdspeak")).toBeNull();
  });

  const sessA = fromWireMcSession({
    key: "claude:a",
    agent: "claude",
    correlation: "ambiguous",
  });
  const sessOn = fromWireMcSession({
    key: "claude:b",
    agent: "claude",
    correlation: "on_story",
    stories: [{ story_id: "HS-1", project: "holdspeak" }],
  });

  it("manualPinsByStory places a pinned session under its story", () => {
    const map = manualPinsByStory([sessA], { "claude:a": "HS-2" }, {});
    expect(map["HS-2"].map((s) => s.key)).toEqual(["claude:a"]);
  });

  it("never duplicates a session the correlator already placed there", () => {
    const correlated = { "HS-1": [sessOn] };
    const map = manualPinsByStory([sessOn], { "claude:b": "HS-1" }, correlated);
    expect(map["HS-1"]).toBeUndefined();
  });

  it("drops a pin whose session is gone from the registry (re-asserts on return)", () => {
    const map = manualPinsByStory([], { "claude:gone": "HS-2" }, {});
    expect(map).toEqual({});
  });
});
