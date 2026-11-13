// Settings grants: the ratified grant words, the palette rule, and the grant
// chips and receipts that Remote access and the status bar draw. Moved out of
// SettingsCore.tsx.
import { Button } from "../../../components/signal/Signal";
import {
  Receipt,
  countToken,
  StateChip,
  SurfaceWell,
} from "../../../desk/surface";
import { refusalWord } from "../../../desk/surface/egress";
import { Token } from "../../../desk/surface/Token";
import { clockOf } from "../../../desk/surface/format";

/* PHILO-7-02: the owner's desk delegation grant rides the credential ledger
 * (the RATIFIED canvas, pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-
 * contract/assets/story-02-canvas/README.md). The server sends the grant's
 * EFFECTIVE state (the kernel's own time-aware rule); the face reads `state`
 * only, never a stored column. */
export type GrantState = "LIVE" | "REVOKED" | "EXPIRED";
export type Delegation = { state: GrantState; grant_id: string; expires_at: number | null };
export type OrphanDelegation = Delegation & { identity: string };
/* PHILO-9-07: the owner's project delegation grant, per (agent, project) (the
 * RATIFIED canvas, pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-
 * contract/assets/story-07-grant-canvas/README.md, set A). The same rule: the
 * server sends the EFFECTIVE state; the face reads `state` only. */
export type ProjectDelegation = Delegation & { project_id: string; project_name: string; project_archived?: boolean };
export type OrphanProjectDelegation = ProjectDelegation & { identity: string };

/** The ratified words (set A, the owner, 2026-09-25). The fences read them
 *  from here, so the words and their fences change together. */
export const GRANT_WORDS = {
  allow: "Allow filing",
  stop: "Stop filing",
  live: "FILING ALLOWED",
  stopped: "FILING STOPPED",
  actAllow: "ALLOW FILING",
  actStop: "STOP FILING",
  cannotAllow: "CANNOT ALLOW",
  cannotStop: "CANNOT STOP",
  revokeCredential: "Revoke credential",
  noCredential: "NO CREDENTIAL",
  agents: "AGENTS",
} as const;

/** PHILO-9-07: the project grant's ratified words (set A, the owner,
 *  2026-09-27: "Ratify as drawn"). The fences read them from here. */
export const PROJECT_GRANT_WORDS = {
  allow: "Allow run and publish",
  stop: "Stop run and publish",
  live: "RUN AND PUBLISH ALLOWED",
  stopped: "RUN AND PUBLISH STOPPED",
  actAllow: "ALLOW RUN AND PUBLISH",
  actStop: "STOP RUN AND PUBLISH",
  projects: "Projects",
  credentialRevoked: "CREDENTIAL REVOKED",
  archived: "ARCHIVED",
} as const;

/** Palette compatibility (the canvas's settled rule): a grant's controls
 *  show only where the credential's ISSUED palette holds the tools that grant
 *  covers (measured with holdspeak.mcp.palettes.resolve_palette; fenced
 *  against it by tests/unit/test_philo9_project_grant_face_rule.py). */
export const PROJECT_GRANT_PALETTES = ["PROJECT", "SWEEP", "DESK", "ALL"] as const;
export const DESK_GRANT_PALETTES = ["DESK", "ALL"] as const;

export function paletteHolds(palette: string | string[] | null, named: readonly string[], prefixes: readonly string[]): boolean {
  if (!palette) return true; // unrestricted
  if (typeof palette === "string") return named.includes(palette);
  return palette.some((tool) => prefixes.some((prefix) => tool.startsWith(prefix)));
}

/** The kernel's refusal codes (verbatim) and their plain face words, from
 *  the egress table (`refusalWord`), so the grant row and the Room's refusal
 *  say one word; the code rides `data-code` for the fence. */
export const GRANT_REFUSAL_TOKEN: Record<string, string> = Object.fromEntries(
  [
    "owner_principal_required",
    "desk_delegation_required",
    "desk_delegation_revoked",
    "desk_delegation_expired",
    "project_delegation_required",
    "project_delegation_revoked",
    "project_delegation_expired",
    "invalid_arguments",
  ].map((code) => [code, refusalWord(code)]),
);

export type GrantVerbKind = "allow" | "stop";
export type GrantRefusal = { verb: GrantVerbKind; code: string };
/** The last grant act's receipt, as its route returned it ({operation_id, receipt}). */
export type GrantAct = {
  operation_id: string;
  outcome: "succeeded" | "refused";
  verb: GrantVerbKind;
  code?: string;
  identity: string;
  /** HH:MM, from the kernel receipt's created_at. */
  time: string;
  /** MMM D. */
  date: string;
  /** PHILO-9-07: a project grant's act names its project. */
  kind?: "desk" | "project";
  project?: string;
  /** Set when the grant ended because the owner revoked the credential. */
  reason?: string;
};

export function receiptClock(createdAt: unknown): { time: string; date: string } {
  const seconds = typeof createdAt === "number" ? createdAt : Date.now() / 1000;
  const d = new Date(seconds * 1000);
  return { time: clockOf(d), date: formatExpiry(seconds) };
}

export function grantActFrom(
  body: unknown, outcome: GrantAct["outcome"], verb: GrantVerbKind, identity: string, code?: string,
  extra: Partial<GrantAct> = {},
): GrantAct | null {
  const record = (body && typeof body === "object" ? body : {}) as Record<string, unknown>;
  const receipt = (record.receipt && typeof record.receipt === "object" ? record.receipt : {}) as Record<string, unknown>;
  const operationId = String(record.operation_id ?? receipt.operation_id ?? "");
  if (!operationId) return null;
  return { operation_id: operationId, outcome, verb, code, identity, ...receiptClock(receipt.created_at), ...extra };
}

export function ProjectGrantChip({ grant }: { grant: Delegation | null | undefined }) {
  if (!grant) return null; // never granted: no chip
  return grant.state === "LIVE"
    ? <StateChip state="success" label={PROJECT_GRANT_WORDS.live} data-testid="project-grant-chip" />
    : <StateChip state="idle" label={PROJECT_GRANT_WORDS.stopped} data-testid="project-grant-chip" />;
}

/** The closed row's summary: only LIVE authority. One project by name; more by count. */
export function ProjectGrantSummary({ grants }: { grants: ProjectDelegation[] }) {
  const live = grants.filter((g) => g.state === "LIVE");
  if (live.length === 0) return null;
  return (
    <span data-testid="project-grant-summary">
      <StateChip state="success" label={PROJECT_GRANT_WORDS.live} />{" "}
      <Token className="surface-token" data-chip>
        {live.length === 1 ? live[0].project_name : countToken(live.length, "PROJECT", "PROJECTS")}
      </Token>
    </span>
  );
}

export function GrantChip({ grant }: { grant: Delegation | null | undefined }) {
  if (!grant) return null; // never granted: no chip (no counters of zero)
  return grant.state === "LIVE"
    ? <StateChip state="success" label={GRANT_WORDS.live} data-testid="grant-chip" />
    : <StateChip state="idle" label={GRANT_WORDS.stopped} data-testid="grant-chip" />;
}

export function GrantRefusalChip({ refusal }: { refusal?: GrantRefusal }) {
  if (!refusal) return null;
  return (
    <span data-testid="grant-refused" data-code={refusal.code}>
      <StateChip state="failure" label={refusal.verb === "allow" ? GRANT_WORDS.cannotAllow : GRANT_WORDS.cannotStop} />{" "}
      <Token className="surface-token" data-chip>{refusalWord(refusal.code)}</Token>
    </span>
  );
}

/** The grant's receipt, readable after its row is gone (one species for both outcomes). */
export function GrantReceiptWell({ act }: { act: GrantAct }) {
  const ok = act.outcome === "succeeded";
  const words = act.kind === "project" ? PROJECT_GRANT_WORDS : GRANT_WORDS;
  return (
    <SurfaceWell head="Receipt">
      <div
        className="prefs-grant-receipt"
        data-testid="grant-receipt"
        data-operation-id={act.operation_id}
        data-outcome={act.outcome}
        data-code={act.code}
      >
        {ok ? <StateChip state="success" label="Succeeded" /> : <StateChip state="failure" label="Refused" />}
        <Token className="surface-token" data-chip>
          {ok
            ? (act.verb === "stop" ? words.stopped : words.live)
            : (act.verb === "stop" ? words.actStop : words.actAllow)}
        </Token>
        {!ok && act.code ? (
          <Token className="surface-token" data-chip>{refusalWord(act.code)}</Token>
        ) : null}
        {act.reason ? <Token className="surface-token" data-chip>{act.reason}</Token> : null}
        {act.project ? <span className="gadget-fact">{act.project}</span> : null}
        <span className="gadget-fact">{act.identity}</span>
        <Token className="surface-token" data-chip>By owner</Token>
        <Token className="surface-token" data-chip data-muted>{act.date} {act.time}</Token>
      </div>
    </SurfaceWell>
  );
}

/** The footer's centre slot: ONE library Button whose face is the library Receipt. */
export function GrantFootReceipt({ act, open, onToggle }: { act: GrantAct; open: boolean; onToggle: () => void }) {
  const word = act.outcome === "succeeded" ? (act.verb === "stop" ? "Stopped" : "Allowed") : "Refused";
  return (
    <Button
      variant="ghost"
      dense
      aria-expanded={open}
      className="settings-grant-receipt"
      aria-label={`Receipt ${word.toLowerCase()} ${act.time}`}
      data-testid="foot-receipt"
      data-operation-id={act.operation_id}
      onClick={onToggle}
    >
      <Receipt status={act.outcome === "succeeded" ? "ok" : "danger"} label={word} timestamp={act.time} />
    </Button>
  );
}

/** Format an epoch-seconds timestamp as `MMM D` (e.g. `SEP 12`). */
export function formatExpiry(epochSeconds: number): string {
  const d = new Date(epochSeconds * 1000);
  const months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  return `${months[d.getMonth()]} ${d.getDate()}`;
}
