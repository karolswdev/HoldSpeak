// HS-172-03 + HS-174-04 — ONE canonical egress-label + scope mapper.
// Maps a model host string to the label the EgressChip shows and the
// scope colour it wears.  Four callers (ProjectRoomCore, MeetingHeader,
// SettingsCore, SystemShade) collapsed here; the vocabulary is:
//   THIS DEVICE        (local/LOCAL/this_device)
//   <ip> · LAN         (RFC-1918 private IPs)
//   REMOTE · <ip>      (origin=remote with a caller IP)
//   <host>             (everything else — cloud hosts show as-is)

const PRIVATE_IP_RE = /^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/;

export type EgressScope = "local" | "cloud" | "remote" | undefined;

/**
 * Derive the egress label and scope for an EgressChip from a raw host
 * string.  Never returns "LOCAL" (the vocabulary is THIS DEVICE / LAN /
 * REMOTE / the host name).
 */
export function egressFor(host: string | null | undefined): {
  label: string;
  scope: EgressScope;
} {
  if (!host) return { label: "", scope: undefined };
  if (host === "local" || host === "LOCAL" || host === "this_device") {
    return { label: "THIS DEVICE", scope: "local" };
  }
  if (host === "THIS DEVICE") {
    return { label: host, scope: "local" };
  }
  if (PRIVATE_IP_RE.test(host)) {
    return { label: `${host} · LAN`, scope: "local" };
  }
  return { label: host, scope: "cloud" };
}

/**
 * HS-174-04 — Derive the egress label and scope for a pipeline event
 * that carries `origin`.  A remote-triggered call shows
 * `REMOTE · <caller ip>` with scope "remote"; a locally spawned
 * operation from a remote trigger shows the host's egress via egressFor.
 *
 * The time is a SEPARATE token after the chip, never inside it.
 */
export function egressForEvent(event: {
  origin?: string | null;
  caller?: string | null;
  host?: string | null;
}): { label: string; scope: EgressScope } {
  if (event.origin === "remote" && event.caller) {
    return { label: `REMOTE · ${event.caller}`, scope: "remote" };
  }
  // Local origin or missing origin: fall through to host-based egress
  return egressFor(event.host ?? event.caller ?? null);
}

/**
 * HS-174-04 — Map a pipeline event's service.method to the human grammar
 * the board uses.  Never shows the class name on a face.
 *
 * Vocabulary:
 *   run_sweep           -> SWEEP (+ ` . N ENTITIES` when summary has a count)
 *   project_run_steward -> STEWARD RUN (+ draft/phase token when present)
 *   list_*, get_*       -> READ . <noun> (noun = method minus prefix, spaces for _)
 *   room                -> READ
 *   unmapped            -> METHOD IN CAPS (underscores as spaces, never the class)
 */
export function receiptLabel(event: {
  op?: string | null;
  title?: string | null;
  outcome?: string | null;
}): string {
  const op = (event.op ?? "").trim();
  if (!op) {
    // Fallback: strip "Service." from the title if present
    const raw = event.title ?? "";
    const dot = raw.indexOf(".");
    if (dot >= 0 && raw.slice(0, dot).endsWith("Service")) {
      return raw.slice(dot + 1).replace(/_/g, " ").toUpperCase();
    }
    return raw.toUpperCase();
  }

  // Sweep
  if (op === "run_sweep") {
    return "SWEEP";
  }

  // Steward run
  if (op === "project_run_steward" || op === "run_steward") {
    return "STEWARD RUN";
  }

  // Reads: list_*, get_*, room
  if (op.startsWith("list_")) {
    const noun = op.slice(5).replace(/_/g, " ").toUpperCase();
    return `READ ${noun}`;
  }
  if (op.startsWith("get_")) {
    const noun = op.slice(4).replace(/_/g, " ").toUpperCase();
    return `READ ${noun}`;
  }
  if (op === "room") {
    return "READ";
  }

  // Unmapped: method in caps, underscores as spaces
  return op.replace(/_/g, " ").toUpperCase();
}
