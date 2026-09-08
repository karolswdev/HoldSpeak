/* HS-200-05 — the physical hotkey's custody, read off `/api/dictation/readiness`.
 *
 * The defect this answers: the runtime recorded whether the global hotkey
 * listener installed and NOTHING read it, so the owner pressed Right Option,
 * got silence, and had no way to learn the cause. The server now carries both
 * that fact and the honestly-read state of the three macOS grants dictation
 * needs; this file turns them into face tokens.
 *
 * Two rules hold here:
 *  - a state we did not read is UNKNOWN, never a cheerful GRANTED;
 *  - the block says nothing at all when there is nothing to say (UX canon A8:
 *    no counters of zero, and no decorative "everything is fine" row).
 */

export type PermissionState =
  | "granted"
  | "denied"
  | "not_determined"
  | "unknown";

export type ChipKind = "success" | "warning" | "failure";

export interface PermissionRow {
  id: string;
  /** MICROPHONE · INPUT MONITORING · ACCESSIBILITY */
  label: string;
  state: PermissionState;
  /** The chip token the face shows for that state. */
  token: string;
  kind: ChipKind;
  /** ONE token naming what stops working: CAPTURE · HOTKEY · TYPING. */
  neededFor: string;
  /** `System Settings > Privacy & Security > <pane>` as path TOKENS. */
  path: string[];
  /** The macOS deep link. Carried, deliberately not yet spent by a verb. */
  settingsUrl: string;
}

export interface HotkeyCustody {
  /** Whether the block renders at all. */
  show: boolean;
  /** macOS is the only platform with these three grants. */
  supported: boolean;
  /** "⌥R" */
  display: string;
  /** true = installed, false = failed, null = no runtime to ask. */
  available: boolean | null;
  token: string;
  kind: ChipKind;
  /** A classified failure token (PYNPUT MISSING…), never a stack. */
  reason: string;
  /** Only the grants that are NOT granted; granted ones are silent. */
  rows: PermissionRow[];
}

const STATE_TOKENS: Record<PermissionState, { token: string; kind: ChipKind }> = {
  granted: { token: "GRANTED", kind: "success" },
  denied: { token: "DENIED", kind: "failure" },
  not_determined: { token: "NOT ASKED", kind: "warning" },
  unknown: { token: "UNKNOWN", kind: "warning" },
};

function asState(value: unknown): PermissionState {
  return value === "granted" ||
    value === "denied" ||
    value === "not_determined"
    ? value
    : "unknown";
}

function asTokens(value: unknown): string[] {
  return Array.isArray(value) ? value.map((v) => String(v)) : [];
}

/** The empty answer: nothing known, nothing drawn. */
const SILENT: HotkeyCustody = {
  show: false,
  supported: false,
  display: "",
  available: null,
  token: "UNKNOWN",
  kind: "warning",
  reason: "",
  rows: [],
};

export function readHotkeyCustody(readiness: unknown): HotkeyCustody {
  const block = (readiness as Record<string, unknown> | null | undefined)?.[
    "hotkey"
  ] as Record<string, unknown> | undefined;
  if (!block || typeof block !== "object") return SILENT;

  const supported = block.supported === true;
  const available =
    block.available === true ? true : block.available === false ? false : null;
  const rows: PermissionRow[] = (
    Array.isArray(block.permissions) ? block.permissions : []
  )
    .map((raw) => {
      const row = (raw ?? {}) as Record<string, unknown>;
      const state = asState(row.state);
      return {
        id: String(row.id ?? ""),
        label: String(row.label ?? row.id ?? ""),
        state,
        token: STATE_TOKENS[state].token,
        kind: STATE_TOKENS[state].kind,
        neededFor: String(row.needed_for ?? ""),
        path: asTokens(row.path),
        settingsUrl: String(row.settings_url ?? ""),
      };
    })
    // A granted permission has nothing to say; only the missing ones draw.
    .filter((row) => row.state !== "granted");

  /* Off macOS there is no pane to walk to and no grant to read, so the three
     rows would be three honest UNKNOWNs with no next step — noise. There, the
     block speaks only when the listener actually failed. */
  const permissionRows = supported ? rows : [];

  /* The head chip describes the DICTATION PATH, not merely the listener
     object. A listener can install cleanly and still hear nothing when Input
     Monitoring is refused — the exact macOS trap this story exists for — and
     the shots caught the consequence: a green ACTIVE sitting beside a red
     DENIED, which reads as "it works, but". BLOCKED is the honest word for
     an installed listener whose grants are not all in hand. */
  const { token, kind } =
    available === true
      ? permissionRows.length > 0
        ? { token: "BLOCKED", kind: "warning" as ChipKind }
        : { token: "ACTIVE", kind: "success" as ChipKind }
      : available === false
        ? { token: "UNAVAILABLE", kind: "failure" as ChipKind }
        : { token: "UNKNOWN", kind: "warning" as ChipKind };
  const show = supported
    ? available !== true || permissionRows.length > 0
    : available === false;

  return {
    show,
    supported,
    display: String(block.display ?? ""),
    available,
    token,
    kind,
    reason: String(block.reason ?? ""),
    rows: permissionRows,
  };
}
