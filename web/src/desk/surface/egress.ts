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

/** `http://127.0.0.1:8899/v1` -> `127.0.0.1`; a bare host stays as it is.
 *  Astra r2 (M3): the RAW spelling, never a URL parser's normal form
 *  (`new URL` turns `127.0.0.1.` into a loopback name the transport does not
 *  pin). Scheme, userinfo, path and port go; nothing else changes. */
export function bareHost(value: string | null | undefined): string {
  const text = String(value ?? "").trim();
  if (!text) return "";
  let authority = text.replace(/^[a-z][a-z0-9+.-]*:\/\//i, "").split(/[/?#]/)[0] ?? "";
  const at = authority.lastIndexOf("@");
  if (at >= 0) authority = authority.slice(at + 1);
  if (authority.startsWith("[")) {
    const close = authority.indexOf("]");
    return close > 0 ? authority.slice(1, close) : authority.slice(1);
  }
  // A bare IPv6 spelling (`::1`) has no port to strip.
  if ((authority.match(/:/g) ?? []).length > 1) return authority;
  return authority.replace(/:\d*$/, "");
}

/** Python's strict IPv4 (ipaddress): four decimal parts, no leading zeros. */
function ipv4Parts(text: string): number[] | null {
  const parts = text.split(".");
  if (parts.length !== 4) return null;
  const out: number[] = [];
  for (const part of parts) {
    if (!/^(0|[1-9]\d{0,2})$/.test(part)) return null;
    const n = Number(part);
    if (n > 255) return null;
    out.push(n);
  }
  return out;
}

/** Python's strict IPv6 (ipaddress): eight 16-bit groups, one
 *  `::` at most, an optional trailing dotted quad. */
function ipv6Groups(text: string): number[] | null {
  // A scope id (`::1%lo0`) is allowed and does not change the address.
  const scope = text.indexOf("%");
  if (scope >= 0 && (scope === text.length - 1 || text.slice(scope + 1).includes("/"))) return null;
  const addr = scope >= 0 ? text.slice(0, scope) : text;
  if (!addr || (addr.match(/::/g) ?? []).length > 1 || addr.includes(":::")) return null;
  let tail: number[] = [];
  let body = addr;
  const lastColon = body.lastIndexOf(":");
  if (body.slice(lastColon + 1).includes(".")) {
    const v4 = ipv4Parts(body.slice(lastColon + 1));
    if (!v4) return null;
    tail = [(v4[0] << 8) | v4[1], (v4[2] << 8) | v4[3]];
    body = body.slice(0, lastColon + 1);
    if (body.endsWith(":") && !body.endsWith("::")) body = body.slice(0, -1);
  }
  const half = (chunk: string): number[] | null => {
    if (!chunk) return [];
    const out: number[] = [];
    for (const group of chunk.split(":")) {
      if (!/^[0-9a-f]{1,4}$/i.test(group)) return null;
      out.push(parseInt(group, 16));
    }
    return out;
  };
  const room = 8 - tail.length;
  if (body.includes("::")) {
    const [left, right] = body.split("::");
    const l = half(left);
    const r = half(right);
    if (!l || !r || l.length + r.length >= room) return null;
    return [...l, ...new Array(room - l.length - r.length).fill(0), ...r, ...tail];
  }
  const all = half(body);
  if (!all || all.length !== room) return null;
  return [...all, ...tail];
}

/** Loopback: the request never leaves this Mac. Mirrors the transport's
 *  contract exactly (holdspeak/loopback_http.py is_loopback_engine_host:
 *  strip one pair of brackets, lowercase, then the word `localhost` or
 *  `ipaddress.ip_address(...).is_loopback`): 127.0.0.0/8 in strict dotted
 *  quad, `::1`, and the IPv4-mapped `::ffff:127.x.x.x`. Never `*.localhost`,
 *  `0.0.0.0`, a trailing dot (`127.0.0.1.`), leading zeros (`127.00.0.1`) or
 *  `:::1`: the transport does not pin those, so a face must not either. */
export function isLoopbackHost(host: string): boolean {
  const h = host.trim().replace(/^\[|\]$/g, "").toLowerCase();
  if (h === "localhost") return true;
  const v4 = ipv4Parts(h);
  if (v4) return v4[0] === 127;
  const v6 = ipv6Groups(h);
  if (!v6) return false;
  if (v6.slice(0, 7).every((g) => g === 0) && v6[7] === 1) return true;
  // IPv4-mapped (Python 3.13+ reads its IPv4 address).
  return v6.slice(0, 5).every((g) => g === 0) && v6[5] === 0xffff && v6[6] >> 8 === 127;
}

/** Spelled like loopback once normalised (`127.0.0.1.`, `localhost.`), but
 *  not pinned by the transport: the backend calls it the private network
 *  (holdspeak/intel/providers.py), so the face says its host, never this Mac. */
function loopbackLookalike(host: string): boolean {
  return host.endsWith(".") && isLoopbackHost(host.replace(/\.+$/, ""));
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
  if (kind === "lan" || (host && (PRIVATE_IP_RE.test(host) || loopbackLookalike(host)))) {
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
