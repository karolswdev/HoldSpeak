// Conductor F2 (Astra round 2 on #906): the two capture races, ported from her
// probes. The real store (`openSession`), the real SessionPullout, MicButton,
// micStreamSession and micSession; only the browser boundary is a double
// (getUserMedia, AudioContext, AudioWorkletNode, WebSocket).
import { act, render, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { SessionPullout } from "../SessionPullout";
import { useSteering } from "../../steering";
import { closeMicSession, drainHold, micPhase } from "../../../lib/micSession";

vi.mock("../../../lib/pendingVoice", () => ({
  loadPendingVoice: async () => null, savePendingVoice: async () => {}, clearPendingVoice: async () => {},
}));

class Worklet {
  static last: Worklet;
  port = { onmessage: null as null | ((e: { data: Float32Array }) => void) };
  connect() {}
  disconnect() {}
  constructor() { Worklet.last = this; }
}
class Context {
  sampleRate = 16000;
  destination = {};
  audioWorklet = { addModule: async () => {} };
  createMediaStreamSource() { return { connect() {}, disconnect() {} }; }
  async suspend() {}
  async resume() {}
  async close() {}
}
class Socket {
  static all: Socket[] = [];
  listeners: Record<string, Array<(e: unknown) => void>> = {};
  constructor() { Socket.all.push(this); }
  addEventListener(t: string, fn: (e: unknown) => void) { (this.listeners[t] ??= []).push(fn); }
  send() {}
  close() { for (const f of this.listeners.close ?? []) f({}); }
}

const realPoll = useSteering.getState().poll;
const mic = () => document.querySelector("[data-testid=session-answer-well] .desk-mic") as HTMLElement;

function browser(getUserMedia: () => Promise<unknown>) {
  Socket.all = [];
  Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia } });
  vi.stubGlobal("AudioContext", Context);
  vi.stubGlobal("AudioWorkletNode", Worklet);
  vi.stubGlobal("WebSocket", Socket);
  Object.assign(URL, { createObjectURL: () => "blob:probe", revokeObjectURL: () => {} });
  useSteering.setState({ poll: vi.fn(async () => {}) } as never);
}

afterEach(() => {
  act(() => useSteering.getState().closeSession());
  useSteering.setState({ poll: realPoll } as never);
  closeMicSession();
  vi.unstubAllGlobals();
});

it("B: a switch while the permission is pending leaves B really recording (A never aborts B's hold)", async () => {
  let grant!: (s: unknown) => void;
  const getUserMedia = vi.fn(() => new Promise((r) => { grant = r; }));
  const track = { enabled: true, stop: vi.fn() };
  browser(getUserMedia);
  render(<SessionPullout />);
  act(() => useSteering.getState().openSession("claude:a", { answer: true }));
  await waitFor(() => expect(getUserMedia).toHaveBeenCalledTimes(1));
  act(() => useSteering.getState().openSession("codex:b", { answer: true }));
  await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
  await act(async () => { grant({ getTracks: () => [track], getAudioTracks: () => [track] }); });
  await waitFor(() => expect(mic().className).toContain("is-listening"));
  act(() => Worklet.last.port.onmessage?.({ data: new Float32Array(1024).fill(0.2) }));
  expect(micPhase()).toBe("held");
  expect(track.enabled).toBe(true);
  expect(drainHold()).not.toBeNull();
});

it("A: a second press while the last answer transcribes waits; the old final never hides the new capture", async () => {
  const track = { enabled: true, stop: vi.fn() };
  browser(vi.fn(async () => ({ getTracks: () => [track], getAudioTracks: () => [track] })));
  render(<SessionPullout />);
  act(() => useSteering.getState().openSession("claude:a", { answer: true }));
  await waitFor(() => expect(mic().className).toContain("is-listening"));
  const first = Socket.all[0];
  act(() => { for (const f of first.listeners.open ?? []) f({}); });
  act(() => mic().click());                                   // stop: transcribing
  await waitFor(() => expect(mic().className).toContain("is-busy"));
  act(() => useSteering.getState().openSession("claude:a", { answer: true }));   // pressed again
  await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
  // Queued: no second capture while the first transcript is pending.
  expect(Socket.all).toHaveLength(1);
  expect(mic().className).toContain("is-busy");
  await act(async () => { for (const f of first.listeners.message ?? []) f({ data: JSON.stringify({ type: "final", text: "First answer" }) }); });
  // The first answer lands; then the queued capture starts and STAYS listening.
  await waitFor(() => expect(mic().className).toContain("is-listening"));
  expect(Socket.all).toHaveLength(2);
  expect((document.querySelector("[data-testid=session-answer-well] .desk-steer-input") as HTMLTextAreaElement).value).toBe("First answer");
  await act(async () => { await new Promise((r) => setTimeout(r, 50)); });
  expect(mic().className).toContain("is-listening");
  expect(micPhase()).toBe("held");
  expect(track.enabled).toBe(true);
});
