// PHILO-10-02 round two (Codex Astra r1 finding 1): an UNKNOWN nudge is never offered for Send
// again -- not after closing and reopening its card, not after a Room reload that reads the
// persisted step state. Adapted from Codex's counsel probe (red on 71a79772). The wire is the
// real hub's answers, recorded by that probe (nudge.send timed out: outcome unknown).
// Selector edits for the 169 rebuild:
//   - orientation band → room head (headline, chips, Draft update)
//   - focus block → NEEDS YOU section
//   - right rail, MetricStrip, SurfaceColumns → removed (the Room is a single column)
//   - four wings (timeline/decisions/search/ask) → two wings (room/history)
//   - REV chip → removed (D1 cut)
//   - DegradedNotice inline → sections degrade individually via the wire
//   - counters (Meetings 0 · Resources 0 · …) → removed (D1 cut)
//   - identity dedup → the name is said once (title bar); no orientation band

import { act, render, screen, waitFor, fireEvent, cleanup } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
import { TitleSlotContext } from "../../../desk/surface/title";
import { WingSlotContext } from "../../../desk/surface/wings";
import { useDesk } from "../../../desk/store";
import { ProjectRoomCore } from "../ProjectRoomCore";

vi.mock("../../../desk/ask", async () => {
  const actual =
    await vi.importActual<typeof import("../../../desk/ask")>(
      "../../../desk/ask",
    );
  return { ...actual, runAsk: vi.fn() };
});

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual =
    await vi.importActual<typeof import("../../../lib/api")>(
      "../../../lib/api",
    );
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

vi.mock("../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/shell")>(
    "../../../desk/shell",
  );
  return { ...actual, openPrimitive: vi.fn(), openSurfaceOr: vi.fn() };
});

function WindowHarness({ scope, onTitle }: { scope?: string; onTitle?: (t: string | null) => void }) {
  const [wings, setWings] = useState<ReactNode>(null);
  const setTitle = onTitle ?? (() => {});
  return (
    <TitleSlotContext.Provider value={setTitle}>
      <WingSlotContext.Provider value={setWings}>
        <div data-testid="wing-slot">{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

/** Build a well-formed /room response with the 169 sections. */
function roomResponse(overrides: Record<string, unknown> = {}) {
  return {
    project_id: "p1",
    revision: 3,
    observed_at: "2026-08-31T10:00:00",
    project: {
      id: "p1",
      name: "Alpha Project",
      description: "Testing the room",
      is_archived: false,
      meeting_count: 2,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-08-31T10:00:00",
      purpose: "Ship the widget",
      outcome_text: "Widget shipped",
      owner_ref: "person:owner1",
      lifecycle: "active",
      posture: "green",
      posture_reason: "On track",
      start_at: "2026-08-01",
      target_at: "2026-12-01",
      revision: 3,
      ...(overrides.project as Record<string, unknown> || {}),
    },
    items: overrides.items ?? { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: overrides.meetings ?? { state: "ok", count: 2, latest: { id: "m1", title: "Review" } },
    resources: overrides.resources ?? { state: "ok", count: 1, latest: null },
    changes: overrides.changes ?? { state: "ok", recent: [] },
    review: overrides.review ?? { state: "absent", reason: "not_yet_built" },
    needsYou: overrides.needsYou ?? { state: "ok", items: [], count: 0 },
    sources: overrides.sources ?? { state: "ok", items: [], count: 0 },
    health: overrides.health ?? {
      state: "ok",
      assessment: "on_track",
      reason: null,
      inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false },
    },
    sinceRead: overrides.sinceRead ?? { state: "ok", readAt: null, groups: [] },
    decisions: overrides.decisions ?? { state: "ok", items: [] },
    commitments: overrides.commitments ?? { state: "ok", items: [] },
    target: overrides.target ?? { state: "absent", reason: "none" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

function detailResponse(url: string) {
  if (url.includes("/meetings"))
    return { meetings: [{ id: "m1", title: "Review", started_at: "2026-07-29T10:00:00Z" }] };
  if (url.startsWith("/api/decisions"))
    return { decisions: [{ id: "d1", text: "Keep grammar", lifecycle: "recorded" }] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting"))
    return { current_meeting: { id: "m1" }, since_last_meeting: {
      previous_meeting: { id: "m0", title: "Kickoff" },
      new_decisions: [], new_actions: [], closed_actions: [],
    }};
  if (url.includes("/room/read"))
    return { read_at: new Date().toISOString() };
  return {};
}

function response(url: string) {
  if (url.includes("/room/read")) return { read_at: new Date().toISOString() };
  if (url.includes("/room")) return roomResponse();
  return detailResponse(url);
}

beforeEach(() => {
  apiFetch.mockImplementation((url: string) => Promise.resolve(response(url)));
  useDesk.setState({
    windowsById: {},
    items: { ...EMPTY_ITEMS },
    projects: [],
    inferenceTargets: [],
  });
});

afterEach(() => {
  vi.clearAllMocks();
});


const STEP = "pststep_2cdd9203b1ad4d229c8a13e2974cab37";
const wire = {
  initial: { step_id: STEP, state: "proposed", effect_kind: "github_comment", repo: "example/payments", pr_number: 7,
    pr_title: "", pr_url: "", reviewer_login: "reviewer", days: 0, comment_text: "", host: "github.com", receipt: {},
    created_at: "2026-09-29T01:52:28+00:00", completed_at: null },
  settled: { step_id: STEP, state: "unknown" },
  send: { success: false, outcome: "unknown", comment_receipt: { effect_kind: "github_comment", pr_number: 7,
    reviewer_login: "reviewer", outcome: "unknown", reason: "timeout" }, operation_id: "op_a14ec3b2ab9848e78d4950d7f2fb2349",
    receipt: { state: "indeterminate", outcome: "timeout" } },
};

function installNudgeWire(persisted = false) {
  apiFetch.mockImplementation((url: string) => {
    if (url.includes('/nudges/') && url.endsWith('/send')) return Promise.resolve(wire.send);
    if (url.includes('/nudges')) return Promise.resolve({nudges: persisted ? [] : [wire.initial]});
    if (url.includes('/room/read')) return Promise.resolve({read_at: new Date().toISOString()});
    if (url.includes('/room')) return Promise.resolve(roomResponse({
      needsYou: {state: 'ok',count: 1,items:[{source:'github',kind:'review_bottleneck',title:'Reviewer',relationship_id:'rel-1',median_days:4,pr_count:1}]},
      health: {state:'ok',assessment:'at_risk',signals:{},people:[{relationship_id:'rel-1',display_name:'Reviewer',login:'reviewer',median_days:4,count:1,prs:[{number:7,title:'Cutover',url:'https://github.com/example/payments/pull/7'}],nudge:{step_id:wire.settled.step_id,state:persisted ? wire.settled.state : 'proposed'}}]}
    }));
    return Promise.resolve(detailResponse(url));
  });
}
afterEach(() => cleanup());
it('UNKNOWN survives closing and reopening the card', async () => {
  installNudgeWire();render(<WindowHarness scope="project:p1" />);
  fireEvent.click(await screen.findByTestId('nudge-verb'));
  fireEvent.click(await screen.findByTestId('nudge-send'));
  await screen.findByTestId('nudge-unknown-row');
  fireEvent.click(screen.getByTestId('nudge-verb'));
  fireEvent.click(screen.getByTestId('nudge-verb'));
  expect(screen.queryByTestId('nudge-send')).toBeNull();
  expect(screen.queryByTestId('nudge-unknown-row')).not.toBeNull();
});
it('UNKNOWN survives a Room reload using its persisted wire state', async () => {
  installNudgeWire(true);render(<WindowHarness scope="project:p1" />);
  fireEvent.click(await screen.findByTestId('nudge-verb'));
  expect(screen.queryByTestId('nudge-send')).toBeNull();
  expect(screen.queryByTestId('nudge-unknown-row')).not.toBeNull();
});

// Round three (Codex Astra r2 finding 2, its probe): Send -> close and reopen while the answer is still
// in flight -> UNKNOWN arrives. The late answer must reach the CURRENT card.
it('UNKNOWN survives a close and reopen while Send is still in flight', async () => {
  installNudgeWire();
  const previous = apiFetch.getMockImplementation()!;
  let settle!: (value: unknown) => void;
  const pending = new Promise((resolve) => { settle = resolve; });
  apiFetch.mockImplementation((url: string) => url.includes('/nudges/') && url.endsWith('/send') ? pending : previous(url));
  render(<WindowHarness scope="project:p1" />);
  fireEvent.click(await screen.findByTestId('nudge-verb'));
  fireEvent.click(await screen.findByTestId('nudge-send'));
  fireEvent.click(screen.getByTestId('nudge-verb'));
  fireEvent.click(screen.getByTestId('nudge-verb'));
  // While in flight the reopened card is busy: pressing Send again posts nothing.
  fireEvent.click(screen.getByTestId('nudge-send'));
  expect(apiFetch.mock.calls.filter(([url]) => String(url).endsWith('/send')).length).toBe(1);
  await act(async () => { settle(wire.send); await pending; });
  expect(screen.queryByTestId('nudge-send')).toBeNull();
  expect(screen.queryByTestId('nudge-unknown-row')).not.toBeNull();
});
