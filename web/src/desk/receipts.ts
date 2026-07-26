// HS-104-05 — the session receipt line. One composed line, three
// tiers, every figure labeled by its provenance. A tier the hub
// cannot vouch for is ABSENT from the wire and absent here — never
// rendered as zero.
import { apiFetch } from "../lib/api";

export interface SessionReceipt {
  receipt_schema: number;
  session_key: string;
  always: {
    provenance: string;
    elapsed_seconds: number | null;
    steers_delivered: number;
    steers_refused: number;
    holds: Record<string, number>;
  };
  tools: Array<{
    tool: string;
    samples: number;
    p50_seconds?: number;
    p95_seconds?: number;
    max_seconds?: number;
  }>;
  reported?: {
    provenance: string;
    model: string;
    input_tokens: number;
    output_tokens: number;
    cache_read_tokens: number;
    cache_creation_tokens: number;
    reported_at: string;
  };
  estimated?: {
    provenance: string;
    cost_usd: number;
    source: string;
    as_of: string;
  };
}

export async function fetchReceipt(
  sessionKey: string,
): Promise<SessionReceipt | null> {
  try {
    return await apiFetch<SessionReceipt>(
      `/api/sessions/${encodeURIComponent(sessionKey)}/receipt`,
    );
  } catch {
    return null;
  }
}

function elapsedText(seconds: number | null): string | null {
  if (seconds === null || seconds <= 0) return null;
  const s = Math.round(seconds);
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}

/** The composed line, one segment list. Each tier states itself:
 *  the always tier is bare (hub records), the reported tier says
 *  (reported), the estimate wears ≈ + its source and date. */
export function receiptSegments(receipt: SessionReceipt): string[] {
  const out: string[] = [];
  const always = receipt.always;
  const elapsed = elapsedText(always.elapsed_seconds);
  if (elapsed) out.push(elapsed);
  const steers = always.steers_delivered + always.steers_refused;
  if (steers > 0) out.push(`${always.steers_delivered} of ${steers} steers landed`);
  const holds = Object.entries(always.holds)
    .filter(([state, n]) => n > 0 && state !== "held")
    .reduce((n, [, v]) => n + v, 0);
  const pending = always.holds["held"] || 0;
  if (holds + pending > 0) {
    out.push(pending > 0 ? `${holds + pending} holds, ${pending} open` : `${holds} holds`);
  }
  const reported = receipt.reported;
  if (reported) {
    out.push(
      `tokens in ${reported.input_tokens.toLocaleString()} · out ${reported.output_tokens.toLocaleString()} · ` +
        `cache read ${reported.cache_read_tokens.toLocaleString()} · cache new ${reported.cache_creation_tokens.toLocaleString()} (reported)`,
    );
  }
  const estimated = receipt.estimated;
  if (estimated) {
    out.push(`≈ $${estimated.cost_usd.toFixed(2)} (${estimated.source}, ${estimated.as_of})`);
  }
  for (const tool of receipt.tools) {
    if (tool.p50_seconds !== undefined) {
      out.push(`${tool.tool} holds p50 ${tool.p50_seconds}s · p95 ${tool.p95_seconds}s (${tool.samples})`);
    } else if (tool.samples > 0) {
      out.push(`${tool.tool} holds ${tool.samples}, max ${tool.max_seconds}s`);
    }
  }
  return out;
}
