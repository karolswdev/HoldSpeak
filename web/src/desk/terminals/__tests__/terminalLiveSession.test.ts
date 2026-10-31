import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { armTerminal, disarmTerminal, readTerminalLive, resizeTerminal, sendTerminalCommand } from "../api";
import { createTerminalSession } from "../terminalSession";
import type { TerminalDescriptor, TerminalOutputFrame } from "../types";

vi.mock("../api", () => ({
  armTerminal: vi.fn(),
  disarmTerminal: vi.fn(),
  readTerminalLive: vi.fn(),
  readTerminalSubscription: vi.fn(),
  resizeTerminal: vi.fn(),
  sendTerminalCommand: vi.fn(),
}));

const descriptor = (): TerminalDescriptor => ({
  id: "live",
  label: "live",
  session: "session-live",
  key: "pane:live",
  agent: "pane",
  command: "zsh",
  current_path: "/isolated",
  state: "live",
  target: { node_id: "local", target_id: "target-live", target_generation: "generation-1" },
  pane_id: "%live",
  context: { status: "unbound", project: null, source: null, worktree: null, launch: null, program: null, mcp: null },
});

const b64 = (value: Uint8Array | string) => {
  const bytes = typeof value === "string" ? new TextEncoder().encode(value) : value;
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary);
};

const liveResponse = (frames: Array<Record<string, unknown>>) => {
  const bytes = new TextEncoder().encode(frames.map((frame) => `${JSON.stringify(frame)}\n`).join(""));
  const body = new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(bytes); controller.close(); } });
  return new Response(body, { status: 200, headers: { "Content-Type": "application/x-ndjson" } });
};

const flush = async () => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};

describe("continuous native terminal session", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(armTerminal).mockResolvedValue({ ok: true });
    vi.mocked(disarmTerminal).mockResolvedValue({ ok: true, status: "disarmed" });
    vi.mocked(resizeTerminal).mockResolvedValue({ ok: true, receipt: null, dimensions: { cols: 80, rows: 24 } });
    vi.mocked(sendTerminalCommand).mockResolvedValue({ ok: true, receipt: null });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("delivers ordered bytes, including UTF-8 split across frames, without replaying duplicates", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    const seen: TerminalOutputFrame[] = [];
    session.getState().output?.subscribe((frame) => seen.push(frame));
    vi.mocked(readTerminalLive).mockResolvedValueOnce(liveResponse([
      { status: "snapshot", stream_id: "stream-1", sequence: 4, data: b64("$ "), encoding: "base64" },
      { status: "output", stream_id: "stream-1", sequence: 5, data: b64("caf"), encoding: "base64" },
      { status: "output", stream_id: "stream-1", sequence: 5, data: b64("duplicate"), encoding: "base64" },
      { status: "output", stream_id: "stream-1", sequence: 6, data: b64(new Uint8Array([0xc3])), encoding: "base64" },
      { status: "output", stream_id: "stream-1", sequence: 7, data: b64(new Uint8Array([0xa9, 0x20])), encoding: "base64" },
    ]));

    session.getState().start();
    await flush();

    expect(seen.map((frame) => frame.sequence)).toEqual([4, 5, 6, 7]);
    expect(seen.map((frame) => frame.kind)).toEqual(["snapshot", "output", "output", "output"]);
    expect([...seen[1].data]).toEqual([...new TextEncoder().encode("caf")]);
    expect([...seen[2].data]).toEqual([0xc3]);
    expect([...seen[3].data]).toEqual([0xa9, 0x20]);
    expect(session.getState().sequence).toBe(7);
    session.getState().stop();
  });

  it("resumes with a fresh stream epoch and requests the latest sequence", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    vi.mocked(readTerminalLive)
      .mockResolvedValueOnce(liveResponse([{ status: "snapshot", stream_id: "stream-1", sequence: 9, data: b64("old"), encoding: "base64" }]))
      .mockResolvedValueOnce(liveResponse([{ status: "snapshot", stream_id: "stream-2", sequence: 1, data: b64("new"), encoding: "base64" }]));
    session.getState().start();
    await flush();
    vi.advanceTimersByTime(250);
    await flush();

    expect(readTerminalLive).toHaveBeenCalledTimes(2);
    expect(vi.mocked(readTerminalLive).mock.calls[1][1]).toBe("stream-1");
    expect(vi.mocked(readTerminalLive).mock.calls[1][2]).toBe(9);
    expect(session.getState().sequence).toBe(1);
    expect(session.getState().raw).toBe("new");
    session.getState().stop();
  });

  it("holds an empty resync marker until the following snapshot and permits snapshot sequence jumps", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    const seen: TerminalOutputFrame[] = [];
    session.getState().output?.subscribe((frame) => seen.push(frame));
    vi.mocked(readTerminalLive).mockResolvedValueOnce(liveResponse([
      { status: "snapshot", stream_id: "stream-1", sequence: 9, data: b64("old"), encoding: "base64" },
      { status: "resync_required", stream_id: "stream-1", sequence: 10 },
      { status: "snapshot", stream_id: "stream-1", sequence: 10, data: b64("fresh"), encoding: "base64" },
    ]));
    session.getState().start();
    await flush();
    expect(seen.map((frame) => frame.kind)).toEqual(["snapshot", "snapshot"]);
    expect(session.getState().raw).toBe("fresh");
    expect(session.getState().sequence).toBe(10);
    session.getState().stop();
  });

  it("honors same-sequence target absence and rejects input already queued", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    vi.mocked(readTerminalLive).mockImplementationOnce(() => new Promise((resolve) => {
      setTimeout(() => resolve(liveResponse([
        { status: "snapshot", stream_id: "stream-1", sequence: 7, data: b64("old"), encoding: "base64" },
        { status: "generation_mismatch", stream_id: "stream-1", sequence: 7, detail: "target replaced" },
      ])), 10);
    }));
    session.getState().start();
    expect(await session.getState().enableTyping()).toBe(true);
    const pending = session.getState().sendText("must not land", true);
    vi.advanceTimersByTime(10);
    await flush();
    expect(await pending).toBe(false);
    expect(session.getState().status).toBe("generation_mismatch");
    expect(session.getState().canType).toBe(false);
    expect(session.getState().raw).toBeNull();
    expect(sendTerminalCommand).not.toHaveBeenCalled();
    session.getState().stop();
  });

  it("classifies an HTTP 409 without status and fences queued input", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    vi.mocked(readTerminalLive).mockImplementationOnce(() => new Promise((resolve) => {
      setTimeout(() => resolve(new Response(JSON.stringify({ error: "target generation changed" }), {
        status: 409,
        headers: { "Content-Type": "application/json" },
      })), 10);
    }));
    session.getState().start();
    expect(await session.getState().enableTyping()).toBe(true);
    const pending = session.getState().sendText("must not land", true);
    vi.advanceTimersByTime(10);
    await flush();
    expect(await pending).toBe(false);
    expect(session.getState().status).toBe("generation_mismatch");
    expect(session.getState().canType).toBe(false);
    expect(session.getState().raw).toBeNull();
    expect(sendTerminalCommand).not.toHaveBeenCalled();
    session.getState().stop();
  });

  it("coalesces geometry and never lets an older resize receipt overwrite the newer desired size", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    vi.mocked(readTerminalLive).mockResolvedValueOnce(liveResponse([{ status: "snapshot", stream_id: "stream-1", sequence: 1, data: b64("$ "), encoding: "base64" }]));
    let resolveFirst!: (value: Awaited<ReturnType<typeof resizeTerminal>>) => void;
    vi.mocked(resizeTerminal).mockReturnValueOnce(new Promise((resolve) => { resolveFirst = resolve; }));
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);
    session.getState().setActivity({ focused: true, visible: true });

    session.getState().setHostGeometry({ cols: 80, rows: 24 });
    session.getState().setHostGeometry({ cols: 100, rows: 30 });
    await flush();
    expect(resizeTerminal).toHaveBeenCalledTimes(1);
    expect(session.getState().resize.desired).toEqual({ cols: 100, rows: 30 });

    resolveFirst({ ok: true, receipt: null, dimensions: { cols: 80, rows: 24 } });
    await flush();
    expect(resizeTerminal).toHaveBeenCalledTimes(2);
    expect(vi.mocked(resizeTerminal).mock.calls[1][1]).toEqual({ cols: 100, rows: 30 });
    session.getState().stop();
  });

  it("marks an overrun replay as needing a fresh snapshot instead of stitching a truncated tail", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    const frames: Array<Record<string, unknown>> = [
      { status: "snapshot", stream_id: "stream-1", sequence: 1, data: b64("$ "), encoding: "base64" },
    ];
    for (let sequence = 2; sequence <= 520; sequence += 1) {
      frames.push({ status: "output", stream_id: "stream-1", sequence, data: b64("x"), encoding: "base64" });
    }
    vi.mocked(readTerminalLive)
      .mockResolvedValueOnce(liveResponse(frames))
      .mockResolvedValueOnce(liveResponse([
        { status: "snapshot", stream_id: "stream-2", sequence: 1, data: b64("fresh"), encoding: "base64" },
      ]));
    session.getState().start();
    await flush();
    expect(session.getState().output?.replay?.(1)).toBeNull();
    session.getState().output?.requestResync?.();
    expect(session.getState().status).toBe("resyncing");
    vi.advanceTimersByTime(250);
    await flush();
    expect(readTerminalLive).toHaveBeenCalledTimes(2);
    expect(vi.mocked(readTerminalLive).mock.calls[1][1]).toBeNull();
    expect(vi.mocked(readTerminalLive).mock.calls[1][2]).toBe(0);
    expect(session.getState().status).toBe("live");
    expect(session.getState().raw).toBe("fresh");
    session.getState().stop();
  });

  it("turns malformed bytes into an explicit resync instead of an empty output frame", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    const seen: TerminalOutputFrame[] = [];
    session.getState().output?.subscribe((frame) => seen.push(frame));
    vi.mocked(readTerminalLive).mockResolvedValueOnce(liveResponse([
      { status: "snapshot", stream_id: "stream-1", sequence: 1, data: b64("boot"), encoding: "base64" },
      { status: "output", stream_id: "stream-1", sequence: 2, data: "not-base64!", encoding: "base64" },
    ]));
    session.getState().start();
    await flush();
    expect(seen.map((frame) => frame.sequence)).toEqual([1]);
    expect(session.getState().status).toBe("resyncing");
    expect(session.getState().error).toBe("Invalid terminal stream bytes");
    session.getState().stop();
  });

  it("keeps a resize refusal separate and stops geometry changes after grant expiry", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    vi.mocked(readTerminalLive).mockResolvedValueOnce(liveResponse([{ status: "snapshot", stream_id: "stream-1", sequence: 1, data: b64("$ "), encoding: "base64" }]));
    vi.mocked(armTerminal).mockResolvedValueOnce({ ok: true, expiresInSeconds: 1 });
    vi.mocked(resizeTerminal).mockResolvedValueOnce({ ok: false, error: "Resize refused", revoke: false });
    vi.mocked(resizeTerminal).mockResolvedValueOnce({ ok: true, receipt: null, dimensions: { cols: 90, rows: 25 } });
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);
    session.getState().setActivity({ focused: true, visible: true });
    session.getState().setHostGeometry({ cols: 90, rows: 25 });
    await flush();
    expect(session.getState().resize.error).toBe("Resize refused");
    expect(session.getState().error).toBeNull();
    expect(await session.getState().retryResize()).toBe(true);
    expect(session.getState().receipt).toBeNull();
    vi.advanceTimersByTime(1_000);
    await flush();
    expect(session.getState().canType).toBe(false);
    session.getState().setHostGeometry({ cols: 100, rows: 30 });
    expect(resizeTerminal).toHaveBeenCalledTimes(2);
    session.getState().stop();
  });

  it("keeps refused host geometry rendered until a verified resize ACK", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    vi.mocked(readTerminalLive).mockResolvedValueOnce(liveResponse([{
      status: "snapshot",
      stream_id: "stream-1",
      sequence: 1,
      data: b64("$ "),
      encoding: "base64",
      pane: { width: 100, height: 30, cursor_x: 0, cursor_y: 0 },
    }]));
    vi.mocked(resizeTerminal)
      .mockResolvedValueOnce({ ok: false, error: "Resize refused", revoke: false })
      .mockResolvedValueOnce({ ok: true, receipt: null, dimensions: { cols: 52, rows: 29 } });
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);
    session.getState().setActivity({ focused: true, visible: true });
    session.getState().setHostGeometry({ cols: 52, rows: 29 });
    await flush();
    expect(session.getState().resize.desired).toEqual({ cols: 52, rows: 29 });
    expect(session.getState().pane).toMatchObject({ width: 100, height: 30 });
    expect(session.getState().resize.error).toBe("Resize refused");
    expect(await session.getState().retryResize()).toBe(true);
    expect(session.getState().pane).toMatchObject({ width: 52, height: 29 });
    session.getState().stop();
  });

  it("reports host geometry only while the granted view owns focus and visibility", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    vi.mocked(readTerminalLive).mockResolvedValueOnce(liveResponse([{ status: "snapshot", stream_id: "stream-1", sequence: 1, data: b64("$ "), encoding: "base64" }]));
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);
    session.getState().setHostGeometry({ cols: 80, rows: 24 });
    expect(resizeTerminal).not.toHaveBeenCalled();
    session.getState().setActivity({ focused: true, visible: true });
    session.getState().setHostGeometry({ cols: 80, rows: 24 });
    await flush();
    expect(resizeTerminal).toHaveBeenCalledTimes(1);
    session.getState().setActivity({ focused: false, visible: false });
    session.getState().setHostGeometry({ cols: 100, rows: 30 });
    expect(resizeTerminal).toHaveBeenCalledTimes(1);
    session.getState().stop();
  });

  it("bounds a stream that never returns headers and leaves a named reconnectable failure", async () => {
    const session = createTerminalSession(descriptor(), { mode: "live" });
    vi.mocked(readTerminalLive).mockReturnValueOnce(new Promise<Response>(() => undefined));
    session.getState().start();
    vi.advanceTimersByTime(10_000);
    await flush();
    expect(session.getState().status).toBe("stream_unavailable");
    expect(session.getState().error).toBe("Terminal stream header timeout");
    session.getState().stop();
  });
});
