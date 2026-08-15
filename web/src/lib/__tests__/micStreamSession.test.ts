// HS-132-04 — the streaming socket declares WHAT KIND of utterance it carries.
//
// A speak-to-fill (every desk field mic) is the user typing with their voice:
// the socket opens with {"type":"start","pipeline":false} and the server's
// final pass is verbatim — no intent routing, no enrichment, no rewriting, no
// journal row. The Speak room's TALK key is the dictate-for-delivery surface;
// it asks for the pipeline, and that is the utterance's ONE pass.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../auth", () => ({
  websocketUrl: (path: string) => `ws://desk.test${path}`,
  websocketProtocols: () => ["holdspeak"],
}));

vi.mock("../micSession", () => ({
  beginHold: vi.fn().mockResolvedValue(undefined),
  endHold: vi.fn().mockReturnValue(null),
  abortHold: vi.fn(),
  micCaptureSupported: vi.fn().mockReturnValue(true),
  subscribeCaptureLevel: vi.fn().mockReturnValue(() => {}),
}));

vi.mock("../speakToFill", () => ({
  toWav16kMono: vi.fn().mockReturnValue(new ArrayBuffer(44)),
}));

import { startStreamSession } from "../micStreamSession";

type Listener = (event: unknown) => void;

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  sent: unknown[] = [];
  private listeners: Record<string, Listener[]> = {};

  constructor(
    public url: string,
    public protocols?: string | string[],
  ) {
    FakeWebSocket.instances.push(this);
  }

  addEventListener(type: string, fn: Listener) {
    (this.listeners[type] ??= []).push(fn);
  }

  send(data: unknown) {
    this.sent.push(data);
  }

  close() {
    this.emit("close", {});
  }

  emit(type: string, event: unknown) {
    (this.listeners[type] ?? []).forEach((fn) => fn(event));
  }

  /** What the client said in JSON text frames, parsed. */
  frames(): Record<string, unknown>[] {
    return this.sent
      .filter((item): item is string => typeof item === "string")
      .map((item) => JSON.parse(item) as Record<string, unknown>);
  }
}

beforeEach(() => {
  FakeWebSocket.instances = [];
  vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function openSocket(options?: { pipeline?: boolean }) {
  const session = await startStreamSession(() => undefined, options);
  const ws = FakeWebSocket.instances[0];
  ws.emit("open", {});
  return { session, ws };
}

describe("startStreamSession declares its pipeline mode (HS-132-04)", () => {
  it("asks for NO pipeline by default (a speak-to-fill)", async () => {
    const { ws } = await openSocket();

    expect(ws.frames()[0]).toEqual({ type: "start", pipeline: false });
  });

  it("asks for the pipeline when the caller is a delivery surface", async () => {
    const { ws } = await openSocket({ pipeline: true });

    expect(ws.frames()[0]).toEqual({ type: "start", pipeline: true });
  });

  it("surfaces the fired command on the final event, with no text", async () => {
    const events: unknown[] = [];
    const session = await startStreamSession((event) => events.push(event), {
      pipeline: true,
    });
    const ws = FakeWebSocket.instances[0];
    ws.emit("open", {});

    const stopped = session.stop();
    ws.emit("message", {
      data: JSON.stringify({
        type: "final",
        text: "",
        fired: { keyword: "standup", kind: "type_text", preview: "types: ## Standup", ok: true },
      }),
    });

    expect(await stopped).toBe("");
    expect(events).toEqual([
      {
        type: "final",
        text: "",
        fired: {
          keyword: "standup",
          kind: "type_text",
          preview: "types: ## Standup",
          ok: true,
        },
      },
    ]);
  });

  it("declares before any audio and before the end frame", async () => {
    const { session, ws } = await openSocket({ pipeline: false });

    const stopped = session.stop();
    ws.emit("message", {
      data: JSON.stringify({ type: "final", text: "verbatim words" }),
    });

    expect(await stopped).toBe("verbatim words");
    const frames = ws.frames().map((frame) => frame.type);
    expect(frames[0]).toBe("start");
    expect(frames).toEqual(["start", "end"]);
  });
});
