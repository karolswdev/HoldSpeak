// HS-172-03 + HS-174-04 — ONE canonical egress-label + scope mapper.
// Maps a model host string to the label the EgressChip shows and the
// scope colour it wears.  Four callers (ProjectRoomCore, MeetingHeader,
// SettingsCore, SystemShade) collapsed here; the vocabulary is:
//   THIS DEVICE        (local/LOCAL/this_device, and loopback: 127.x, localhost)
//   <ip> · LAN         (RFC-1918 private IPs)
//   REMOTE · <ip>      (origin=remote with a caller IP)
//   <host>             (everything else — cloud hosts show as-is)

const PRIVATE_IP_RE = /^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/;

export type EgressScope = "local" | "cloud" | "remote" | undefined;

/** The wire words a model record or a receipt uses for "on this machine". */
const THIS_MACHINE = new Set(["local", "LOCAL", "this_device", "same_device", "THIS DEVICE"]);

/** `http://127.0.0.1:8899/v1` -> `127.0.0.1`; a bare host stays as it is. */
export function bareHost(value: string | null | undefined): string {
  const text = String(value ?? "").trim();
  if (!text) return "";
  try {
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(text)) return new URL(text).hostname.replace(/^\[|\]$/g, "");
  } catch {
    // fall through to the plain split
  }
  const host = text.replace(/^[a-z][a-z0-9+.-]*:\/\//i, "").split("/")[0] ?? "";
  // A bare IPv6 address (`::1`) has no port to strip.
  if ((host.match(/:/g) ?? []).length > 1 && !host.startsWith("[")) return host;
  if (host.startsWith("[")) return host.slice(1, host.indexOf("]") > 0 ? host.indexOf("]") : undefined);
  return host.replace(/:\d+$/, "");
}

/** Loopback: the request never leaves this Mac. Mirrors the transport's
 *  contract exactly (holdspeak/loopback_http.py is_loopback_engine_host):
 *  the word `localhost`, or a loopback IP literal (127.0.0.0/8, ::1). Not
 *  `*.localhost` and not `0.0.0.0`: the transport does not pin those, so a
 *  face must not call them this Mac. */
export function isLoopbackHost(host: string): boolean {
  const h = host.trim().replace(/^\[|\]$/g, "").toLowerCase();
  if (h === "localhost") return true;
  if (/^127\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.test(h)) return h.split(".").every((part) => Number(part) <= 255);
  if (h === "0:0:0:0:0:0:0:1") return true;
  return h.includes("::") && /^(0{0,4}:){2,7}0{0,3}1$/.test(h);
}

export type HostPlace = "mac" | "lan" | "cloud";

/**
 * PHILO-17 (U16): the ONE place a host becomes words. Loopback and the wire
 * words for "here" are this Mac; a private address (or a `lan` engine) is
 * its own host name or IP; anything else is the provider's host. Runs on's
 * lead lines and chips and every egress chip (egressFor) read it.
 */
export function hostPlace(
  hostOrUrl: string | null | undefined,
  kind?: string | null,
): { place: HostPlace; host: string; words: string } {
  const raw = String(hostOrUrl ?? "").trim();
  const host = THIS_MACHINE.has(raw) ? "" : bareHost(raw);
  if (THIS_MACHINE.has(raw) || (host && isLoopbackHost(host))) {
    return { place: "mac", host: "", words: "this Mac" };
  }
  if (kind === "cloud") return { place: "cloud", host, words: host || "the internet" };
  if (kind === "lan" || (host && PRIVATE_IP_RE.test(host))) {
    return { place: "lan", host, words: host || "your network" };
  }
  // No address at all: an in-process engine (MLX, a file) the backend named
  // local. A host that is not loopback is never this Mac, whatever the kind.
  if (!host && (kind === "local" || kind === "preset" || !kind)) return { place: "mac", host: "", words: "this Mac" };
  return { place: "cloud", host, words: host };
}

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
  // HS-200-12: `same_device` is the deployment revision's boundary word
  // (holdspeak/deployment_revisions.py:97), the value a bound intel job
  // records as its host when the model runs here; it read as a cloud host.
  // PHILO-17 (U16): a loopback address (`127.0.0.1`) is this machine too;
  // it read as a cloud host on the meeting, four times.
  const place = hostPlace(host);
  if (place.place === "mac") return { label: "THIS DEVICE", scope: "local" };
  if (place.place === "lan") return { label: `${host} · LAN`, scope: "local" };
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

  // PHILO-15 lane 12 (B25): the Door's create verb reads Create, never
  // the method name (`CREATE FROM SETUP`).
  if (op === "create_from_setup") {
    return "CREATE";
  }

  // Sweep
  if (op === "run_sweep") {
    return "SWEEP";
  }

  // Steward run
  if (op === "project_run_steward" || op === "run_steward") {
    return "STEWARD RUN";
  }

  // PHILO-9-03 (F7): the owner's confirmation that he delivered an update.
  // Past tense only when it happened (Codex Astra r1 finding 1): a refused
  // or failed mark is the attempt, never "MARKED".
  if (op === "mark_update_delivered") {
    return receiptFace(event.outcome).state === "success" ? "MARKED DELIVERED" : "MARK DELIVERED";
  }

  // PHILO-9-06: the owner's project grant, in the grant row's act words
  // (SettingsCore PROJECT_GRANT_WORDS actAllow / actStop).
  if (op === "delegation.grant") {
    return "ALLOW RUN AND PUBLISH";
  }
  if (op === "delegation.revoke") {
    return "STOP RUN AND PUBLISH";
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

/** PHILO-9-03: the hub's refusal codes in plain words, one table for every
 *  face that names a refusal (the delivery line, the steward's start, the
 *  Room's RECEIPTS). An unknown code is said in its own words. */
const REFUSAL_WORDS: Record<string, string> = {
  update_not_published: "NOT PUBLISHED",
  idempotency_conflict: "ALREADY USED",
  // PHILO-9-06: the grant row's own words (SettingsCore GRANT_REFUSAL_TOKEN).
  // Outside the grant's bound the hub answers owner_principal_required.
  owner_principal_required: "OWNER ONLY",
  project_delegation_required: "NO GRANT",
  project_delegation_revoked: "GRANT STOPPED",
  project_delegation_expired: "GRANT EXPIRED",
  steward_policy_required: "NO SAVED POLICY",
  steward_disabled: "STEWARD OFF",
  cooldown_active: "COOLING DOWN",
};

export function refusalWord(code: string): string {
  return REFUSAL_WORDS[code] ?? code.toUpperCase().replace(/_/g, " ");
}

/** PHILO-9-03 (Codex Astra r1 finding 1, closed as a class): every receipt
 *  outcome the Room's RECEIPTS can carry, and how it is drawn -- never a
 *  success chip for anything but a success. */
export type ReceiptFace = { state: "success" | "failure" | "idle" | "warning"; icon: string; word: string | null };

export function receiptFace(outcome: string | null | undefined): ReceiptFace {
  switch ((outcome ?? "").toLowerCase()) {
    case "":
    case "ok":
    case "succeeded":
      return { state: "success", icon: "●", word: null };
    case "refused":
      return { state: "failure", icon: "✗", word: "REFUSED" };
    case "cancelled":
      return { state: "idle", icon: "—", word: "CANCELLED" };
    case "indeterminate":
      return { state: "warning", icon: "⚠", word: "RESULT UNKNOWN" };
    default: // "error", "failed", and anything the face does not know
      return { state: "failure", icon: "✗", word: "FAILED" };
  }
}
