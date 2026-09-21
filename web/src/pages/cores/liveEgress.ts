/* HS-202-02 — the Live surface's intelligence badge, read from the hub.
 *
 * `/api/runtime/status` publishes `intel_egress` as
 * `{ enabled, provider, can_transmit_offmachine, egress }`
 * (holdspeak/runtime/activity.py:209-234). LiveCore read a `label` key that
 * has never existed, so the chip fell to its "This device" default on every
 * desk and wore a hardcoded `⌂` in front of it (03-interaction-walk.md
 * Appendix B.2). This maps the payload the hub actually sends; with no
 * posture read at all it says nothing, the pattern HistoryCore already
 * proves (HistoryCore.tsx:262-267).
 */

export type EgressBadge = {
  label: string;
  scope: "local" | "cloud";
};

export function intelEgressBadge(posture: unknown): EgressBadge | null {
  if (!posture || typeof posture !== "object") return null;
  const read = posture as Record<string, unknown>;
  if (typeof read.enabled !== "boolean") return null;
  if (!read.enabled) return { label: "INTELLIGENCE OFF", scope: "local" };
  if (typeof read.can_transmit_offmachine !== "boolean") return null;
  if (!read.can_transmit_offmachine)
    return { label: "THIS DEVICE", scope: "local" };
  const provider = String(read.provider ?? "").trim();
  return {
    label: (provider || "OFF DEVICE").toUpperCase(),
    scope: "cloud",
  };
}
