// The steering slice (HS-87-01) — attach. The load-bearing rule under
// test: the peek poll runs ONLY while the pull-out is open. The recorder
// counts /peek hits; after closeSession the count must freeze.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  PEEK_POLL_MS,
  fromWireSteeringSession,
  isCoderFrame,
  useSteering,
} from "../steering";

const LIVE_BODY = {
  key: "claude:abc123",
  agent: "claude",
  stale: false,
  awaiting_response: true,
  question: "ship it?",
  updated_at: "2026-07-08T00:00:00Z",
  peek: { status: "live", hash: "h1", lines: ["$ make", "ok"] },
};

function stubPeek(recorder: string[], body: any = LIVE_BODY, status = 200) {
  vi.stubGlobal("fetch", (url: string) => {
    recorder.push(String(url));
    return Promise.resolve({
      ok: status < 400,
      status,
      json: () => Promise.resolve(body),
    });
  });
}

describe("the steering slice (attach)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    useSteering.getState().closeSession();
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("normalizes the wire envelope", () => {
    const s = fromWireSteeringSession(LIVE_BODY);
    expect(s).toEqual({
      key: "claude:abc123",
      agent: "claude",
      stale: false,
      awaitingResponse: true,
      question: "ship it?",
      updatedAt: "2026-07-08T00:00:00Z",
    });
  });

  it("openSession polls immediately and then on the tick", async () => {
    const hits: string[] = [];
    stubPeek(hits);
    useSteering.getState().openSession("claude:abc123");
    await vi.advanceTimersByTimeAsync(0);
    expect(hits.length).toBe(1);
    expect(hits[0]).toContain("/api/coders/claude%3Aabc123/peek");
    await vi.advanceTimersByTimeAsync(PEEK_POLL_MS);
    expect(hits.length).toBe(2);
    const st = useSteering.getState();
    expect(st.paneStatus).toBe("live");
    expect(st.paneLines).toEqual(["$ make", "ok"]);
  });

  it("closing the pull-out stops the poll — zero hits after close", async () => {
    const hits: string[] = [];
    stubPeek(hits);
    useSteering.getState().openSession("claude:abc123");
    await vi.advanceTimersByTimeAsync(PEEK_POLL_MS * 2);
    const before = hits.length;
    expect(before).toBeGreaterThan(0);
    useSteering.getState().closeSession();
    await vi.advanceTimersByTimeAsync(PEEK_POLL_MS * 5);
    expect(hits.length).toBe(before);
    expect(useSteering.getState().openKey).toBeNull();
  });

  it("carries the hash gate and keeps the view on not_modified", async () => {
    const hits: string[] = [];
    stubPeek(hits);
    useSteering.getState().openSession("claude:abc123");
    await vi.advanceTimersByTimeAsync(0);
    stubPeek(hits, { ...LIVE_BODY, peek: { status: "not_modified", hash: "h1" } });
    await vi.advanceTimersByTimeAsync(PEEK_POLL_MS);
    expect(hits[1]).toContain("last_hash=h1");
    const st = useSteering.getState();
    expect(st.paneStatus).toBe("live");
    expect(st.paneLines).toEqual(["$ make", "ok"]); // the gate held; nothing dropped
  });

  it("typed absences render as themselves, never an empty black box", async () => {
    const hits: string[] = [];
    stubPeek(hits, {
      ...LIVE_BODY,
      peek: { status: "pane_gone", detail: "can't find pane %3" },
    });
    useSteering.getState().openSession("claude:abc123");
    await vi.advanceTimersByTimeAsync(0);
    const st = useSteering.getState();
    expect(st.paneStatus).toBe("pane_gone");
    expect(st.paneDetail).toBe("can't find pane %3");
  });

  it("a 404 is the registry speaking: unknown_session", async () => {
    const hits: string[] = [];
    stubPeek(hits, { status: "unknown_session", key: "claude:abc123" }, 404);
    useSteering.getState().openSession("claude:abc123");
    await vi.advanceTimersByTimeAsync(0);
    expect(useSteering.getState().paneStatus).toBe("unknown_session");
  });
});

describe("coder frames on the one bus", () => {
  it("matches only scope:coder intel_status frames", () => {
    expect(
      isCoderFrame({ type: "intel_status", data: { scope: "coder" } }),
    ).toBe(true);
    expect(
      isCoderFrame({ type: "intel_status", data: { scope: "belt" } }),
    ).toBe(false);
    expect(isCoderFrame({ type: "duration", data: { scope: "coder" } })).toBe(false);
    expect(isCoderFrame(null)).toBe(false);
  });
});
