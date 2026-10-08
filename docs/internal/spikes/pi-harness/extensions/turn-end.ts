// Spike: report each turn end (pi agent_end) as a Stop-shaped line, the payload `holdspeak agent-hook ingest` reads.
import { appendFileSync } from "node:fs";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const OUT = process.env.HOLDSPEAK_SPIKE_TURN_LOG ?? "/dev/null";

export default function (pi: ExtensionAPI) {
  pi.on("agent_end", async (event: any, ctx: any) => {
    const last = [...event.messages].reverse().find((m: any) => m.role === "assistant");
    const text = (last?.content ?? []).filter((c: any) => c.type === "text").map((c: any) => c.text).join("\n");
    appendFileSync(OUT, JSON.stringify({
      hook_event_name: "Stop",
      session_id: ctx.sessionManager?.getSessionId?.() ?? null,
      transcript_path: ctx.sessionManager?.getSessionFile?.() ?? null,
      cwd: ctx.cwd,
      stop_reason: last?.stopReason ?? null,
      last_assistant_message: text,
    }) + "\n");
  });
}
