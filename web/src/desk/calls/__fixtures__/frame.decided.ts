// from CALLS-DESIGN §6; replace with a recording when the hub slice lands.
// A call_state frame: his Yes decided the held send; the send is a result.
import type { CallStateFrame } from "../types";
import { callLive } from "./call.live";

export const frameDecided: CallStateFrame = {
  reason: "decided",
  call: {
    ...callLive,
    hold: null,
    results: [
      ...callLive.results,
      { kind: "send", label: "Runbook reminder to Platform channel", ref: "send:runbook-reminder", effect: "sent" },
    ],
  },
};
