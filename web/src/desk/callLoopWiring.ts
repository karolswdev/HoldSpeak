// HS-154-02 — the wiring: the call loop's onSubmit IS the composer's send.
//
// The call loop (lib/callLoop) takes an onSubmit(text) callback. This
// module binds it to the SAME sendTurn function the ThreadComposer
// uses (desk/threads.ts:sendTurn) — so a voiced utterance goes through
// admission, palette, guardrails, and the fence, exactly like a typed
// message. No parallel turn entrance; no direct fetch to /api/threads/*/turns.
//
// Story 03 will connect this wiring to the live call chip; for now it is
// exported as a clean seam the spy test can prove is real.

import { sendTurn } from "./threads";
import {
  startCallLoop,
  stopCallLoop,
  callLoopState,
  type CallLoopCallbacks,
  type CallLoopError,
} from "../lib/callLoop";

export type { CallLoopError };

export interface CallLoopWiring {
  start: () => Promise<void>;
  stop: () => void;
  state: () => ReturnType<typeof callLoopState>;
}

/** Create a call loop wired to a thread's send path.
 *
 *  `onSubmit` is `sendTurn` — the SAME function the ThreadComposer's
 *  handleSend calls. The caller provides `onError` for the in-flow
 *  error row. */
export function wireCallLoop(
  threadId: string,
  onError: (error: CallLoopError) => void,
  onStateChange?: (state: "idle" | "listening" | "transcribing") => void,
): CallLoopWiring {
  const callbacks: CallLoopCallbacks = {
    onSubmit: (text: string) => {
      // The SAME path the composer uses: sendTurn posts to
      // /api/threads/:id/turns with admission, palette, guardrails.
      void sendTurn(threadId, { text });
    },
    onError,
    onStateChange,
  };

  return {
    start: () => startCallLoop(callbacks),
    stop: () => stopCallLoop(),
    state: () => callLoopState(),
  };
}
