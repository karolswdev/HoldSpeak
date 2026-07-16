// The Delivery Runtime read model on the Desk (HS-94-08). The load-bearing
// rules under test: the store holds NO authority (status/target/policy/grant
// all come from the server, never a UI field); an open terminal target is
// never reinterpreted (a different node/worktree is a different target);
// freshness renders as itself; and the List view + belt compatibility both
// read the one read model.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  deliveryBeltRepos,
  deliveryListRows,
  fromWireAttempt,
  fromWireNode,
  fromWireSource,
  sourceRecovery,
  useDelivery,
  type DeliverySource,
} from "../delivery";
import {
  sameTarget,
  sendPreview,
  targetKey,
  useDeliveryTerminal,
  type OpenTarget,
} from "../deliveryTerminal";
import { targetHandle, type DiscoveredTarget } from "../deliveryFactory";

const SNAPSHOT = {
  delivery_schema: 1,
  revision: "rev_a1",
  cursor: "cur_a1",
  generated_at: "2026-07-16T00:00:00Z",
  sources: [
    {
      source_id: "src_1",
      node_id: null,
      label: "holdspeak",
      status: "live",
      detail: "",
      observed_at: "2026-07-16T00:00:00Z",
      capabilities: { schemas: { feed_schema: 1 } },
      worktrees: [{ worktree_id: "wt_1", branch: "main" }],
      projects: [
        {
          slug: "holdspeak",
          prefix: "HS",
          current_phase: {
            number: 94,
            title: "Delivery Runtime",
            status: "open",
            stories_done: 7,
            stories_total: 10,
          },
          next_story: { story_id: "HS-94-08", title: "Web Desk", status: "in-progress" },
          phases: [
            { number: 93, title: "Effortless", status: "closed", stories_done: 8, stories_total: 8 },
            { number: 94, title: "Delivery Runtime", status: "open", stories_done: 7, stories_total: 10 },
          ],
          stories: [
            { story_id: "HS-94-08", title: "Web Desk", status: "in-progress", phase: 94, evidence_exists: false },
            { story_id: "HS-94-01", title: "Contract", status: "done", phase: 94, evidence_exists: true },
            { story_id: "HS-93-01", title: "Three starts", status: "done", phase: 93, evidence_exists: true },
          ],
          warnings: 2,
        },
      ],
      sessions: null,
    },
    {
      source_id: "src_2",
      node_id: "node_a",
      label: "delivery-workbench",
      status: "incompatible",
      detail: "feed_schema 3 found, 1 required",
      observed_at: "2026-07-15T23:00:00Z",
      capabilities: null,
      worktrees: [{ worktree_id: "wt_2", branch: "main" }],
      projects: null,
      sessions: null,
    },
  ],
};

const ATTEMPTS = {
  attempts_schema: 1,
  attempts: [
    {
      attempt_id: "att_1",
      story_ref: { source_id: "src_1", project: "holdspeak", story_id: "HS-94-08" },
      node_id: "node_a",
      worktree_id: "wt_1",
      session_id: "sess_1",
      target_id: "term_1",
      association: { kind: "launch", claimed_by: "desk-owner" },
      exact: true,
      state: "working",
      started_at: "2026-07-16T00:00:00Z",
      updated_at: "2026-07-16T00:01:00Z",
      ended_at: null,
    },
    {
      attempt_id: "att_2",
      story_ref: { source_id: "src_1", project: "holdspeak", story_id: "HS-94-01" },
      worktree_id: "wt_1",
      association: { kind: "heuristic" },
      exact: true,
      state: "idle",
      started_at: "x",
      updated_at: "x",
      ended_at: null,
    },
  ],
};

const NODES = {
  nodes_schema: 1,
  nodes: [
    {
      name: "studio-mac",
      node_id: "node_a",
      kind: "node-link",
      status: "live",
      last_seen: "2026-07-16T00:01:00Z",
      capabilities: ["terminal.text"],
      commands_enabled: true,
      compat: "1",
      clock_skew_seconds: 0.2,
    },
  ],
};

function stubRoutes(bodies: Record<string, any>, seen?: any[]) {
  vi.stubGlobal("fetch", (url: string, init?: any) => {
    seen?.push({ url: String(url), init });
    const key = Object.keys(bodies).find((k) => String(url).includes(k));
    const entry = key ? bodies[key] : {};
    const status = entry.__status ?? 200;
    return Promise.resolve({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(entry.__body ?? entry),
    });
  });
}

describe("wire normalizers keep provenance and never invent", () => {
  it("fromWireSource nests projects/stories with source provenance", () => {
    const s = fromWireSource(SNAPSHOT.sources[0]);
    expect(s.status).toBe("live");
    expect(s.worktrees[0]).toMatchObject({ worktreeId: "wt_1", branch: "main", sourceId: "src_1" });
    const project = s.projects[0];
    expect(project.currentPhase).toMatchObject({ number: 94, storiesDone: 7 });
    expect(project.nextStoryId).toBe("HS-94-08");
    // Each story carries the source it came from — provenance, not a guess.
    expect(project.stories[0]).toMatchObject({ sourceId: "src_1", project: "holdspeak" });
  });

  it("an unknown status coerces to unavailable, an off-live source keeps null rows honest", () => {
    const incompatible = fromWireSource(SNAPSHOT.sources[1]);
    expect(incompatible.status).toBe("incompatible");
    expect(incompatible.projects).toEqual([]); // null projects → empty, never invented
    expect(fromWireSource({ status: "wat" }).status).toBe("unavailable");
  });

  it("a heuristic association is always inexact, whatever the wire claims", () => {
    const exact = fromWireAttempt(ATTEMPTS.attempts[0]);
    expect(exact).toMatchObject({ association: "launch", exact: true, targetId: "term_1" });
    const heuristic = fromWireAttempt(ATTEMPTS.attempts[1]);
    expect(heuristic.association).toBe("heuristic");
    expect(heuristic.exact).toBe(false); // ambiguity is visible, never dressed as exact
  });

  it("fromWireNode carries typed liveness", () => {
    const n = fromWireNode(NODES.nodes[0]);
    expect(n).toMatchObject({ nodeId: "node_a", kind: "node-link", commandsEnabled: true });
  });
});

describe("the store holds no authority", () => {
  beforeEach(() => {
    localStorage.clear();
    useDelivery.setState({ sources: [], nodes: [], attempts: [], revision: "", updatedAt: null });
  });
  afterEach(() => vi.unstubAllGlobals());

  it("exposes no setter for status, target, policy, grant, or attempt state", () => {
    const store = useDelivery.getState() as unknown as Record<string, unknown>;
    for (const forbidden of ["setStatus", "setTarget", "setPolicy", "setGrant", "setState", "setAttemptState", "associate"]) {
      expect(typeof store[forbidden]).toBe("undefined");
    }
    // The only mutators are refresh (server-derived) and setFocusSource (a view pref).
    expect(typeof store.refresh).toBe("function");
    expect(typeof store.setFocusSource).toBe("function");
  });

  it("refresh derives every field from the server snapshot, not any argument", async () => {
    const seen: any[] = [];
    stubRoutes(
      { "/api/delivery/snapshot": SNAPSHOT, "/api/delivery/nodes": NODES, "/api/delivery/attempts": ATTEMPTS },
      seen,
    );
    await useDelivery.getState().refresh();
    const st = useDelivery.getState();
    expect(st.sources.map((s) => s.status)).toEqual(["live", "incompatible"]);
    expect(st.attempts[0].targetId).toBe("term_1"); // from the server, verbatim
    expect(st.revision).toBe("rev_a1");
    expect(st.nodes[0].nodeId).toBe("node_a");
  });

  it("setFocusSource only touches the view preference and localStorage", () => {
    useDelivery.getState().setFocusSource("src_1");
    expect(useDelivery.getState().focusSourceId).toBe("src_1");
    expect(localStorage.getItem("hs.delivery.focus")).toBe("src_1");
    // Nothing about association/target/status moved.
    expect(useDelivery.getState().sources).toEqual([]);
  });

  it("polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame", async () => {
    const seen: any[] = [];
    stubRoutes(
      { "/api/delivery/snapshot": SNAPSHOT, "/api/delivery/nodes": NODES, "/api/delivery/attempts": ATTEMPTS },
      seen,
    );
    await useDelivery.getState().refresh();
    // Now the source answers 304 — the store must keep its last coherent frame.
    stubRoutes(
      {
        "/api/delivery/snapshot": { __status: 304, __body: {} },
        "/api/delivery/nodes": NODES,
        "/api/delivery/attempts": ATTEMPTS,
      },
      seen,
    );
    await useDelivery.getState().refresh();
    const snapCall = seen
      .filter((c) => c.url.includes("/api/delivery/snapshot"))
      .at(-1);
    const headers = new Headers(snapCall.init.headers);
    expect(headers.get("If-None-Match")).toBe("rev_a1");
    expect(useDelivery.getState().sources.length).toBe(2); // unchanged frame retained
  });
});

describe("freshness renders as itself with a distinct recovery", () => {
  const base: DeliverySource = fromWireSource(SNAPSHOT.sources[0]);
  it("a live source offers no recovery", () => {
    expect(sourceRecovery(base)).toBeNull();
  });
  it("each off-live state names a distinct recovery, never a blank retry", () => {
    const states = ["stale", "offline", "incompatible", "unauthorized", "unavailable"] as const;
    const labels = states.map((state) => sourceRecovery({ ...base, status: state })!.label);
    expect(new Set(labels).size).toBe(states.length); // all distinct
    expect(sourceRecovery({ ...base, status: "incompatible", detail: "schema 3 vs 1" })!.hint).toContain("schema");
  });
});

describe("the immutable terminal target is never reinterpreted", () => {
  const targetA: OpenTarget = {
    targetId: "term_a",
    targetGeneration: "gen_1",
    nodeId: "node_a",
    label: "HS-94-08",
    sessionLabel: "hs94",
    worktreeId: "wt_1",
    agent: "codex",
  };
  const targetB: OpenTarget = { ...targetA, targetId: "term_b", nodeId: "node_b", label: "HS-94-05" };

  afterEach(() => {
    useDeliveryTerminal.getState().close();
    vi.unstubAllGlobals();
  });

  it("a different node yields a different target key (selecting is not reinterpreting)", () => {
    expect(targetKey(targetA)).not.toBe(targetKey(targetB));
    expect(sameTarget(targetA, targetB)).toBe(false);
    expect(sameTarget(targetA, { ...targetA })).toBe(true);
    // Two discovered panes on different nodes map to different handles.
    const d1: DiscoveredTarget = {
      nodeId: "node_a", session: "s", paneId: "%1", targetId: "t1", targetGeneration: "g1",
      sourceId: null, worktreeId: null, profileId: null, launchId: null, storyRef: null,
      attemptId: null, attemptState: null, sessionBound: false,
    };
    const d2: DiscoveredTarget = { ...d1, nodeId: "node_b", targetId: "t2", targetGeneration: "g2" };
    expect(targetKey(targetHandle(d1))).not.toBe(targetKey(targetHandle(d2)));
  });

  it("has no setter that mutates an open target's id or generation", () => {
    const store = useDeliveryTerminal.getState() as unknown as Record<string, unknown>;
    for (const forbidden of ["setTargetId", "setGeneration", "retarget", "reinterpret", "setNode"]) {
      expect(typeof store[forbidden]).toBe("undefined");
    }
    // open() replaces wholesale — the ONLY way the open target changes.
    useDeliveryTerminal.setState({ openTarget: targetA });
    useDeliveryTerminal.setState({ openTarget: targetB });
    expect(useDeliveryTerminal.getState().openTarget).toEqual(targetB);
  });

  it("a command names the OPEN target's ids and supplies no authority block", async () => {
    const posts: any[] = [];
    stubRoutes(
      {
        "/api/delivery/terminal/commands": {
          command_id: "cid-1",
          state: "complete",
          receipt: { receipt_id: "receipt_9", state: "succeeded", target_id: "term_a" },
        },
      },
      posts,
    );
    useDeliveryTerminal.setState({ openTarget: targetA, status: "live" });
    const ok = await useDeliveryTerminal.getState().sendText("continue", true);
    expect(ok).toBe(true);
    const body = JSON.parse(posts[0].init.body);
    expect(body.target).toEqual({ node_id: "node_a", target_id: "term_a", target_generation: "gen_1" });
    expect(body.operation).toEqual({ family: "coder_steering", verb: "terminal.text" });
    expect(body.payload).toEqual({ text: "continue", submit: true });
    // The client NEVER supplies authority/actor/policy/grant — the hub derives them.
    expect(body.authority).toBeUndefined();
    expect(body.actor).toBeUndefined();
    expect(useDeliveryTerminal.getState().sendDetail).toContain("receipt_9");
  });

  it("a refused receipt renders in place, not as a delivered send", async () => {
    stubRoutes({
      "/api/delivery/terminal/commands": {
        command_id: "cid-2",
        state: "complete",
        receipt: { state: "refused", outcome: "generation_mismatch", error: "pane recycled" },
      },
    });
    useDeliveryTerminal.setState({ openTarget: targetA, status: "live", sendState: "idle" });
    const ok = await useDeliveryTerminal.getState().sendText("late", true);
    expect(ok).toBe(false);
    expect(useDeliveryTerminal.getState().sendState).toBe("refused");
    expect(useDeliveryTerminal.getState().sendDetail).toContain("generation_mismatch");
  });

  it("the send preview names the exact destination and consequence", () => {
    expect(sendPreview(targetA, "terminal.text", true)).toEqual({
      destination: "HS-94-08 · node_a",
      consequence: "types text and submits",
    });
    expect(sendPreview(targetA, "terminal.keys", false)!.consequence).toBe("sends keys to the pane");
    expect(sendPreview(null, "terminal.text", true)).toBeNull();
  });
});

describe("delivery objects reach the List view", () => {
  it("deliveryListRows includes current-phase Stories and active attempts, bounded", () => {
    const sources = SNAPSHOT.sources.map(fromWireSource);
    const attempts = ATTEMPTS.attempts.map(fromWireAttempt);
    const rows = deliveryListRows(sources, attempts);
    const stories = rows.filter((r) => r.kind === "Story").map((r) => r.label);
    // Only the current phase (94) stories — never a dump of the phase-93 story.
    expect(stories).toContain("HS-94-08");
    expect(stories).not.toContain("HS-93-01");
    // The active (working) attempt rides in as a Coder session row; the idle one does not.
    const sessions = rows.filter((r) => r.kind === "Coder session").map((r) => r.label);
    expect(sessions).toEqual(["HS-94-08"]);
    // A story row carries its source freshness, resolved from the read model.
    expect(rows.find((r) => r.label === "HS-94-08" && r.kind === "Story")!.freshness).toBe("live");
  });
});

describe("belt compatibility reads the one read model", () => {
  it("maps sources to the belt repo shape, freshness folded honestly", () => {
    const repos = deliveryBeltRepos(SNAPSHOT.sources.map(fromWireSource));
    expect(repos[0]).toMatchObject({ name: "holdspeak", status: "live" });
    expect(repos[0].projects[0]).toMatchObject({ slug: "holdspeak", nextStoryId: "HS-94-08" });
    expect(repos[0].projects[0].phases.map((p) => p.status)).toEqual(["closed", "open"]);
    // An incompatible source becomes the belt's "compatibility" with no invented projects.
    expect(repos[1]).toMatchObject({ name: "delivery-workbench", status: "compatibility" });
    expect(repos[1].projects).toEqual([]);
  });
});
