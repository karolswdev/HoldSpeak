// HS-154-02 — the wiring: the call loop's onSubmit IS the composer's send.
//
// The call loop (lib/callLoop) takes an onSubmit(text) callback. This
// module binds it to the SAME submitTurn action the ThreadComposer
// uses — so a voiced utterance appears immediately and goes through
// admission, palette, guardrails, and the fence, exactly like a typed
// message. No parallel turn entrance; no direct fetch to /api/threads/*/turns.
//
import { useThreadStore } from "./threads";
import { clearWriteFailure, reportWriteFailure } from "./hooks/useWriteReceipt";
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
 *  `onSubmit` uses `submitTurn` — the SAME action the ThreadComposer's
 *  handleSend calls. The caller provides `onError` for the in-flow
 *  error row. */
export function wireCallLoop(
  threadId: string,
  onError: (error: CallLoopError) => void,
  onStateChange?: (state: "idle" | "listening" | "transcribing") => void,
): CallLoopWiring {
  const callbacks: CallLoopCallbacks = {
    onSubmit: (text: string) => {
      void useThreadStore.getState().submitTurn(threadId, { text }).then(
        () => clearWriteFailure(),
        (error) => reportWriteFailure("send turn", error, () => callbacks.onSubmit(text)),
      );
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
