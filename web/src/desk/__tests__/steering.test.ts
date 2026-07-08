// The steering slice (HS-87-01) — attach. The load-bearing rule under
// test: the peek poll runs ONLY while the pull-out is open. The recorder
// counts /peek hits; after closeSession the count must freeze.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  PEEK_POLL_MS,
  fromWireSteeringSession,
  isCoderFrame,
  mmss,
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

describe("the arming grant (HS-87-02)", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    useSteering.getState().closeSession();
    useSteering.setState({ armedKeys: {} });
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("mmss renders the honest remainder", () => {
    expect(mmss(900)).toBe("15:00");
    expect(mmss(61)).toBe("1:01");
    expect(mmss(0)).toBe("0:00");
    expect(mmss(-5)).toBe("0:00");
  });

  it("arm success sets the countdown anchor and the pin map", async () => {
    vi.stubGlobal("fetch", (url: string, opts?: any) => {
      const body =
        String(url).includes("/arm") && opts?.method === "POST"
          ? { status: "armed", key: "claude:abc123", pane_id: "%5", expires_in_seconds: 900 }
          : LIVE_BODY;
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });
    });
    useSteering.setState({ openKey: "claude:abc123" });
    await useSteering.getState().arm();
    const st = useSteering.getState();
    expect(st.armed).toBe(true);
    expect(st.armedUntil).not.toBeNull();
    expect(st.armedKeys["claude:abc123"]).toBeGreaterThan(Date.now());
  });

  it("a typed refusal renders in place, not as a grant", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve({
        ok: false,
        status: 409,
        json: () =>
          Promise.resolve({
            status: "stale_session",
            detail: "registry record is 2700s old — a stale session cannot be armed",
          }),
      }),
    );
    useSteering.setState({ openKey: "claude:abc123" });
    await useSteering.getState().arm();
    const st = useSteering.getState();
    expect(st.armed).toBe(false);
    expect(st.armError).toContain("stale session cannot be armed");
  });

  it("disarm clears the grant immediately", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) }),
    );
    useSteering.setState({
      openKey: "claude:abc123",
      armed: true,
      armedUntil: Date.now() + 60_000,
      armedKeys: { "claude:abc123": Date.now() + 60_000 },
    });
    await useSteering.getState().disarm();
    const st = useSteering.getState();
    expect(st.armed).toBe(false);
    expect(st.armedKeys["claude:abc123"]).toBeUndefined();
  });

  it("the peek envelope re-syncs the grant — expiry flips the desk without a reload", async () => {
    const hits: string[] = [];
    stubPeek(hits, {
      ...LIVE_BODY,
      grant: { armed: true, expires_in_seconds: 300 },
    });
    useSteering.getState().openSession("claude:abc123");
    await vi.advanceTimersByTimeAsync(0);
    expect(useSteering.getState().armed).toBe(true);
    stubPeek(hits, {
      ...LIVE_BODY,
      grant: { armed: false, expires_in_seconds: null },
      peek: { status: "not_modified", hash: "h1" },
    });
    await vi.advanceTimersByTimeAsync(PEEK_POLL_MS);
    expect(useSteering.getState().armed).toBe(false);
  });

  it("refreshGrants maps the wire onto the pins", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            grants: { "claude:abc123": { pane_id: "%5", expires_in_seconds: 120 } },
          }),
      }),
    );
    await useSteering.getState().refreshGrants();
    expect(useSteering.getState().armedKeys["claude:abc123"]).toBeGreaterThan(
      Date.now(),
    );
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
