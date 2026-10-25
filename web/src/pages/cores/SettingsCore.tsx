// HS-95-07 / HS-111-01 — the Settings core, rethought as the OS's own
// Prefs program (the verified audit at .tmp/hs-111-01-audit.md §3):
// a drawer face of authored pref modules; a module swaps the WHOLE
// window body; the footer status bar carries the receipt and the
// refusals; every control is a gadget from the surface kit. The pane
// roster is a code constant — the wire never mints a pane again.
import { wireDate, wireClock } from "../../desk/surface/format";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import type {
  CoreProps,
  SecretState,
  SettingsResponse,
  AuthorityPolicyResponse,
  CalendarSourceFact,
} from "./core-types";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { CONTROL_MODES, controlModeLabel, humanizeWireValue } from "../../lib/productLanguage";
import { documentBuildId } from "../../lib/buildId";
import { useFlushOnLeave } from "../../lib/flushOnLeave";
import { useResource } from "../pageSupport";
import { SurfaceState } from "../../desk/surface/Surface";
import {
  CheckGadget,
  CycleGadget,
  EgressChip,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  GadgetTable,
  PropGadget,
  SecretRow,
  StepperGadget,
  StringGadget,
  type CycleOption,
} from "../../desk/surface/gadgets";
import {
  Disclosure,
  Receipt,
  countToken,
  humanTime,
  StateChip,
  ConfirmVerb,
  GadgetDivider,
  SurfaceColumns,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceWell,
} from "../../desk/surface";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { egressFor, hostPlace } from "../../desk/surface/egress";
import { openSurface, openSurfaceOr } from "../../desk/shell";
import { announceTaskReturn } from "../../desk/returnToTask";
import { HotkeyCapture } from "./settingsBespoke";
import { toggleSfx } from "../../lib/sfx";
// PARKED (HS-170-03): ModelsModule retired — the Concierge is its own window now.
// import { ModelsModule } from "./settingsModels";
import { TtsSettingsBlock } from "./settingsTts";
// PARKED (HS-170-03): CapabilityAssignmentsCore — reached via Concierge Adjust.
// import { CapabilityAssignmentsCore } from "./CapabilityAssignmentsCore";
import { WallpaperModule } from "./settingsWallpaper";
import { RhythmNoticeRows, RhythmSweepFold } from "./settingsRhythm";
import { OwnerNameGroup, PeopleAccessModule, ownerSaveState, useOwnerPreferences } from "./settingsPeople";
import { PrefSection, PrefWindow, clockWord } from "./settingsWindow";
import { ConnectionsPane, type ConnectionsFoot } from "./connections";
import { Destinations } from "./connections/Destinations";
import { RunsOnCore } from "../../features/runson/RunsOnCore";
import "./settingsSurfaceRepair.css";
// HS-139-05: activateLauncher removed (Delivery tile absorbed).
import {
  CADENCE_PRESSURE_OPTIONS,
  INTELLIGENCE_AUTO_OPTIONS,
  LANGUAGE_OPTIONS,
  BuilderToolsModule,
  DeskModule,
  MIR_PROFILE_OPTIONS,
  MODULE_ALIASES,
  PREF_MODULES,
  SETTINGS_SECTIONS,
  type SettingsSectionId,
  PrefStatusBar,
  SettingsRailGlyph,
  WAKE_ACTION_OPTIONS,
  type SettingsHubWire,
} from "./settingsPrefs";

const SECRET_LABELS: Record<string, string> = {
  web_token: "Web pairing token",
  device_psk: "Device audio key",
  telegram_bot_token: "Telegram bot token",
  telegram_pairing_code: "Telegram pairing code",
  failure_webhook_url: "Failure alert webhook",
  failure_webhook_credential: "Failure alert credential",
  companion_webhook_url: "Custom webhook",
};
const ROTATABLE_SECRETS = new Set([
  "web_token",
  "device_psk",
  "telegram_pairing_code",
]);

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

/** Apply one settings transaction even when an older payload lacks a new section. */
export function mergeSettingsChanges(
  source: SettingsResponse,
  changes: Array<[string[], unknown]>,
): SettingsResponse {
  const draft = clone(source);
  for (const [path, next] of changes) {
    if (!path.length) continue;
    let cursor = draft as Record<string, unknown>;
    path.forEach((part, index) => {
      if (index === path.length - 1) {
        cursor[part] = next;
        return;
      }
      const child = cursor[part];
      if (!child || typeof child !== "object" || Array.isArray(child)) {
        cursor[part] = {};
      }
      cursor = cursor[part] as Record<string, unknown>;
    });
  }
  return draft;
}

/** Install the next full-document base before a queued write can overlap it. */
export function installSettingsChanges(
  source: SettingsResponse,
  changes: Array<[string[], unknown]>,
  install: (draft: SettingsResponse) => void,
): SettingsResponse {
  const draft = mergeSettingsChanges(source, changes);
  install(draft);
  return draft;
}

/** Repaint authoritative settings plus only the exact writes still pending. */
export function projectPendingSettingsChanges(
  base: SettingsResponse,
  groups: Array<Array<[string[], unknown]>>,
): SettingsResponse {
  return groups.reduce(
    (draft, changes) => mergeSettingsChanges(draft, changes),
    base,
  );
}

/** HS-175 counsel C8 -- the viewer's LOCAL clock (HH:MM) from an ISO
 * instant (``...Z`` or an offset).  Naive strings parse as local, which
 * is what a hub-local stamp means; an unparseable value prints nothing. */
export function formatLocalClock(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = wireDate(iso);
  if (!d) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Source identity comes from the stored name and canonical source type. */
export function calendarSourceIdentity(source: { label: string; url: string }, reportedType?: string) {
  const native = source.url.trim().toLowerCase().startsWith("eventkit:") || reportedType?.toUpperCase() === "MACOS";
  const snapshot = !native && (reportedType?.toUpperCase() === "SNAPSHOT" || /(?:^|[\\/])calendar-snapshots[\\/][^\\/]+\.ics$/i.test(source.url));
  const type = native ? "Mac calendar" : snapshot ? "Snapshot" : "Calendar feed";
  const name = source.label.trim();
  const technical = /^eventkit:/i.test(name) || /^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(name) || name === source.url;
  return { native, snapshot, type, label: name && !technical ? name : type };
}

/** HS-175 counsel C10 -- the chip beside ``Snapshot``: the resolved
 * vision host (LAN / cloud / paired device) or THIS DEVICE when the model
 * runs here.  ``null`` when no vision model resolves (nothing can leave
 * and the upload refuses by name) -- absence is the signal. */
export function snapshotEgressChip(
  egress: { scope?: string; host?: string | null } | null | undefined,
): { label: string; scope: "local" | "cloud" | "mixed"; title: string } | null {
  if (!egress || !egress.scope) return null;
  const host = (egress.host || "").trim();
  if (!host || hostPlace(host).place === "mac") return null;
  const where = egress.scope === "cloud" ? "a cloud service" : egress.scope === "mesh" ? "a paired device" : "a device on your network";
  return { label: host, scope: egress.scope === "cloud" ? "cloud" : "mixed", title: `The screenshot is sent to ${host} (${where}) for extraction.` };
}

/** Render one egress chip per source with off-device reach. */
export function calendarSourceEgressChips(
  facts: CalendarSourceFact[] | undefined,
): Array<{ id: string; label: string; title: string; scope: "cloud" }> {
  if (!facts) return [];
  const chips: Array<{ id: string; label: string; title: string; scope: "cloud" }> = [];
  for (const fact of facts) {
    if (!fact.egress || !fact.host || !fact.refresh_seconds || !fact.enabled) continue;
    const minutes = Math.round(fact.refresh_seconds / 60);
    if (minutes < 1) continue;
    const host = fact.host.toUpperCase();
    const name = fact.label ? fact.label.toUpperCase() : host;
    chips.push({
      id: fact.id ?? host,
      label: `FETCHES ${name} · ${host} · ${minutes} MIN`,
      title: `Fetches ${fact.label || fact.host} every ${minutes} minutes. No credentials or headers are sent.`,
      scope: "cloud",
    });
  }
  return chips;
}

/* HS-101 round 4 — the glass never wears wire keys: curated names
 * for the fields people actually meet, an acronym dictionary for the
 * rest. */
const FRIENDLY_FIELDS: Record<string, string> = {
  mlx_model: "MLX model",
  llama_cpp_model_path: "llama.cpp model file",
  profile_id: "Engine",
  max_total_latency_ms: "Latency budget",
  journal_retention: "Journal retention",
  n_ctx: "Context window",
};
const ACRONYMS: Record<string, string> = {
  Mlx: "MLX",
  Openai: "OpenAI",
  Api: "API",
  Url: "URL",
  Id: "ID",
  Ui: "UI",
  Llm: "LLM",
  Cpp: "C++",
  Ms: "ms",
  Env: "env",
  Ip: "IP",
  Db: "DB",
  Vad: "VAD",
  Mir: "MIR",
};

function title(key: string) {
  const curated = FRIENDLY_FIELDS[key];
  if (curated) return curated;
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (value) => value.toUpperCase())
    .split(" ")
    .map((word) => ACRONYMS[word] ?? word)
    .join(" ");
}

/* ── HS-172: egress helper (shared) ── */
// intelHostLabel / intelHostScope collapsed into egressFor (desk/surface/egress.ts).

const SECTION_ALIASES: Record<string, SettingsSectionId> = {
  voice: "speak",
  hotkey: "speak",
  transcription: "speak",
  "voice-typing": "speak",
  "wake-word": "speak",
  meetings: "meetings",
  calendar: "accounts",
  rhythm: "notices",
  cadence: "notices",
  integrations: "accounts",
  accounts: "accounts",
  people: "you",
  owner: "you",
  agents: "agents",
  sounds: "desk",
  appearance: "desk",
  presence: "desk",
  wallpaper: "desk",
  desk: "desk",
  system: "this-mac",
  devices: "this-mac",
  models: "this-mac",
  assignments: "this-mac",
  delivery: "this-mac",
};
const LEGACY_FOCUS: Record<string, string> = {
  models: "engines",
  delivery: "engines",
  assignments: "engines",
  integrations: "connections",
  calendar: "calendar",
  wallpaper: "wallpaper",
  people: "owner-name",
  system: "device-name",
};
const SETTINGS_FOCUS_PATHS: Record<string, string> = {
  "owner-name": "owner.name",
  "owner-aliases": "owner.aliases",
  "push-to-talk": "hotkey",
  language: "model.language",
  "preview-before-type": "dictation.preview_before_type",
  "voice-commands": "dictation.macros.enabled",
  "wake-word": "wake_word.enabled",
  "spoken-symbols": "dictation.spoken_symbols",
  "make-summary": "meeting.intelligence_auto",
  "record-by-itself": "meeting.auto_record",
  microphone: "meeting.mic_device",
  export: "meeting.auto_export",
  "quiet-hours": "heartbeat.quiet_hours",
  notify: "heartbeat.notify",
  "daily-brief": "cadence.brief_enabled",
  "max-nudges": "cadence.max_nudges_per_day",
  "desk-sounds": "ui.desk_sounds",
  motion: "motion",
  presence: "presence.enabled",
  "device-name": "mesh.device_name",
  "people-access": "people.access",
};

const SETTINGS_WINGS = [
  { id: "settings", label: "Settings" },
  { id: "models", label: "Engines" },
  { id: "integrations", label: "Accounts" },
];


/** Legacy scope contract retained for callers and old saved desks. The page
 * converts it to a section with `settingsPageScope` below. */
export function settingsScope(scope?: string): { module: string | null; focus?: string } {
  const [head, ...tail] = (scope ?? "").split("::");
  if (!head) return { module: null };
  if (head.startsWith("integration:")) {
    return { module: "integrations", focus: [head.slice("integration:".length), ...tail].filter(Boolean).join("::") };
  }
  // The retired Guide deep link lands in the one Setup window. It is not a
  // Settings wing, so new Settings navigation cannot create a second home.
  if (head === "guide" || head === "setup") return { module: "setup", focus: tail.length ? tail.join("::") : undefined };
  // `desk` is the one old alias whose successor changed section; keep its
  // face meaning ahead of the retired module table's system fallback.
  const module = MODULE_ALIASES[head] ?? (SETTINGS_WINGS.some((entry) => entry.id === head) || PREF_MODULES.some((entry) => entry.id === head) ? head : null);
  return { module, focus: tail.length ? tail.join("::") : undefined };
}

function settingsPageScope(scope?: string): { module: string | null; focus?: string } {
  const [head, ...tail] = (scope ?? "").split("::");
  if (head.startsWith("integration:")) {
    return { module: "accounts", focus: [head.slice("integration:".length), ...tail].filter(Boolean).join("::") };
  }
  const legacy = head === "desk" ? head : MODULE_ALIASES[head] ?? head;
  if (head === "guide" || head === "setup") return { module: "setup", focus: tail.length ? tail.join("::") : undefined };
  const module = SECTION_ALIASES[legacy] ?? (SETTINGS_SECTIONS.some((entry) => entry.id === legacy) ? legacy : null);
  return { module, focus: tail.length ? tail.join("::") : LEGACY_FOCUS[head] };
}

/* ── HS-174-02/03: Remote Access — the credential ledger + issue well ── */

const PALETTE_OPTIONS: CycleOption[] = [
  { value: "PROJECT" },
  { value: "SWEEP" },
  { value: "DESK" },
  { value: "ALL" },
];
const TTL_OPTIONS: CycleOption[] = [
  { value: "43200", label: "12 H" },
  { value: "86400", label: "24 H" },
  { value: "604800", label: "7 D" },
  { value: "2592000", label: "30 D" },
];
type RemoteCredential = {
  id: string;
  identity: string;
  /** Palette name (string like "PROJECT") or resolved tool list. */
  palette: string | string[] | null;
  /** Epoch seconds (converted from monotonic by the server). */
  expires_at: number;
  last_used_at: number | null;
  /** Authoritative active flag from the server. */
  active: boolean;
};

/* PHILO-7-02: the owner's desk delegation grant rides the credential ledger
 * (the RATIFIED canvas, pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-
 * contract/assets/story-02-canvas/README.md). The server sends the grant's
 * EFFECTIVE state (the kernel's own time-aware rule); the face reads `state`
 * only, never a stored column. */
type GrantState = "LIVE" | "REVOKED" | "EXPIRED";
type Delegation = { state: GrantState; grant_id: string; expires_at: number | null };
type OrphanDelegation = Delegation & { identity: string };
/* PHILO-9-07: the owner's project delegation grant, per (agent, project) (the
 * RATIFIED canvas, pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-
 * contract/assets/story-07-grant-canvas/README.md, set A). The same rule: the
 * server sends the EFFECTIVE state; the face reads `state` only. */
type ProjectDelegation = Delegation & { project_id: string; project_name: string; project_archived?: boolean };
type OrphanProjectDelegation = ProjectDelegation & { identity: string };
type ProjectFact = { id: string; name: string; is_archived?: boolean | number | null };

type RemoteWire = {
  enabled: boolean;
  bind_host: string | null;
  port: number | null;
  credentials: (RemoteCredential & {
    delegation?: Delegation | null;
    /** One per project with any stored grant row (absent = never granted). */
    project_delegations?: ProjectDelegation[];
  })[];
  /** Grants LIVE in storage whose identity has no credential row. */
  delegations?: OrphanDelegation[];
  /** Project grants LIVE in storage whose identity has no credential row. */
  project_delegations?: OrphanProjectDelegation[];
  active_count: number;
  total_count: number;
};

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

function paletteHolds(palette: string | string[] | null, named: readonly string[], prefixes: readonly string[]): boolean {
  if (!palette) return true; // unrestricted
  if (typeof palette === "string") return named.includes(palette);
  return palette.some((tool) => prefixes.some((prefix) => tool.startsWith(prefix)));
}

/** The kernel's refusal codes (verbatim) and their plain face tokens; the
 *  code rides `data-code` for the fence. */
export const GRANT_REFUSAL_TOKEN: Record<string, string> = {
  owner_principal_required: "OWNER ONLY",
  desk_delegation_required: "NO GRANT",
  desk_delegation_revoked: "GRANT STOPPED",
  desk_delegation_expired: "GRANT EXPIRED",
  project_delegation_required: "NO GRANT",
  project_delegation_revoked: "GRANT STOPPED",
  project_delegation_expired: "GRANT EXPIRED",
  invalid_arguments: "BAD REQUEST",
};

type GrantVerbKind = "allow" | "stop";
type GrantRefusal = { verb: GrantVerbKind; code: string };
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

function receiptClock(createdAt: unknown): { time: string; date: string } {
  const seconds = typeof createdAt === "number" ? createdAt : Date.now() / 1000;
  const d = new Date(seconds * 1000);
  return { time: d.toTimeString().slice(0, 5), date: formatExpiry(seconds) };
}

function grantActFrom(
  body: unknown, outcome: GrantAct["outcome"], verb: GrantVerbKind, identity: string, code?: string,
  extra: Partial<GrantAct> = {},
): GrantAct | null {
  const record = (body && typeof body === "object" ? body : {}) as Record<string, unknown>;
  const receipt = (record.receipt && typeof record.receipt === "object" ? record.receipt : {}) as Record<string, unknown>;
  const operationId = String(record.operation_id ?? receipt.operation_id ?? "");
  if (!operationId) return null;
  return { operation_id: operationId, outcome, verb, code, identity, ...receiptClock(receipt.created_at), ...extra };
}

function ProjectGrantChip({ grant }: { grant: Delegation | null | undefined }) {
  if (!grant) return null; // never granted: no chip
  return grant.state === "LIVE"
    ? <StateChip state="success" label={PROJECT_GRANT_WORDS.live} data-testid="project-grant-chip" />
    : <StateChip state="idle" label={PROJECT_GRANT_WORDS.stopped} data-testid="project-grant-chip" />;
}

/** The closed row's summary: only LIVE authority. One project by name; more by count. */
function ProjectGrantSummary({ grants }: { grants: ProjectDelegation[] }) {
  const live = grants.filter((g) => g.state === "LIVE");
  if (live.length === 0) return null;
  return (
    <span data-testid="project-grant-summary">
      <StateChip state="success" label={PROJECT_GRANT_WORDS.live} />{" "}
      <span className="surface-token" data-chip>
        {live.length === 1 ? live[0].project_name.toUpperCase() : countToken(live.length, "PROJECT", "PROJECTS")}
      </span>
    </span>
  );
}

function GrantChip({ grant }: { grant: Delegation | null | undefined }) {
  if (!grant) return null; // never granted: no chip (no counters of zero)
  return grant.state === "LIVE"
    ? <StateChip state="success" label={GRANT_WORDS.live} data-testid="grant-chip" />
    : <StateChip state="idle" label={GRANT_WORDS.stopped} data-testid="grant-chip" />;
}

function GrantRefusalChip({ refusal }: { refusal?: GrantRefusal }) {
  if (!refusal) return null;
  return (
    <span data-testid="grant-refused" data-code={refusal.code}>
      <StateChip state="failure" label={refusal.verb === "allow" ? GRANT_WORDS.cannotAllow : GRANT_WORDS.cannotStop} />{" "}
      <span className="surface-token" data-chip>{GRANT_REFUSAL_TOKEN[refusal.code] ?? refusal.code}</span>
    </span>
  );
}

/** The grant's receipt, readable after its row is gone (one species for both outcomes). */
export function GrantReceiptWell({ act }: { act: GrantAct }) {
  const ok = act.outcome === "succeeded";
  const words = act.kind === "project" ? PROJECT_GRANT_WORDS : GRANT_WORDS;
  return (
    <SurfaceWell head="RECEIPT">
      <div
        className="prefs-grant-receipt"
        data-testid="grant-receipt"
        data-operation-id={act.operation_id}
        data-outcome={act.outcome}
        data-code={act.code}
      >
        {ok ? <StateChip state="success" label="SUCCEEDED" /> : <StateChip state="failure" label="REFUSED" />}
        <span className="surface-token" data-chip>
          {ok
            ? (act.verb === "stop" ? words.stopped : words.live)
            : (act.verb === "stop" ? words.actStop : words.actAllow)}
        </span>
        {!ok && act.code ? (
          <span className="surface-token" data-chip>{GRANT_REFUSAL_TOKEN[act.code] ?? act.code}</span>
        ) : null}
        {act.reason ? <span className="surface-token" data-chip>{act.reason}</span> : null}
        {act.project ? <span className="gadget-fact">{act.project}</span> : null}
        <span className="gadget-fact">{act.identity}</span>
        <span className="surface-token" data-chip>BY OWNER</span>
        <span className="surface-token" data-chip data-muted>{act.date} {act.time}</span>
      </div>
    </SurfaceWell>
  );
}

/** The footer's centre slot: ONE library Button whose face is the library Receipt. */
export function GrantFootReceipt({ act, open, onToggle }: { act: GrantAct; open: boolean; onToggle: () => void }) {
  const word = act.outcome === "succeeded" ? (act.verb === "stop" ? "STOPPED" : "ALLOWED") : "REFUSED";
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
function formatExpiry(epochSeconds: number): string {
  const d = new Date(epochSeconds * 1000);
  const months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  return `${months[d.getMonth()]} ${d.getDate()}`;
}

/** True when the credential has not expired (epoch seconds vs now). */
function isActive(expiresAt: number): boolean {
  return expiresAt * 1000 > Date.now();
}

/** Relative age string from epoch seconds (e.g. `2 H AGO`, `3 D AGO`). */
function relativeAge(epochSeconds: number): string {
  const seconds = Math.max(0, Math.floor((Date.now() - epochSeconds * 1000) / 1000));
  if (seconds < 60) return `${seconds} S AGO`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} M AGO`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} H AGO`;
  return `${Math.floor(seconds / 86400)} D AGO`;
}

/** The palette label: the name when a string, or the first entry when a list. */
function paletteLabel(palette: string | string[] | null): string {
  if (!palette) return "ALL";
  if (typeof palette === "string") return palette;
  if (palette.length === 0) return "ALL";
  return palette[0];
}

/* ── HS-200-02: the loaded runtime identity (contract C1) ──────────
 * What this hub ACTUALLY loaded — captured at its process start, so a
 * later checkout cannot move it. The repair chips are the compact state
 * C1 asks the ordinary Desk to fly; the paths and the pid stay inside
 * the RAW fold, which is the diagnostics surface. */

export type RuntimeIdentityWire = {
  identity: {
    backend_version?: string;
    backend_revision?: string;
    backend_revision_source?: string;
    process_start?: string;
    pid?: number;
    frontend_build?: string;
    database_id?: string;
    database_path?: string;
    schema_version_expected?: number | null;
    schema_version_loaded?: number | null;
    config_revision?: string;
  };
  repair?: string[];
  owns_database?: boolean | null;
  diagnoses?: { id: string; token: string; detail: string }[];
  ownership?: { held?: boolean | null; lock_path?: string | null; owner?: Record<string, unknown> | null };
  bundle_on_disk?: string;
};

const shortToken = (value: string, length = 12) =>
  value && value.length > length ? value.slice(0, length) : value;

export function RuntimeIdentityModule({ children }: { children?: ReactNode } = {}) {
  const [wire, setWire] = useState<RuntimeIdentityWire | null>(null);
  const [error, setError] = useState("");
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let live = true;
    apiFetch<RuntimeIdentityWire>("/api/system/identity")
      .then((next) => { if (live) { setWire(next); setError(""); } })
      .catch((err) => { if (live) setError(readableError(err)); });
    return () => { live = false; };
  }, [nonce]);

  // PHILO-17 U35: the build hashes, the schema and the mesh name are
  // diagnostics. They live in ONE RAW fold; only a repair finding (a stale
  // bundle, a second writer) stays on the face, because it needs him.
  if (error) {
    return (
      <>
        <div className="prefs-read-failure" data-testid="runtime-unreadable" role="alert">
          <span>Device read failed · Settings unchanged · Retry</span>
          <Button variant="ghost" dense onClick={() => { setError(""); setNonce((n) => n + 1); }}>Retry</Button>
        </div>
        {children ? <FoldGadget title="More">{children}</FoldGadget> : null}
      </>
    );
  }
  if (!wire) return <><span className="gadget-fact" role="status">Reading device details…</span>{children ? <FoldGadget title="More">{children}</FoldGadget> : null}</>;

  const id = wire.identity ?? {};
  const served = id.frontend_build ?? "";
  const document_ = documentBuildId();
  const tokens = [...(wire.repair ?? [])];
  // The loaded document disagreeing with the process is the same finding,
  // seen from the browser. Never list a token twice.
  if (document_ && served && document_ !== served && !tokens.includes("STALE BUNDLE")) {
    tokens.push("STALE BUNDLE");
  }
  const schema = id.schema_version_loaded ?? id.schema_version_expected;

  return (
    <>
      {tokens.length ? (
        <div className="prefs-hub-chips" data-testid="runtime-repair">
          {tokens.map((token) => (
            <StateChip key={token} state="warning" label={token} />
          ))}
        </div>
      ) : null}
      <FoldGadget title="More">
        <GadgetGroup material="inset" label="Diagnostics">
          <GadgetRow label="Backend">
            <span className="surface-token" data-chip data-testid="runtime-backend">
              {`${id.backend_version ?? "unknown"} · ${shortToken(id.backend_revision ?? "unknown")}`}
            </span>
          </GadgetRow>
          <GadgetRow label="Bundle">
            <span className="surface-token" data-chip data-testid="runtime-bundle">
              {served ? shortToken(served) : "NONE"}
            </span>
          </GadgetRow>
          <GadgetRow label="Document">
            <span className="surface-token" data-chip data-testid="runtime-document">
              {document_ ? shortToken(document_) : "NONE"}
            </span>
          </GadgetRow>
          <GadgetRow label="Schema">
            <span className="surface-token" data-chip data-testid="runtime-schema">
              {schema == null ? "NONE" : `SCHEMA ${schema}`}
            </span>
          </GadgetRow>
          <GadgetRow label="Database">
            <span className="surface-token" data-chip data-testid="runtime-database">
              {shortToken(id.database_id ?? "unknown", 8)}
            </span>
          </GadgetRow>
          <GadgetRow label="Started">
            <span className="surface-token" data-chip data-testid="runtime-started">
              {humanTime(id.process_start ?? "")}
            </span>
          </GadgetRow>
          <GadgetRow label="Identity">
            <Button variant="secondary" dense onClick={() => setNonce((n) => n + 1)}>
              Recheck
            </Button>
          </GadgetRow>
          <GadgetRow label="Config">
            <span className="surface-token" data-chip>{shortToken(id.config_revision ?? "unknown", 8)}</span>
          </GadgetRow>
          <GadgetRow label="Process">
            <span className="surface-token" data-chip>{`PID ${id.pid ?? "—"}`}</span>
          </GadgetRow>
          <GadgetRow label="Owns database">
            <span className="surface-token" data-chip data-testid="runtime-owns">
              {wire.owns_database === true ? "OWNER" : wire.owns_database === false ? "TENANT" : "UNKNOWN"}
            </span>
          </GadgetRow>
          {id.database_path ? (
            <GadgetRow label="Path" wide>
              <span className="surface-token" data-chip data-testid="runtime-path">{id.database_path}</span>
            </GadgetRow>
          ) : null}
          {(wire.diagnoses ?? []).map((finding) => (
            <GadgetRow key={finding.id} label={finding.token} wide>
              <span className="surface-token" data-chip>{finding.detail}</span>
            </GadgetRow>
          ))}
        </GadgetGroup>
        {children}
      </FoldGadget>
    </>
  );
}

/** HS-174: the System module face — owns the display step + hub chips
 *  so the REMOTE chip updates live when the toggle fires. */
function SystemModule({
  hubSystem,
  deviceName,
  deskModule,
  rawWell,
  grantAct,
  receiptOpen,
  onGrantAct,
}: {
  hubSystem: { host: string; mesh: boolean; remote?: boolean };
  deviceName: ReactNode;
  deskModule: ReactNode;
  rawWell: ReactNode;
  grantAct?: GrantAct | null;
  receiptOpen?: boolean;
  onGrantAct?: (act: GrantAct) => void;
}) {
  return (
    <>
      <div className="prefs-hub-chips" data-testid="system-hub-chips">
        <span className="surface-token" data-chip data-testid="system-display">{hubSystem.host}</span>
      </div>
      <SurfaceColumns
        variant="preferences"
        main={<RemoteAccessModule grantAct={grantAct} receiptOpen={receiptOpen} onGrantAct={onGrantAct} />}
        side={deskModule}
      />
      <GadgetGroup material="inset" label="This Mac">
        {deviceName}
      </GadgetGroup>
      {/* PHILO-17 U35: one RAW fold holds the diagnostics (build hashes,
          schema), and the device rows. */}
      <RuntimeIdentityModule>
        {rawWell}
      </RuntimeIdentityModule>
    </>
  );
}

export function RemoteAccessModule({
  onEnabledChange,
  grantAct = null,
  receiptOpen = false,
  onGrantAct,
}: {
  /** Report the live enabled state so the parent can update hub chips. */
  onEnabledChange?: (enabled: boolean) => void;
  /** PHILO-7-02: the last grant act's receipt, and whether its well is open
   *  (the footer's receipt Button toggles it; it outlives the row). */
  grantAct?: GrantAct | null;
  receiptOpen?: boolean;
  onGrantAct?: (act: GrantAct) => void;
} = {}) {
  const [wire, setWire] = useState<RemoteWire | null>(null);
  const [loading, setLoading] = useState(true);
  type ReadTarget = "remote" | "projects";
  const [readErrors, setReadErrors] = useState<Partial<Record<ReadTarget, string>>>({});
  const [writeError, setWriteError] = useState<{ action: string; subject: string; message: string } | null>(null);
  const remoteReads = useRef(0);
  const projectReads = useRef(0);
  const writes = useRef(0);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [issueOpen, setIssueOpen] = useState(false);
  const [issueName, setIssueName] = useState("");
  const [issuePalette, setIssuePalette] = useState("PROJECT");
  const [issueTtl, setIssueTtl] = useState("43200");
  const [issuing, setIssuing] = useState(false);
  const [oneTimeToken, setOneTimeToken] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [toggleBusy, setToggleBusy] = useState(false);
  const [granting, setGranting] = useState<string | null>(null);
  const [refusals, setRefusals] = useState<Record<string, GrantRefusal>>({});
  // PHILO-9-07: the projects a credential row can grant, and which rows are open.
  const [projects, setProjects] = useState<ProjectFact[]>([]);
  const [openRows, setOpenRows] = useState<string[]>([]);

  const fetchRemote = useCallback(async () => {
    const order = ++remoteReads.current;
    setLoading(true);
    try {
      const data = await apiFetch<RemoteWire>("/api/settings/remote");
      if (order !== remoteReads.current) return;
      setWire(data);
      setReadErrors((current) => ({ ...current, remote: undefined }));
      onEnabledChange?.(data.enabled);
    } catch (err) {
      if (order === remoteReads.current) setReadErrors((current) => ({ ...current, remote: readableError(err) }));
    } finally {
      if (order === remoteReads.current) setLoading(false);
    }
  }, [onEnabledChange]);

  const fetchProjects = useCallback(async () => {
    const order = ++projectReads.current;
    setProjectsLoading(true);
    try {
      const listed = await apiFetch<{ projects?: ProjectFact[] }>("/api/projects");
      if (order !== projectReads.current) return;
      setProjects((listed?.projects ?? []).filter((project) => !project.is_archived));
      setReadErrors((current) => ({ ...current, projects: undefined }));
    } catch (err) {
      if (order === projectReads.current) setReadErrors((current) => ({ ...current, projects: readableError(err) }));
    } finally {
      if (order === projectReads.current) setProjectsLoading(false);
    }
  }, []);

  // A new explicit writer owns its outcome. Reads never accept or retry it.
  const beginWrite = () => {
    const order = ++writes.current;
    setWriteError(null);
    return order;
  };
  const failWrite = (order: number, action: string, subject: string, err: unknown) => {
    if (order === writes.current) setWriteError({ action, subject, message: readableError(err) });
  };

  useEffect(() => { void fetchRemote(); }, [fetchRemote]);

  const toggleEnabled = async (next: string) => {
    const enabled = next === "ON";
    const order = beginWrite();
    setToggleBusy(true);
    try {
      await apiFetch("/api/settings/remote", {
        method: "PUT",
        json: { enabled },
      });
      await fetchRemote();
    } catch (err) {
      failWrite(order, `Turn remote access ${enabled ? "on" : "off"}`, "", err);
    } finally {
      setToggleBusy(false);
    }
  };

  const issueCredential = async () => {
    if (!issueName.trim()) return;
    const identity = issueName.trim();
    const order = beginWrite();
    setIssuing(true);
    try {
      const result = await apiFetch<{
        token: string;
        id: string;
        identity: string;
        palette: string;
        expires_at: number;
      }>("/api/settings/remote/credentials", {
        method: "POST",
        json: {
          identity,
          palette: issuePalette,
          ttl_seconds: Number(issueTtl),
        },
      });
      setOneTimeToken(result.token);
      setIssueOpen(false);
      setIssueName("");
      setIssuePalette("PROJECT");
      setIssueTtl("43200");
      await fetchRemote();
    } catch (err) {
      failWrite(order, "Issue credential", identity, err);
    } finally {
      setIssuing(false);
    }
  };

  /** PHILO-7-02: Allow / Stop filing -- delegation.grant / delegation.revoke. */
  const setGrant = async (identity: string, verb: GrantVerbKind) => {
    const order = beginWrite();
    setGranting(identity);
    try {
      const result = await apiFetch(`/api/settings/remote/delegations/${encodeURIComponent(identity)}`, {
        method: verb === "allow" ? "PUT" : "DELETE",
        ...(verb === "allow" ? { json: {} } : {}),
      });
      setRefusals((current) => {
        const next = { ...current };
        delete next[identity];
        return next;
      });
      const act = grantActFrom(result, "succeeded", verb, identity);
      if (act) onGrantAct?.(act);
    } catch (err) {
      const payload = err instanceof ApiError ? err.payload : null;
      const code = payload && typeof payload === "object"
        ? String((payload as Record<string, unknown>).error ?? "")
        : "";
      if (code) {
        setRefusals((current) => ({ ...current, [identity]: { verb, code } }));
        const act = grantActFrom(payload, "refused", verb, identity, code);
        if (act) onGrantAct?.(act);
      } else {
        failWrite(order, GRANT_WORDS[verb], identity, err);
      }
    } finally {
      setGranting(null);
      await fetchRemote();
    }
  };

  /** PHILO-9-07: Allow / Stop run and publish -- project.delegation.grant / .revoke. */
  const setProjectGrant = async (identity: string, projectId: string, projectName: string, verb: GrantVerbKind) => {
    const key = `${identity}/${projectId}`;
    const extra = { kind: "project" as const, project: projectName };
    const order = beginWrite();
    setGranting(key);
    try {
      const result = await apiFetch(
        `/api/settings/remote/delegations/${encodeURIComponent(identity)}/projects/${encodeURIComponent(projectId)}`,
        { method: verb === "allow" ? "PUT" : "DELETE", ...(verb === "allow" ? { json: {} } : {}) },
      );
      setRefusals((current) => {
        const next = { ...current };
        delete next[key];
        return next;
      });
      const act = grantActFrom(result, "succeeded", verb, identity, undefined, extra);
      if (act) onGrantAct?.(act);
    } catch (err) {
      const payload = err instanceof ApiError ? err.payload : null;
      const code = payload && typeof payload === "object"
        ? String((payload as Record<string, unknown>).error ?? "")
        : "";
      if (code) {
        setRefusals((current) => ({ ...current, [key]: { verb, code } }));
        const act = grantActFrom(payload, "refused", verb, identity, code, extra);
        if (act) onGrantAct?.(act);
      } else {
        failWrite(order, PROJECT_GRANT_WORDS[verb], `${identity} · ${projectName}`, err);
      }
    } finally {
      setGranting(null);
      await fetchRemote();
    }
  };

  const revokeCredential = async (id: string, identity: string) => {
    const order = beginWrite();
    setRevoking(id);
    try {
      const result = await apiFetch<Record<string, unknown>>(`/api/settings/remote/credentials/${id}`, {
        method: "DELETE",
      });
      // Durable first: the credential's LIVE grants were revoked BEFORE the
      // credential, each with its own receipt (credential_revoked).
      const projectEnded = Array.isArray(result?.project_grants_revoked)
        ? (result.project_grants_revoked as Record<string, unknown>[])
        : [];
      if (projectEnded.length > 0) {
        const last = projectEnded[projectEnded.length - 1];
        const act = grantActFrom(last, "succeeded", "stop", identity, undefined, {
          kind: "project", project: String(last.project_name ?? ""), reason: PROJECT_GRANT_WORDS.credentialRevoked,
        });
        if (act) onGrantAct?.(act);
      } else if (result?.grant_revoked) {
        const act = grantActFrom(result, "succeeded", "stop", identity);
        if (act) onGrantAct?.(act);
      }
      await fetchRemote();
    } catch (err) {
      failWrite(order, "Revoke credential", identity, err);
    } finally {
      setRevoking(null);
    }
  };

  const copyToken = () => {
    if (oneTimeToken) {
      void navigator.clipboard.writeText(oneTimeToken);
    }
  };

  if (loading && !wire) return <span className="gadget-fact" role="status">Reading remote access…</span>;
  if (readErrors.remote && !wire) return <div className="prefs-read-failure" role="alert"><span>Remote access read failed · Grants unchanged · Retry</span><Button dense variant="ghost" onClick={() => void fetchRemote()}>Retry</Button></div>;

  const enabled = wire?.enabled ?? false;
  const allCredentials = wire?.credentials ?? [];
  // PHILO-7-02: a grant is authority, whatever the transport switch says.
  // ON: every credential row. OFF: the credential rows with a LIVE desk or
  // (PHILO-9-07) a LIVE project grant. Always: every grant row with no credential.
  const credentials = enabled
    ? allCredentials
    : allCredentials.filter((c) => c.delegation?.state === "LIVE"
        || (c.project_delegations ?? []).some((g) => g.state === "LIVE"));
  const delegations = wire?.delegations ?? [];
  const projectOrphans = wire?.project_delegations ?? [];
  const toggleRow = (identity: string, open: boolean) => {
    setOpenRows((rows) => (open ? [...rows.filter((r) => r !== identity), identity] : rows.filter((r) => r !== identity)));
    if (open) {
      // The projects the row can grant: every project that is not archived.
      void fetchProjects();
    }
  };
  const activeCount = credentials.filter((c) => c.active).length;
  const totalCount = allCredentials.length;
  const addressToken = enabled && wire?.port
    ? `${wire.bind_host || "0.0.0.0"}:${wire.port}`
    : null;

  return (
    <GadgetGroup material="inset" label="Remote access" actions={enabled && !issueOpen ? (
      <Button variant="ghost" onClick={() => { setOneTimeToken(null); setIssueOpen(true); }} data-testid="issue-credential-btn">Issue credential</Button>
    ) : undefined}>
      {/* The toggle row */}
      {/* PHILO-17 U35: plain words (was "Streamable HTTP", the transport's
          name); the select keeps its "Remote transport" name. */}
      <GadgetRow label="Other devices">
        <CycleGadget
          label="Remote transport"
          value={enabled ? "ON" : "OFF"}
          options={[{ value: "OFF" }, { value: "ON" }]}
          disabled={toggleBusy || loading}
          onChange={toggleEnabled}
        />
        {enabled && addressToken ? (
          <span className="gadget-fact" data-testid="remote-address">{addressToken}</span>
        ) : null}
        {enabled && totalCount > 0 ? (
          <span className="surface-token" data-chip data-testid="remote-total-count">
            {countToken(totalCount, "CREDENTIAL", "CREDENTIALS")}
          </span>
        ) : null}
      </GadgetRow>

      {/* PHILO-7-02: the ledger renders when any credential row OR any
          grant row is visible, whatever the switch says. */}
      {credentials.length > 0 || delegations.length > 0 || projectOrphans.length > 0 ? (
        <SurfaceLedger
          count={<>
            {GRANT_WORDS.agents}
            {activeCount > 0 ? (
              <> · <span className="surface-token" data-chip data-testid="remote-active-count">
                {countToken(activeCount, "ACTIVE CREDENTIAL", "ACTIVE CREDENTIALS")}
              </span></>
            ) : null}
          </>}
          cols="room"
        >
          {credentials.map((cred) => {
            const projectGrants = cred.project_delegations ?? [];
            const projectCapable = paletteHolds(cred.palette, PROJECT_GRANT_PALETTES, ["project.run_steward"]);
            // A LIVE desk grant always keeps its chip and its Stop (a grant is authority).
            const deskCapable = paletteHolds(cred.palette, DESK_GRANT_PALETTES, ["desk.", "zone.", "decision.", "note.", "kb."])
              || cred.delegation?.state === "LIVE";
            const isOpen = projectCapable && openRows.includes(cred.identity);
            const bodyId = `project-lines-${cred.id}`;
            return (
              <SurfaceLedgerRow
                key={cred.id}
                lead={<StateChip state={cred.active ? "success" : "idle"} label="" icon="●" />}
                primary={cred.identity}
                expands={false}
                open={isOpen}
                data-testid={`credential-row-${cred.id}`}
                cells={<>
                  {deskCapable ? <GrantChip grant={cred.delegation} /> : null}
                  <GrantRefusalChip refusal={refusals[cred.identity]} />
                  <ProjectGrantSummary grants={projectGrants} />
                  <span className="surface-token" data-chip data-testid="palette-token">{paletteLabel(cred.palette)}</span>
                  {cred.active ? (
                    <span className="surface-token" data-chip>
                      EXPIRES {formatExpiry(cred.expires_at)}
                    </span>
                  ) : (
                    <StateChip state="warning" label="EXPIRED" />
                  )}
                  <span className="surface-token" data-chip data-muted>
                    {cred.last_used_at ? `LAST USED ${relativeAge(cred.last_used_at)}` : "NEVER USED"}
                  </span>
                </>}
                trailing={<>
                  {projectCapable ? (
                    // The library Disclosure's trigger; its body is the row's own
                    // expansion slot (the HS-200-15 pattern). No popover, no modal.
                    <Disclosure
                      label={PROJECT_GRANT_WORDS.projects}
                      ariaLabel={`${PROJECT_GRANT_WORDS.projects}: ${cred.identity}`}
                      open={isOpen}
                      onOpenChange={(open) => toggleRow(cred.identity, open)}
                      controlsId={bodyId}
                      variant="default"
                    >
                      {null}
                    </Disclosure>
                  ) : null}
                  {deskCapable ? (
                    <Button
                      variant="ghost"
                      dense
                      disabled={granting === cred.identity}
                      onClick={() => void setGrant(cred.identity, cred.delegation?.state === "LIVE" ? "stop" : "allow")}
                      data-testid="grant-verb"
                    >
                      {cred.delegation?.state === "LIVE" ? GRANT_WORDS.stop : GRANT_WORDS.allow}
                    </Button>
                  ) : null}
                  <Button
                    variant="ghost"
                    dense
                    disabled={revoking === cred.id}
                    onClick={() => void revokeCredential(cred.id, cred.identity)}
                    data-testid="credential-revoke"
                  >
                    {GRANT_WORDS.revokeCredential}
                  </Button>
                </>}
              >
                {projectCapable ? (
                  <div id={bodyId} data-testid={`project-lines-${cred.identity}`}>
                    {[
                      ...projects.map((p) => ({ id: p.id, name: p.name, archived: false })),
                      // Archive keeps a grant (the charter): a LIVE grant on an
                      // archived project stays listed, Stop only, never Allow.
                      ...projectGrants
                        .filter((g) => g.project_archived && g.state === "LIVE")
                        .map((g) => ({ id: g.project_id, name: g.project_name, archived: true })),
                    ].map((p) => {
                      const grant = projectGrants.find((g) => g.project_id === p.id) ?? null;
                      const key = `${cred.identity}/${p.id}`;
                      const live = grant?.state === "LIVE";
                      return (
                        <GadgetRow key={p.id} label={p.name} wide controlWidth="full">
                          <span className="prefs-project-line" data-testid={`project-line-${p.id}`}>
                            {p.archived ? (
                              <span className="surface-token" data-chip data-testid="project-archived">
                                {PROJECT_GRANT_WORDS.archived}
                              </span>
                            ) : null}
                            <ProjectGrantChip grant={grant} />
                            <GrantRefusalChip refusal={refusals[key]} />
                            {live || !p.archived ? (
                              <Button
                                variant="ghost"
                                dense
                                disabled={granting === key}
                                onClick={() => void setProjectGrant(cred.identity, p.id, p.name, live ? "stop" : "allow")}
                                data-testid="project-grant-verb"
                              >
                                {live ? PROJECT_GRANT_WORDS.stop : PROJECT_GRANT_WORDS.allow}
                              </Button>
                            ) : null}
                          </span>
                        </GadgetRow>
                      );
                    })}
                  </div>
                ) : null}
              </SurfaceLedgerRow>
            );
          })}
          {delegations.map((grant) => (
            <SurfaceLedgerRow
              key={grant.grant_id}
              lead={<StateChip state="idle" label="" icon="●" />}
              primary={grant.identity}
              expands={false}
              data-testid={`delegation-row-${grant.grant_id}`}
              cells={<>
                <GrantChip grant={grant} />
                <GrantRefusalChip refusal={refusals[grant.identity]} />
                <span className="surface-token" data-chip data-muted>{GRANT_WORDS.noCredential}</span>
              </>}
              trailing={grant.state === "LIVE" ? (
                <Button
                  variant="ghost"
                  dense
                  disabled={granting === grant.identity}
                  onClick={() => void setGrant(grant.identity, "stop")}
                  data-testid="grant-verb"
                >
                  {GRANT_WORDS.stop}
                </Button>
              ) : undefined}
            />
          ))}
          {/* PHILO-9-07: a LIVE project grant with no credential row (a restart
              or a lost credential), beside Phase 7's desk orphans, with its Stop. */}
          {projectOrphans.map((grant) => {
            const key = `${grant.identity}/${grant.project_id}`;
            return (
              <SurfaceLedgerRow
                key={grant.grant_id}
                lead={<StateChip state="idle" label="" icon="●" />}
                primary={grant.identity}
                expands={false}
                data-testid={`project-delegation-row-${grant.grant_id}`}
                cells={<>
                  <ProjectGrantChip grant={grant} />
                  <GrantRefusalChip refusal={refusals[key]} />
                  <span className="surface-token" data-chip>{grant.project_name.toUpperCase()}</span>
                  {grant.project_archived ? (
                    <span className="surface-token" data-chip data-testid="project-archived">{PROJECT_GRANT_WORDS.archived}</span>
                  ) : null}
                  <span className="surface-token" data-chip data-muted>{GRANT_WORDS.noCredential}</span>
                </>}
                trailing={grant.state === "LIVE" ? (
                  <Button
                    variant="ghost"
                    dense
                    disabled={granting === key}
                    onClick={() => void setProjectGrant(grant.identity, grant.project_id, grant.project_name, "stop")}
                    data-testid="project-grant-verb"
                  >
                    {PROJECT_GRANT_WORDS.stop}
                  </Button>
                ) : undefined}
              />
            );
          })}
        </SurfaceLedger>
      ) : null}

      {/* The last grant act's receipt: outside the removable ledger, so it
          survives when its row disappears; opened from the footer. */}
      {receiptOpen && grantAct ? <GrantReceiptWell act={grantAct} /> : null}

      {/* Everything below only when ON */}
      {enabled ? (
        <>
          {/* One-time token display (after issue, before dismissal) */}
          {oneTimeToken ? (
            <SurfaceWell>
              <div className="prefs-token-once">
                <code className="prefs-token-value" data-testid="token-value">{oneTimeToken}</code>
                <Button variant="ghost" dense onClick={copyToken} data-testid="token-copy">
                  Copy
                </Button>
              </div>
              <span className="prefs-token-caption" data-tone="warning">
                TOKEN SHOWN ONCE — COPY IT NOW
              </span>
            </SurfaceWell>
          ) : null}

          {/* Issue credential verb + well */}
          {issueOpen ? (
            <SurfaceWell>
              <GadgetRow label="Name" controlWidth="full">
                <StringGadget
                  label="Credential name"
                  value={issueName}
                  placeholder="e.g. sweep-runner"
                  onChange={setIssueName}
                  autoFocus
                />
              </GadgetRow>
              <GadgetRow label="Access">
                <CycleGadget
                  label="Access"
                  value={issuePalette}
                  options={PALETTE_OPTIONS}
                  onChange={setIssuePalette}
                />
              </GadgetRow>
              <GadgetRow label="Expires after">
                <CycleGadget
                  label="Expires after"
                  value={issueTtl}
                  options={TTL_OPTIONS}
                  onChange={setIssueTtl}
                />
              </GadgetRow>
              <div className="prefs-issue-actions">
                <Button variant="primary" disabled={issuing || !issueName.trim()} onClick={() => void issueCredential()} data-testid="issue-submit">
                  Issue
                </Button>
                <Button variant="ghost" onClick={() => { setIssueOpen(false); setIssueName(""); }} data-testid="issue-cancel">
                  Cancel
                </Button>
              </div>
            </SurfaceWell>
          ) : null}
        </>
      ) : null}

      {readErrors.remote ? (
        <div className="prefs-read-failure" role="alert" data-testid="remote-read-error">
          <span>Remote access read failed · Grants unchanged · Retry · {humanizeWireValue(readErrors.remote)}</span>
          <Button dense variant="ghost" disabled={loading} onClick={() => void fetchRemote()}>Retry</Button>
        </div>
      ) : null}
      {readErrors.projects ? (
        <div className="prefs-read-failure" role="alert" data-testid="remote-projects-error">
          <span>Project read failed · Projects unchanged · Retry · {humanizeWireValue(readErrors.projects)}</span>
          <Button dense variant="ghost" disabled={projectsLoading} onClick={() => void fetchProjects()}>Retry</Button>
        </div>
      ) : null}
      {writeError ? (
        <div className="prefs-read-failure" role="alert" data-testid="remote-error">
          <span>Change not confirmed · {writeError.action}{writeError.subject ? ` · ${writeError.subject}` : ""} · {humanizeWireValue(writeError.message)}</span>
          <Button dense variant="ghost" disabled={loading} onClick={() => void fetchRemote()}>Reload current state</Button>
        </div>
      ) : null}
    </GadgetGroup>
  );
}

export function SettingsCore(props: CoreProps) {
  return <SettingsFace {...props} />;
}

function SettingsFace({ hero, scope }: CoreProps) {
  // A scope is a new entry intent. The page stays mounted and the scope only
  // chooses its section and row anchor.
  const [navigation, setNavigation] = useState(() => settingsPageScope(scope));
  // Window grammar: at a narrow content width the rail is the first view.
  // An entry with a scope (a palette row, a deep link) opens its pane.
  const [paneOpen, setPaneOpen] = useState(() => Boolean(settingsPageScope(scope).module));
  useEffect(() => {
    const next = settingsPageScope(scope);
    if (next.module === "setup") {
      openSurfaceOr("configure-setup", "/");
      setNavigation({ module: null });
    } else {
      setNavigation(next);
      setHighlight(next.focus ?? "");
      if (next.module) setPaneOpen(true);
    }
  }, [scope]);
  // The You writer lives with the window: its state is the status bar's.
  const ownerPrefs = useOwnerPreferences();
  // Settings opens on the owner's identity category. A legacy "settings"
  // scope still lands on the same face; it never restores the old all-page
  // document.
  const moduleId = navigation.module === "settings" || !navigation.module ? "you" : navigation.module;
  const contentRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const body = contentRef.current?.closest<HTMLElement>(".desk-surface-body");
    if (!body) return;
    body.scrollTop = 0;
  }, [moduleId]);
  const integrationSubject =
    moduleId === "accounts"
      ? navigation.focus
      : null;
  const resource = useResource<SettingsResponse>("/api/settings", {});
  const authority = useResource<AuthorityPolicyResponse>(
    "/api/authority/policy",
    {},
  );
  // HS-170-04: the hub wire — one read for all seven module rows' state tokens.
  const hub = useResource<SettingsHubWire>("/api/settings/hub", {
    models: { engines: 0, groupsSet: 0, defaultSet: false },
    connections: { connected: 0 },
    voice: { live: false, target: "" },
    meetings: { intelligence: false, auto: "off", host: "" },
    rhythm: { loops: 0 },
    sounds: { on: false },
    system: { host: "THIS DEVICE", mesh: false, remote: false },
    posture: "neutral",
    writtenAt: null,
  });
  // null = the drawer face; a module id = that module owns the body.
  // PHILO-7-02: the last grant act's receipt (the footer's centre Button)
  // and whether its RECEIPT well is open under Remote access.
  const [grantAct, setGrantAct] = useState<GrantAct | null>(null);
  const [grantReceiptOpen, setGrantReceiptOpen] = useState(false);
  const [highlight, setHighlight] = useState("");
  const [saving, setSaving] = useState(false);
  const [writtenAt, setWrittenAt] = useState("");
  /** Betterment setup ST1: a Notify or quiet-hours write draws the
   *  embedded sweep again (it reads the same heartbeat). */
  const [heartbeatRevision, setHeartbeatRevision] = useState(0);
  const [refusal, setRefusal] = useState("");
  const [secretBusy, setSecretBusy] = useState("");
  // HS-168-03: connections receipt for the integrations module footer.
  const [connectionsFoot, setConnectionsFoot] = useState<ConnectionsFoot | null>(null);
  const handleConnectionsFooter = useCallback((foot: ConnectionsFoot) => {
    setConnectionsFoot(foot);
  }, []);
  const [authorityBusy, setAuthorityBusy] = useState(false);
  const secrets = (resource.data._secrets ?? {}) as Record<string, SecretState>;
  type SpokenSymbol = { spoken?: string; symbol?: string; attach?: string };
  // An unfinished dictionary row stays on this face, outside the settings
  // document, until its required fields can pass the producer's validation.
  const [spokenSymbolsDraft, setSpokenSymbolsDraft] = useState<SpokenSymbol[] | null>(null);

  // HS-175-03: calendar sources facts for the CALENDAR section.
  const [calSources, setCalSources] = useState<{
    sources: Array<{
      id: string; label: string; type: string; status: string;
      host: string | null; event_count: number;
      last_read: string | null; last_read_at?: string | null; egress: boolean;
    }>;
    auto_record: string;
    auto_record_lead_minutes: number;
    matched_this_week: number;
    snapshot_egress?: { scope: string; host?: string | null } | null;
  } | null>(null);
  // The ONE connect well, two uses: "new" under the Connect row, or a
  // source id under that source's row (pre-filled, Save rewrites its URL).
  const [calWellFor, setCalWellFor] = useState<string | null>(null);
  const [calWellValue, setCalWellValue] = useState("");
  const [calWellName, setCalWellName] = useState("");
  const [calWellError, setCalWellError] = useState("");
  const [calWellSaving, setCalWellSaving] = useState(false);
  const calWellGeneration = useRef(0);
  const calSavePending = useRef(false);
  // The in-world Remove confirm step (never a modal): the armed source id.
  const [calRemoveFor, setCalRemoveFor] = useState<string | null>(null);
  const [calLoading, setCalLoading] = useState(false);
  const [calReadError, setCalReadError] = useState("");
  const loadCalSources = useCallback(async () => {
    setCalLoading(true);
    try {
      setCalSources(await apiFetch<typeof calSources>("/api/calendar/sources"));
      setCalReadError("");
    } catch (error) {
      setCalReadError(readableError(error));
    } finally { setCalLoading(false); }
  }, []);
  // Betterment setup ST1: the one page keeps Calendar in Accounts while
  // Meetings reads the same source facts for Auto-record. Load once when the
  // face mounts so an owner who opens Settings at the top and scrolls to
  // either section sees the real source state without pressing the index.
  useEffect(() => { void loadCalSources(); }, [loadCalSources]);

  /* HS-101 round 3 — the configuring archetype saves ON CHANGE
     (Article VII: no ceremony): every edit lands debounced. HS-111-01:
     the receipt is the footer status bar (USING · WRITTEN hh:mm:ss);
     a refusal replaces it in the danger tone until the next edit. */
  const saveTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(saveTimer.current), []);
  // HS-130-07: Settings is the canonical full-document writer. It threads the
  // FRESHEST `_revision` (via a ref, not the possibly-stale debounced draft)
  // so its own back-to-back saves never self-conflict, while a genuinely
  // concurrent write from another surface is still rejected + reconciled.
  type SettingsWriteJob = {
    id: number;
    changes: Array<[string[], unknown]>;
  };
  const authoritativeBaseRef = useRef<SettingsResponse>(resource.data);
  const revisionRef = useRef<string | undefined>(resource.data._revision);
  const saveQueue = useRef<Promise<void>>(Promise.resolve());
  const pendingJobsRef = useRef<SettingsWriteJob[]>([]);
  const debouncedChangesRef = useRef<Array<[string[], unknown]>>([]);
  const nextJobIdRef = useRef(0);
  const writerFencedRef = useRef(false);
  const failedChangesRef = useRef<Array<[string[], unknown]>>([]);
  const lastFailureRef = useRef("");
  type LeaveWrite = {
    jobIds: number[];
    changes: Array<[string[], unknown]>;
    newerChanges: Array<[string[], unknown]>;
    status: "pending" | "succeeded" | "failed";
  };
  // A leave patch can supersede only the jobs it actually covered, and only
  // after that patch is accepted.  This replaces the old lifetime boolean:
  // a later job must keep its own conflict/refusal path.
  const leaveWritesRef = useRef<LeaveWrite[]>([]);
  const pruneLeaveWrites = () => {
    const liveJobIds = new Set(pendingJobsRef.current.map((job) => job.id));
    leaveWritesRef.current = leaveWritesRef.current.filter(
      (leave) => leave.status === "pending" || leave.jobIds.some((id) => liveJobIds.has(id)),
    );
  };
  const repaintPending = () => {
    const visible = projectPendingSettingsChanges(
      authoritativeBaseRef.current,
      [
        failedChangesRef.current,
        ...pendingJobsRef.current.map((pending) => pending.changes),
        debouncedChangesRef.current,
      ],
    );
    resource.setData(visible);
  };
  useEffect(() => {
    if (pendingJobsRef.current.length || debouncedChangesRef.current.length || failedChangesRef.current.length)
      return;
    authoritativeBaseRef.current = resource.data;
    revisionRef.current = resource.data._revision;
  }, [resource.data]);
  useEffect(() => {
    if (spokenSymbolsDraft === null) return;
    const writesSymbols = ([path]: [string[], unknown]) =>
      path.length === 2 && path[0] === "dictation" && path[1] === "spoken_symbols";
    if (
      debouncedChangesRef.current.some(writesSymbols) ||
      failedChangesRef.current.some(writesSymbols) ||
      pendingJobsRef.current.some((job) => job.changes.some(writesSymbols))
    ) return;
    const confirmed = (authoritativeBaseRef.current.dictation as { spoken_symbols?: SpokenSymbol[] } | undefined)?.spoken_symbols ?? [];
    if (
      confirmed.length === spokenSymbolsDraft.length &&
      confirmed.every((entry, index) =>
        entry.spoken === spokenSymbolsDraft[index].spoken?.trim() &&
        entry.symbol === spokenSymbolsDraft[index].symbol &&
        (entry.attach ?? "none") === (spokenSymbolsDraft[index].attach ?? "none").trim().toLowerCase(),
      )
    ) setSpokenSymbolsDraft(null);
  }, [resource.data, spokenSymbolsDraft]);
  const readAuthoritativeBase = async () => {
    const authoritative = await apiFetch<SettingsResponse>("/api/settings");
    authoritativeBaseRef.current = authoritative;
    revisionRef.current = authoritative._revision;
    writerFencedRef.current = false;
    return authoritative;
  };
  const removePendingJob = (id: number) => {
    pendingJobsRef.current = pendingJobsRef.current.filter(
      (pending) => pending.id !== id,
    );
    pruneLeaveWrites();
  };
  const sameSettingValue = (left: unknown, right: unknown) => {
    if (Object.is(left, right)) return true;
    try {
      return JSON.stringify(left) === JSON.stringify(right);
    } catch {
      return false;
    }
  };
  const clearFailedChangesCoveredByLeave = (changes: Array<[string[], unknown]>) => {
    const finalValues = new Map<string, unknown>();
    for (const [path, next] of changes) finalValues.set(path.join("."), next);
    failedChangesRef.current = failedChangesRef.current.filter(([path, next]) => {
      const key = path.join(".");
      return !finalValues.has(key) || !sameSettingValue(next, finalValues.get(key));
    });
    setRefusal(failedChangesRef.current.length ? lastFailureRef.current : "");
  };
  const leaveCoveredJobIds = () => {
    const covered = new Set<number>();
    for (const leave of leaveWritesRef.current) {
      // A terminal failed attempt still owns these job identities for this
      // leave cycle, so a repeated hide does not duplicate its request.  The
      // status is checked separately before any 409 can be superseded.
      for (const id of leave.jobIds) covered.add(id);
    }
    return covered;
  };
  const newerChangesForLeave = (leave: LeaveWrite) => [
    ...leave.newerChanges,
    ...pendingJobsRef.current
      .filter((job) => !leave.jobIds.includes(job.id))
      .flatMap((job) => job.changes),
    ...debouncedChangesRef.current,
  ];
  const latestValues = (changes: Array<[string[], unknown]>) => {
    const values = new Map<string, unknown>();
    for (const [path, next] of changes) values.set(path.join("."), next);
    return values;
  };
  const performSave = async (job: SettingsWriteJob) => {
    // HS-200-41 (return-to-task, focus half): the control the owner was on
    // when this write began, captured BEFORE the await — see the
    // do-not-steal rule in `desk/returnToTask.ts`.
    const from =
      typeof document !== "undefined"
        ? (document.activeElement as HTMLElement | null)
        : null;
    setSaving(true);
    setRefusal("");
    try {
      if (writerFencedRef.current) await readAuthoritativeBase();
      const payload = mergeSettingsChanges(
        {} as SettingsResponse,
        job.changes,
      );
      const result = await apiFetch<{ settings?: Record<string, unknown> }>(
        "/api/settings",
        {
          method: "PUT",
          json: revisionRef.current
            ? { ...payload, _revision: revisionRef.current }
            : payload,
        },
      );
      const authoritative = result.settings ?? mergeSettingsChanges(authoritativeBaseRef.current, job.changes);
      authoritativeBaseRef.current = authoritative as SettingsResponse;
      revisionRef.current = authoritative._revision as string | undefined;
      failedChangesRef.current = failedChangesRef.current.filter(([path]) => !job.changes.some(([saved]) => saved.join(".") === path.join(".")));
      setRefusal(failedChangesRef.current.length ? lastFailureRef.current : "");
      removePendingJob(job.id);
      repaintPending();
      // The readiness signal AND the focus return, in one call: a face
      // holding an unfinished task re-reads without a reload, and the verb
      // the owner left gets focus back (design D2(a) "Focus return").
      announceTaskReturn(from);
      setWrittenAt(new Date().toTimeString().slice(0, 8));
      void hub.reload();
      if (job.changes.some(([path]) => path[0] === "calendar" || path[0] === "meeting")) void loadCalSources();
      return true;
    } catch (error) {
      // A revisionless leave patch can supersede this save only when this
      // exact job was in that patch and the keepalive was accepted.  A
      // pending or failed leave does not make a conflict disappear.
      const supersededByLeave =
        error instanceof ApiError &&
        error.status === 409 &&
        leaveWritesRef.current.some(
          (leave) => leave.status === "succeeded" && leave.jobIds.includes(job.id),
        );
      if (!supersededByLeave) {
        failedChangesRef.current.push(...job.changes);
        lastFailureRef.current = readableError(error);
        setRefusal(lastFailureRef.current);
      }
      writerFencedRef.current = true;
      removePendingJob(job.id);
      if (!supersededByLeave) {
        try {
          await readAuthoritativeBase();
        } catch {
          // A later queued job must reconcile before it can write.
        }
      }
      repaintPending();
      return false;
    } finally {
      setSaving(false);
    }
  };
  const save = (changes: Array<[string[], unknown]>): Promise<boolean> => {
    for (const leave of leaveWritesRef.current) {
      if (leave.status === "pending") leave.newerChanges.push(...changes);
    }
    const job = { id: ++nextJobIdRef.current, changes };
    pendingJobsRef.current.push(job);
    const next = saveQueue.current.then(
      () => performSave(job),
      () => performSave(job),
    );
    saveQueue.current = next.then(
      () => undefined,
      () => undefined,
    );
    return next;
  };
  const updateMany = (changes: Array<[string[], unknown]>) => {
    installSettingsChanges(resource.data, changes, resource.setData);
    debouncedChangesRef.current.push(...changes);
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      const pending = debouncedChangesRef.current;
      debouncedChangesRef.current = [];
      if (pending.length) void save(pending);
    }, 700);
  };
  const update = (path: string[], next: unknown) => updateMany([[path, next]]);
  // PHILO-17 words: a reload inside the 700 ms delay lost the edit. When the
  // page hides, the unsent edits (and any queued behind a save in flight) go
  // out NOW as one keepalive PUT of only the changed paths, never chained
  // behind the queue (Astra r2 on #1090). It carries no revision, so it
  // applies; an older full-document save still in flight carries the old
  // revision, and the hub refuses it if it lands later.
  useFlushOnLeave(() => {
    clearTimeout(saveTimer.current);
    const unsent = debouncedChangesRef.current;
    const coveredJobIds = leaveCoveredJobIds();
    const queuedJobs = pendingJobsRef.current.filter((job) => !coveredJobIds.has(job.id));
    if (!unsent.length && !queuedJobs.length) return;
    debouncedChangesRef.current = [];
    const changes = [...queuedJobs.flatMap((job) => job.changes), ...unsent];
    const patch = mergeSettingsChanges({} as SettingsResponse, changes);
    const leave: LeaveWrite = {
      jobIds: queuedJobs.map((job) => job.id),
      changes,
      newerChanges: [],
      status: "pending",
    };
    leaveWritesRef.current.push(leave);
    writerFencedRef.current = true;
    void apiFetch<{ settings?: SettingsResponse }>("/api/settings", {
      method: "PUT",
      json: patch,
      keepalive: true,
    }).then((result) => {
      leave.status = "succeeded";
      // Keep later local jobs ahead of this older leave patch.  A keepalive
      // response can arrive after a new ordinary job has already completed;
      // adopting its whole document would repaint that newer value away.
      const newerPaths = new Set(
        newerChangesForLeave(leave).map(([path]) => path.join(".")),
      );
      const acceptedLeaveChanges = changes.filter(([path]) => !newerPaths.has(path.join(".")));
      const rebased = mergeSettingsChanges(
        authoritativeBaseRef.current,
        acceptedLeaveChanges,
      );
      if (result?.settings?._revision && !newerPaths.size) {
        rebased._revision = result.settings._revision;
        revisionRef.current = result.settings._revision;
      }
      authoritativeBaseRef.current = rebased;
      // A newer local write can share the same value/path as this leave
      // patch.  Its own 409 refusal remains authoritative until Retry; only
      // the paths this response actually accepted may clear failed drafts.
      clearFailedChangesCoveredByLeave(acceptedLeaveChanges);
      repaintPending();
      pruneLeaveWrites();
    }).catch((error) => {
      leave.status = "failed";
      // The queued jobs retain their own save/error lifecycle.  Only edits
      // which existed solely in this keepalive need to enter Retry now.
      const newerValues = latestValues(newerChangesForLeave(leave));
      const failedUnsent = unsent.filter(([path]) => {
        const key = path.join(".");
        return !newerValues.has(key);
      });
      if (failedUnsent.length) {
        failedChangesRef.current.push(...failedUnsent);
        lastFailureRef.current = readableError(error);
        setRefusal(lastFailureRef.current);
        repaintPending();
      }
      pruneLeaveWrites();
    });
  });
  const commitMany = async (changes: Array<[string[], unknown]>) => {
    installSettingsChanges(resource.data, changes, resource.setData);
    setRefusal("");
    clearTimeout(saveTimer.current);
    const pending = [...debouncedChangesRef.current, ...changes];
    debouncedChangesRef.current = [];
    return save(pending);
  };
  const retryFailedChanges = () => {
    const newer = [...pendingJobsRef.current.flatMap((job) => job.changes), ...debouncedChangesRef.current];
    const retry = failedChangesRef.current.filter(([path]) => !newer.some(([pending]) => pending.join(".") === path.join(".")));
    return commitMany(retry);
  };
  const reconcileSettings = async () => {
    const reconcile = async () => {
      try {
        await readAuthoritativeBase();
        repaintPending();
        setRefusal(failedChangesRef.current.length ? lastFailureRef.current : "");
        return true;
      } catch (error) {
        setRefusal(readableError(error));
        writerFencedRef.current = true;
        return false;
      }
    };
    const next = saveQueue.current.then(reconcile, reconcile);
    saveQueue.current = next.then(
      () => undefined,
      () => undefined,
    );
    return next;
  };
  const beforeCalendarChange = async () => {
    if (debouncedChangesRef.current.length) {
      const accepted = await commitMany([]);
      return accepted && failedChangesRef.current.length === 0;
    }
    await saveQueue.current;
    return failedChangesRef.current.length === 0;
  };
  const calendarChanged = async () => {
    await reconcileSettings();
    void hub.reload();
    await loadCalSources();
  };

  const changeSecret = async (
    secretId: string,
    action: "replace" | "rotate" | "delete",
    value?: string,
  ) => {
    setSecretBusy(secretId);
    setRefusal(failedChangesRef.current.length ? lastFailureRef.current : "");
    try {
      if (action === "replace") {
        await apiFetch(`/api/settings/secrets/${secretId}`, {
          method: "PUT",
          json: { value },
        });
      } else if (action === "rotate") {
        await apiFetch(`/api/settings/secrets/${secretId}/rotate`, {
          method: "POST",
        });
      } else {
        await apiFetch(`/api/settings/secrets/${secretId}`, {
          method: "DELETE",
        });
      }
      await reconcileSettings();
      void hub.reload();
      setWrittenAt(new Date().toTimeString().slice(0, 8));
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setSecretBusy("");
    }
  };

  const setControlMode = async (controlMode: string) => {
    setAuthorityBusy(true);
    setRefusal(failedChangesRef.current.length ? lastFailureRef.current : "");
    try {
      const result = await apiFetch<Record<string, unknown>>(
        "/api/authority/control-mode",
        {
          method: "PUT",
          json: { control_mode: controlMode },
        },
      );
      authority.setData({ ...authority.data, ...result });
      setRefusal(failedChangesRef.current.length ? lastFailureRef.current : "");
      setWrittenAt(new Date().toTimeString().slice(0, 8));
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setAuthorityBusy(false);
    }
  };

  // The section words are the page index.  They scroll the existing face;
  // they never create a wing or replace the page body.
  const openSection = (id: string, focus = "") => {
    setNavigation({ module: id, focus });
    setHighlight(focus);
    setPaneOpen(true);
  };
  const openModule = (id: string) => {
    const section = SECTION_ALIASES[id] ?? id;
    openSection(section);
  };
  const backToSettings = () => openSection("this-mac");

  /* ── gadget bindings (plain function helpers — never components
        defined in render, which would remount and drop focus) ── */
  const val = (path: string[]): unknown =>
    path.reduce<unknown>(
      (acc, part) =>
        acc && typeof acc === "object"
          ? (acc as Record<string, unknown>)[part]
          : undefined,
      resource.data,
    );
  const hl = (path: string[]) => (SETTINGS_FOCUS_PATHS[highlight] ?? highlight) === path.join(".");
  const check = (path: string[], label: string, fact?: string) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={fact}
      highlight={hl(path)}
      controlWidth="short"
    >
      <CheckGadget
        variant="state"
        label={label}
        checked={Boolean(val(path))}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const str = (
    path: string[],
    label: string,
    opts?: { placeholder?: string; fact?: string },
  ) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={opts?.fact}
      highlight={hl(path)}
      controlWidth="full"
    >
      <StringGadget
        label={label}
        value={val(path) == null ? "" : String(val(path))}
        placeholder={opts?.placeholder}
        onChange={(next) => update(path, next || null)}
      />
    </GadgetRow>
  );
  const num = (
    path: string[],
    label: string,
    opts?: { unit?: string; step?: number; min?: number; max?: number },
  ) => (
    <GadgetRow key={path.join(".")} label={label} highlight={hl(path)} controlWidth="short">
      <StepperGadget
        label={label}
        value={Number(val(path) ?? 0)}
        unit={opts?.unit}
        step={opts?.step}
        min={opts?.min}
        max={opts?.max}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const cyc = (
    path: string[],
    label: string,
    options: CycleOption[],
    fact?: string,
  ) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={fact}
      highlight={hl(path)}
      controlWidth="standard"
    >
      <CycleGadget
        label={label}
        value={val(path) == null ? "" : String(val(path))}
        options={options}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const prop = (
    path: string[],
    label: string,
    opts?: { min?: number; max?: number; step?: number; fact?: string },
  ) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={opts?.fact}
      highlight={hl(path)}
      controlWidth="full"
    >
      <PropGadget
        label={label}
        value={Number(val(path) ?? opts?.min ?? 0)}
        min={opts?.min}
        max={opts?.max}
        step={opts?.step}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const csv = (path: string[], label: string, fact = "comma-separated") => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={fact}
      highlight={hl(path)}
      controlWidth="full"
    >
      <StringGadget
        label={label}
        value={
          Array.isArray(val(path)) ? (val(path) as unknown[]).join(", ") : ""
        }
        onChange={(next) =>
          update(
            path,
            next
              .split(",")
              .map((part) => part.trim())
              .filter(Boolean),
          )
        }
      />
    </GadgetRow>
  );

  /* ── the generic walker: survives ONLY inside System (§3.2) ── */
  const walkerRows = (
    node: Record<string, unknown>,
    path: string[],
  ): ReactNode[] =>
    Object.entries(node).map(([key, item]) => {
      const nextPath = [...path, key];
      if (item !== null && typeof item === "object" && !Array.isArray(item))
        return (
          <GadgetGroup material="inset" key={nextPath.join(".")} label={title(key)}>
            {walkerRows(item as Record<string, unknown>, nextPath)}
          </GadgetGroup>
        );
      if (typeof item === "boolean") return check(nextPath, title(key));
      if (typeof item === "number") return num(nextPath, title(key));
      if (Array.isArray(item)) return csv(nextPath, title(key));
      return str(nextPath, title(key));
    });

  /* ── the authored owner-facing modules ── */
  /* Betterment setup ST1: Calendar has one home, Settings ▸ Accounts. The
     source rows, Add feed and Import image moved here from Meetings (the
     HS-175-03 block, unchanged); Accounts' Calendar row chooses a calendar. */
  const calendarSection = (): ReactNode => {
        const data = resource.data;
        const sourcesPath: string[] = ["calendar", "sources"];
        const sources: Array<{
          id: string;
          label: string;
          url: string;
          enabled: boolean;
        }> = (val(sourcesPath) as any[]) ?? [];
        const patchSource = (
          index: number,
          patch: Record<string, unknown>,
        ) => {
          const next = sources.map((s, i) =>
            i === index ? { ...s, ...patch } : s,
          );
          update(sourcesPath, next);
        };
        // HS-175-03: rows come from the settings sources (first paint
        // carries them), the per-source egress fact from _calendar_sources,
        // and counts / last-read / status from /api/calendar/sources.
        const calFacts = new Map(
          ((data._calendar_sources ?? []) as CalendarSourceFact[]).map((f) => [f.id ?? "", f]),
        );
        const calStats = new Map((calSources?.sources ?? []).map((s) => [s.id, s]));
        const editingSource = sources.find((source) => source.id === calWellFor);
        const editingIdentity = editingSource ? calendarSourceIdentity(editingSource, calStats.get(editingSource.id)?.type) : null;
        const openCalWell = (target: string, prefill: string, name = "") => {
          ++calWellGeneration.current;
          setCalRemoveFor(null);
          setCalWellFor(target);
          setCalWellValue(prefill);
          setCalWellName(name);
          setCalWellError("");
        };
        const closeCalWell = () => {
          ++calWellGeneration.current;
          setCalWellFor(null);
          setCalWellValue("");
          setCalWellName("");
          setCalWellError("");
        };
        const saveCalWell = async () => {
          const url = calWellValue.trim();
          if ((!url && !editingIdentity?.native) || calWellFor === null || calSavePending.current) return;
          const generation = calWellGeneration.current;
          calSavePending.current = true;
          setCalWellSaving(true);
          setCalWellError("");
          const nextSources =
            calWellFor === "new"
              ? [...sources, { id: crypto.randomUUID(), label: calWellName.trim(), url, enabled: true }]
              : sources.map((s) => (s.id === calWellFor ? { ...s, label: calWellName.trim(), ...(editingIdentity?.native || editingIdentity?.snapshot ? {} : { url }) } : s));
          const ok = await commitMany([[sourcesPath, nextSources]]);
          calSavePending.current = false;
          setCalWellSaving(false);
          if (generation !== calWellGeneration.current) return;
          if (ok) {
            closeCalWell();
          } else {
            setCalWellError("Not saved");
          }
        };
        const calWell = (
          <div className="prefs-calendar-well" data-testid="calendar-well">
            <StringGadget label="Calendar name" caption value={calWellName} placeholder={editingIdentity?.type ?? "Calendar name"} onChange={(value) => { ++calWellGeneration.current; setCalWellName(value); setCalWellError(""); }} />
            {!editingIdentity?.native && !editingIdentity?.snapshot ? (
            <StringGadget
              label="Calendar URL or file path"
              value={calWellValue}
              placeholder="Paste an ICS URL or a file path"
              onChange={(value) => { ++calWellGeneration.current; setCalWellValue(value); setCalWellError(""); }}
              caption
              mic
            />
            ) : <FoldGadget title="Details"><code className="prefs-source-location">{editingSource?.url}</code></FoldGadget>}
            {calWellError ? <span className="gadget-fact" role="alert">{calWellError}</span> : null}
            <div className="prefs-calendar-well-actions">
              <Button variant="ghost" dense onClick={closeCalWell}>Cancel</Button>
              <Button dense loading={calWellSaving} disabled={!calWellValue.trim() && !editingIdentity?.native} onClick={() => void saveCalWell()}>Save</Button>
            </div>
          </div>
        );
    // HS-175-03: CALENDAR section replaces the 146 Calendar GadgetGroup.
    // Source rows, the Connect calendar well, Snapshot.
    return (
              <div className="prefs-calendar-section"><GadgetGroup label="Calendar feeds" material="inset" actions={
                  <div data-testid="calendar-connect-row" className="prefs-inline-controls">
                    <Button variant="secondary" dense onClick={() => openCalWell("new", "")} data-testid="calendar-add-btn">Add feed</Button>
                    {(() => { const chip = snapshotEgressChip(calSources?.snapshot_egress); return chip ? <EgressChip label={chip.label} scope={chip.scope} title={chip.title} /> : null; })()}
                    <Button variant="secondary" dense data-testid="calendar-snapshot-btn" onClick={() => {
                      const input = document.createElement("input");
                      input.type = "file"; input.accept = ".png,.jpg,.jpeg,.webp"; input.multiple = true;
                      input.onchange = async () => {
                        if (!input.files?.length) return;
                        const fd = new FormData();
                        for (let i = 0; i < Math.min(input.files.length, 3); i++) fd.append("files", input.files[i]);
                        try { openSurface("review-calendar-snapshot", JSON.stringify(await apiFetch<Record<string, unknown>>("/api/calendar/snapshot", { method: "POST", body: fd }))); }
                        catch (error) { setRefusal(readableError(error)); }
                      }; input.click();
                    }}>Import image</Button>
                  </div>
                }>
                {calLoading && !calSources ? <span className="gadget-fact" role="status">Reading calendars…</span> : null}
                {calReadError ? <div className="prefs-read-failure" role="alert"><span>Calendar read failed · Sources unchanged · Retry</span><Button dense variant="ghost" disabled={calLoading} onClick={() => void loadCalSources()}>Retry</Button></div> : null}
                {sources.length ? <SurfaceLedger count={null} cols="settings-calendar" label="Calendar sources">
                  {sources.map((entry, index) => {
                    const fact = calFacts.get(entry.id);
                    const stat = calStats.get(entry.id);
                    const host = fact?.egress && fact.host ? String(fact.host) : null;
                    const identity = calendarSourceIdentity(entry, stat?.type);
                    const label = identity.label;
                    const type = identity.type;
                    const minutes = fact?.refresh_seconds ? Math.round(fact.refresh_seconds / 60) : 15;
                    const state = (!entry.enabled ? "idle" : stat?.status ?? "idle") as "success" | "failure" | "idle";
                    const editing = calWellFor === entry.id;
                    const removing = calRemoveFor === entry.id;
                    return (
                      <SurfaceLedgerRow
                        key={entry.id}
                        data-testid={`calendar-source-${entry.id}`}
                        wrap
                        lead={<StateChip state={state} icon={"●"} label="" />}
                        primary={<span data-muted={!entry.enabled || undefined} style={!entry.enabled ? { color: "var(--text-muted)" } : undefined}>{label}</span>}
                        cells={
                          <span style={{ display: "inline-flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                            {label !== type ? <span className="gadget-fact">{type}</span> : null}
                            {!entry.enabled ? <span className="gadget-fact">Disabled</span> : null}
                            {/* HS-175 counsel C9 (H2-2): egress where egress happens --
                                the host on an HTTPS source; a file source carries NO
                                chip (absence is the signal, never a reassurance). */}
                            {host
                              ? <EgressChip label={host} scope="cloud" title={`Fetches ${label} from ${host} every ${minutes} minutes. No credentials or headers are sent.`} />
                              : null}
                            {/* C9(b): COUNT(DISTINCT uid) counts events -- named so. */}
                            {(() => { const ct = stat ? countToken(stat.event_count, "EVENT") : null; return ct ? <span className="surface-token" data-chip data-testid="calendar-source-events">{ct}</span> : null; })()}
                            {/* C8: the viewer's local clock from the ISO instant. */}
                            {(() => { const clock = formatLocalClock(stat?.last_read_at) ?? stat?.last_read ?? null; return clock ? <span className="surface-token" data-chip data-testid="calendar-source-last-read">LAST READ {clock}</span> : null; })()}
                          </span>
                        }
                        trailing={
                          <>
                            {/* C10 (H8-2): Edit is withheld on a SNAPSHOT row -- its
                                path is generated by the upload and rewritten by it. */}
                            <Button variant="secondary" dense data-testid="calendar-source-edit" onClick={(e) => { e.stopPropagation(); openCalWell(entry.id, entry.url, entry.label); }}>Edit</Button>
                          </>
                        }
                        open={editing || removing}
                        onToggle={() => {
                          if (editing) closeCalWell(); else openCalWell(entry.id, entry.url, entry.label);
                        }}
                      >
                        {editing ? <>{calWell}<div className="prefs-calendar-well-actions"><Button variant="ghost" dense data-testid="calendar-source-toggle" onClick={() => patchSource(index, { enabled: !entry.enabled })}>{entry.enabled ? "Disable" : "Enable"}</Button><Button variant="ghost" dense data-testid="calendar-source-remove" onClick={() => { closeCalWell(); setCalRemoveFor(entry.id); }}>Remove</Button></div></> : null}
                        {removing ? (
                          <div className="prefs-calendar-well" data-testid="calendar-remove-confirm">
                            <span className="surface-token" data-chip data-tone="danger">REMOVE {label.toUpperCase()}</span>
                            <div className="prefs-calendar-well-actions">
                              <Button variant="danger" dense onClick={() => { setCalRemoveFor(null); update(sourcesPath, sources.filter((_, i) => i !== index)); }}>Remove</Button>
                              <Button variant="ghost" dense onClick={() => setCalRemoveFor(null)}>Cancel</Button>
                          </div>
                        </div>
                      ) : null}
                    </SurfaceLedgerRow>
                  );
                })}
              </SurfaceLedger> : null}
                {/* Add feed reuses the existing source editor. */}
                {calWellFor === "new" ? calWell : null}
                {/* PARKED (Settings audit): a full Connect row repeated Add. */}
            </GadgetGroup></div>
    );
  };

  const renderModule = (id: string): ReactNode => {
    const data = resource.data;
    switch (id) {
      /* ── Voice: hotkey + language + voice typing + wake word ── */
      case "voice": {
        const symbols = spokenSymbolsDraft ?? (val(["dictation", "spoken_symbols"]) ?? []) as SpokenSymbol[];
        const symbolsPath = ["dictation", "spoken_symbols"];
        const writeSymbols = (next: SpokenSymbol[]) => {
          setSpokenSymbolsDraft(next);
          if (next.every((entry) => entry.spoken?.trim() && (entry.symbol?.length ?? 0) > 0)) {
            update(symbolsPath, next);
          }
        };
        const patchSymbol = (index: number, patch: Record<string, string>) =>
          writeSymbols(
            symbols.map((entry, row) =>
              row === index ? { ...entry, ...patch } : entry,
            ),
          );
        const macroItems = (val(["dictation", "macros", "items"]) ??
          []) as unknown[];
        return (
          <>
            <SurfaceColumns
              variant="preferences"
              main={<>
                <GadgetGroup label="Voice typing" material="inset">
                  <HotkeyCapture
                    grouped={false}
                    value={(data.hotkey ?? {}) as Record<string, unknown>}
                    highlight={hl(["hotkey"])}
                    onCommit={(next) =>
                      update(["hotkey"], {
                        ...(data.hotkey as Record<string, unknown>),
                        ...next,
                      })
                    }
                    onRefuse={setRefusal}
                  />
                  {cyc(["model", "language"], "Language", LANGUAGE_OPTIONS)}
                  <GadgetDivider />
                  {check(["dictation", "preview_before_type"], "Preview before type")}
                  {check(
                    ["dictation", "macros", "enabled"],
                    "Voice commands",
                    countToken(macroItems.length, "command", "commands") ?? undefined,
                  )}
                </GadgetGroup>
                <GadgetGroup label="Wake word" material="inset">
                  {check(["wake_word", "enabled"], "Enabled")}
                  {cyc(
                    ["wake_word", "action"],
                    "Action",
                    WAKE_ACTION_OPTIONS,
                  )}
                </GadgetGroup>
              </>}
              side={
                <GadgetGroup
                  label="Spoken symbols"
                  material="inset"
                  actions={<>
                    <Button dense variant="secondary" onClick={() => setSpokenSymbolsDraft([...symbols, { spoken: "", symbol: "", attach: "none" }])}>Add symbol</Button>
                    {spokenSymbolsDraft !== null ? <span className="gadget-fact" role="status">Draft</span> : null}
                  </>}
                >
                  {symbols.length ? (
                    <GadgetTable
                      layout="fields"
                      head={["Spoken", "Symbol", "Attach"]}
                      verbs={(index) => <ConfirmVerb
                        label="Forget"
                        confirmLabel="Forget?"
                        ariaLabel={`Forget symbol ${index + 1}`}
                        onConfirm={() => writeSymbols(symbols.filter((_, row) => row !== index))}
                      />}
                      rows={symbols.map((entry, index) => [
                        <StringGadget
                          key="spoken"
                          label={`Spoken phrase ${index + 1}`}
                          value={entry.spoken ?? ""}
                          placeholder="arrow"
                          onChange={(next) => patchSymbol(index, { spoken: next })}
                        />,
                        <StringGadget
                          key="symbol"
                          label={`Symbol ${index + 1}`}
                          value={entry.symbol ?? ""}
                          placeholder="→"
                          mic={false}
                          onChange={(next) => patchSymbol(index, { symbol: next })}
                        />,
                        <CycleGadget
                          key="attach"
                          label={`Attachment ${index + 1}`}
                          value={entry.attach ?? "none"}
                          options={[
                            { value: "none" },
                            { value: "left" },
                            { value: "right" },
                            { value: "both" },
                          ]}
                          onChange={(next) => patchSymbol(index, { attach: next })}
                        />,
                      ])}
                    />
                  ) : <span className="gadget-fact">No spoken symbols</span>}
                </GadgetGroup>
              }
            />
            {/* HS-139-04/05: all voice RAW wells merged. */}
            <FoldGadget title="More">
              <GadgetGroup material="inset" label="Transcription">
                {num(
                  ["model", "transcribe_timeout_seconds"],
                  "Transcribe timeout",
                  {
                    unit: "s",
                    min: 5,
                    step: 5,
                  },
                )}
              </GadgetGroup>
              <GadgetGroup material="inset" label="Pipeline">
                {csv(["dictation", "pipeline", "stages"], "Stages")}
                {num(
                  ["dictation", "pipeline", "max_total_latency_ms"],
                  "Latency budget",
                  { unit: "ms", min: 0, step: 250 },
                )}
                {num(
                  ["dictation", "pipeline", "rewrite_passes"],
                  "Rewrite passes",
                  {
                    min: 0,
                    max: 5,
                  },
                )}
                {check(
                  ["dictation", "pipeline", "target_detect_llm_enabled"],
                  "LLM target detect",
                )}
                {prop(
                  ["dictation", "pipeline", "target_detect_llm_below"],
                  "Detect below",
                  { min: 0, max: 1, step: 0.05 },
                )}
              </GadgetGroup>
              <GadgetGroup material="inset" label="Wake word">
                {str(["wake_word", "model"], "Model", {
                  placeholder: "hey_jarvis",
                })}
                {prop(["wake_word", "threshold"], "Threshold", {
                  min: 0,
                  max: 1,
                  step: 0.05,
                })}
                {num(["wake_word", "armed_window_seconds"], "Armed window", {
                  unit: "s",
                  min: 1,
                  step: 1,
                })}
              </GadgetGroup>
            </FoldGadget>
          </>
        );
      }
      /* ── Sounds & Presence: desk sounds + presence + mascot ── */
      case "sounds":
        return (
          <SurfaceColumns variant="preferences" main={<>
              <GadgetGroup material="inset" label="Sounds">
                <GadgetRow
                  label="Desk sounds"
                  highlight={hl(["ui", "desk_sounds"])}
                  controlWidth="short"
                >
                  <CheckGadget
                    variant="state"
                    label="DESK SOUNDS"
                    checked={Boolean(val(["ui", "desk_sounds"]) ?? true)}
                    onChange={(next) => {
                      update(["ui", "desk_sounds"], next);
                      toggleSfx(next);
                    }}
                  />
                </GadgetRow>
              </GadgetGroup>
              <GadgetGroup material="inset" label="Presence">
                {check(["presence", "enabled"], "Presence")}
                {check(["presence", "mascot"], "Mascot")}
              </GadgetGroup>
          </>} side={<TtsSettingsBlock />} />
        );
      case "wallpaper":
        // Betterment setup ST1: the one Wallpaper home; the favorite marks
        // came with it from the parked Change places window.
        return <WallpaperModule showFavorites />;
      /* ── Meetings: display fact + intel row + capture + calendar + RAW (incl. actuators) ── */
      case "meetings": {
        const autoVal = String(val(["meeting", "intelligence_auto"]) ?? "every");
        const meetingsHub = (hub.data as Record<string, unknown>).meetings as Record<string, unknown> | undefined;
        // HS-172: null host = no model assigned; real host = chip.
        // The hub returns a host only when a model is actually assigned;
        // until the wire fix lands, fall back to defaultSet as the signal.
        const hubHost = meetingsHub?.host ? String(meetingsHub.host) : null;
        // PHILO-15 B33: the summary ROUTE decides (the hub's `engineSet`, the
        // queue's answer); the host and the default are fallbacks for a hub
        // that sends no route fact.
        const routeEngine = typeof meetingsHub?.engineSet === "boolean" ? meetingsHub.engineSet : null;
        // Astra r1 P2: the owner's OFF is a choice, never a missing model.
        const summariesOff = meetingsHub?.summariesOff === true;
        const hasModel = routeEngine !== null
          ? routeEngine
          : Boolean(hubHost) && hubHost !== "THIS DEVICE"
            ? true
            : Boolean(hub.data.models?.defaultSet);
        const intelHost = hasModel ? hubHost : null;
        const lastRunAt = meetingsHub?.lastRunAt ? String(meetingsHub.lastRunAt) : null;
        const lastRunS = meetingsHub?.lastRunS != null ? Number(meetingsHub.lastRunS) : null;
        const lastRunReceipt = lastRunAt
          ? `LAST RAN ${wireClock(lastRunAt)}${lastRunS != null ? " · " + lastRunS + " S" : ""}`
          : null;
        const autoRecordLink = <Button
          variant="ghost"
          dense
          data-testid="settings-auto-record-link"
          onClick={() => openSurfaceOr("review-meetings", "/history", "record")}
        >Meetings › Record</Button>;
        return (
          <>
            <SurfaceColumns variant="preferences" main={<>
              <GadgetGroup material="inset" label="Summary">
                <GadgetRow label="Make summary" highlight={hl(["meeting", "intelligence_auto"])}>
                  <CycleGadget label="Auto-run the summary" value={autoVal} options={INTELLIGENCE_AUTO_OPTIONS} onChange={(next) => update(["meeting", "intelligence_auto"], next)} />
                </GadgetRow>
                {/* Betterment setup ST1: the engine is a fact line; Engines
                    is its one home (`Engines ›` opens it at Meetings). */}
                <GadgetRow label="Summaries run on" controlWidth="full" highlight={focusHighlight === "engines"}>
                  <span className="prefs-summary-controls" data-testid="settings-summary-controls">
                    {summariesOff ? <StateChip state="idle" label="Summaries off" data-testid="settings-summaries-off" />
                      : hasModel ? <>
                        <span className="prefs-value">{String(meetingsHub?.engine || "Assigned engine")}</span>
                        {intelHost && egressFor(intelHost).label ? <EgressChip label={egressFor(intelHost).label} scope={egressFor(intelHost).scope} /> : null}
                      </> : <StateChip state="warning" label="No engine" data-testid="settings-no-model" />}
                    <Button variant={!hasModel && !summariesOff ? "secondary" : "ghost"} dense onClick={() => openSurfaceOr("configure-runs-on", "/models")} data-testid="settings-engines-link">
                      Engines ›
                    </Button>
                  </span>
                </GadgetRow>
              </GadgetGroup>
              <GadgetGroup material="inset" label="Recording">
                <GadgetRow label="Microphone" highlight={hl(["meeting", "mic_device"])}>
                  <span className="prefs-value">
                    {String(val(["meeting", "mic_device"]) || "System default")}
                  </span>
                </GadgetRow>
                <GadgetRow label="System audio">
                  <span className="prefs-value">
                    {String(val(["meeting", "system_audio_device"]) || "Auto")}
                  </span>
                </GadgetRow>
                <div data-testid="settings-auto-record"><GadgetRow label="Auto-record" highlight={hl(["meeting", "auto_record"])}>{autoRecordLink}</GadgetRow></div>
                <FoldGadget title="Audio devices">
                  <GadgetRow wide label="Mic device" fact="Custom name" controlWidth="full">
                    <StringGadget
                      label="Mic device"
                      placeholder="System default"
                      value={String(val(["meeting", "mic_device"]) ?? "")}
                      onChange={(next) => update(["meeting", "mic_device"], next || null)}
                    />
                  </GadgetRow>
                  <GadgetRow wide label="System audio name" fact="Custom name" controlWidth="full">
                    <StringGadget
                      label="System audio device"
                      placeholder="Auto"
                      value={String(val(["meeting", "system_audio_device"]) ?? "")}
                      onChange={(next) => update(["meeting", "system_audio_device"], next || null)}
                    />
                  </GadgetRow>
                </FoldGadget>
              </GadgetGroup>
            </>} side={<>
            <GadgetGroup material="inset" label="Export">
              <GadgetRow label="Auto export" controlWidth="short" highlight={hl(["meeting", "auto_export"])}>
                <CheckGadget
                  variant="state"
                  label="Auto export"
                  checked={Boolean(val(["meeting", "auto_export"]))}
                  onChange={(next) => update(["meeting", "auto_export"], next)}
                />
              </GadgetRow>
              {Boolean(val(["meeting", "auto_export"])) ? (
                <GadgetRow label="Format">
                  <CycleGadget
                    label="Export format"
                    value={String(val(["meeting", "export_format"]) ?? "markdown")}
                    options={[
                      { value: "txt", label: "TXT" },
                      { value: "markdown", label: "MD" },
                      { value: "json", label: "JSON" },
                      { value: "srt", label: "SRT" },
                    ]}
                    onChange={(next) => update(["meeting", "export_format"], next)}
                  />
                </GadgetRow>
              ) : null}
            </GadgetGroup>
            </>} />
            {/* HS-139-04: all operator knobs fold behind one RAW well.
                PHILO-17 U35: Allow actuators is one of them (it sat on the
                face), and the fold carries no hand-kept count. */}
            <FoldGadget title="More">
              {lastRunReceipt ? <span className="gadget-fact" data-testid="settings-last-ran">{lastRunReceipt}</span> : null}
              <GadgetGroup material="inset" label="Capture">
                {check(["meeting", "diarization_enabled"], "Diarization")}
                {check(["meeting", "diarize_mic"], "Diarize mic")}
                {prop(["meeting", "similarity_threshold"], "Similarity", {
                  min: 0,
                  max: 1,
                  step: 0.05,
                })}
              </GadgetGroup>
              {/* HS-202-04 (F06): same rule, the advanced sheet. */}
              <GadgetGroup material="inset" label="Summary">
                {check(["meeting", "intel_cloud_store"], "Cloud store")}
              </GadgetGroup>
              <GadgetGroup material="inset" label="Deferred queue">
                {num(["meeting", "intel_retry_base_seconds"], "Retry base", {
                  unit: "s",
                  min: 1,
                  step: 5,
                })}
                {num(["meeting", "intel_retry_max_seconds"], "Retry max", {
                  unit: "s",
                  min: 1,
                  step: 60,
                })}
                {num(
                  ["meeting", "intel_retry_max_attempts"],
                  "Retry attempts",
                  {
                    min: 1,
                  },
                )}
                {/* PARKED: alert webhook header is not persisted by this writer. */}
              </GadgetGroup>
              <GadgetGroup material="inset" label="Routing">
                {cyc(
                  ["meeting", "routing_profile"],
                  "Routing profile",
                  MIR_PROFILE_OPTIONS,
                )}
                {check(["meeting", "intent_router_enabled"], "Intent router")}
                {num(["meeting", "intent_window_seconds"], "Intent window", {
                  unit: "s",
                  min: 10,
                  step: 10,
                })}
                {num(["meeting", "intent_step_seconds"], "Intent step", {
                  unit: "s",
                  min: 5,
                  step: 5,
                })}
                {prop(
                  ["meeting", "intent_score_threshold"],
                  "Score threshold",
                  {
                    min: 0,
                    max: 1,
                    step: 0.05,
                  },
                )}
                {num(
                  ["meeting", "intent_hysteresis_windows"],
                  "Hysteresis windows",
                  { min: 0, max: 10 },
                )}
                {check(
                  ["meeting", "intent_segment_probe_enabled"],
                  "Segment probe",
                )}
                {csv(["meeting", "disabled_plugins"], "Disabled plugins")}
              </GadgetGroup>
              <GadgetGroup material="inset" label="Actuators">
                {check(["meeting", "allow_actuators"], "Allow actuators")}
                {csv(["meeting", "allowed_actuators"], "Allowed actuators")}
                {csv(["meeting", "webhook_allowed_hosts"], "Webhook hosts")}
              </GadgetGroup>
            </FoldGadget>
          </>
        );
      }
      /* ── Rhythm: cadence user-facing + Telegram + RAW ── */
      case "rhythm":
        return (
          <>
            <SurfaceColumns variant="preferences" main={<>
              {/* Betterment setup ST1: quiet hours have one store, the
                  heartbeat policy the notices loop reads; Notify moved here
                  from the parked Rhythm window. */}
              <RhythmNoticeRows
                highlight={focusHighlight}
                onSaved={() => setWrittenAt(new Date().toTimeString().slice(0, 8))}
                onWrite={() => setHeartbeatRevision((n) => n + 1)}
              />
              <GadgetGroup material="inset" label="Cadence">
                {check(["cadence", "enabled"], "Enabled")}
                {cyc(
                  ["cadence", "pressure"],
                  "Pressure",
                  CADENCE_PRESSURE_OPTIONS,
                )}
                {num(["cadence", "max_nudges_per_day"], "Max nudges", {
                  unit: "/day",
                  min: 0,
                })}
              </GadgetGroup>
            </>} side={<>
              {/* PHILO-15 05: the morning Brief job, ON by default; its own setting. */}
              <GadgetGroup material="inset" label="Morning brief">
                {check(["cadence", "brief_enabled"], "Enabled")}
                {num(["cadence", "brief_hour"], "Make at", {
                  unit: "h",
                  min: 0,
                  max: 23,
                })}
              </GadgetGroup>
            </>} />
            {/* HS-139-04: operator knobs fold behind RAW. */}
            <FoldGadget title="More">
              <GadgetGroup material="inset">
                {check(["cadence", "use_llm"], "Use LLM")}
                {num(["cadence", "tick_interval_seconds"], "Tick interval", {
                  unit: "s",
                  min: 30,
                  step: 30,
                })}
                {csv(["cadence_telegram", "allowed_chat_ids"], "Allowed chats")}
              </GadgetGroup>
              {/* Betterment setup ST1: the parked Rhythm window's sweep
                  interval, Run now, Where it runs, mutes and loops. */}
              <RhythmSweepFold revision={heartbeatRevision} />
            </FoldGadget>
          </>
        );
      /* ── Models: legacy deep-link compatibility. Engines is its own Desk
         window; this branch remains for callers that still render a module
         directly. ── */
      case "models":
      case "assignments": {
        return <RunsOnCore scope={navigation.focus} title="Settings" onBack={backToSettings} />;
      }
      /* ── Connections: tools + credentials + RAW ── */
      case "integrations": {
        const RAW_SECRETS = new Set([
          "failure_webhook_url",
          "failure_webhook_credential",
        ]);
        const keepSecrets = Object.entries(secrets).filter(
          ([id]) => !RAW_SECRETS.has(id),
        );
        const rawSecrets = Object.entries(secrets).filter(([id]) =>
          RAW_SECRETS.has(id),
        );
        const secretRow = ([secretId, state]: [string, SecretState]) => (
          <SecretRow
            key={secretId}
            label={SECRET_LABELS[secretId] ?? title(secretId)}
            configured={Boolean(state.configured)}
            destination={state.destination}
            busy={secretBusy === secretId}
            rotatable={ROTATABLE_SECRETS.has(secretId)}
            onReplace={(value) => void changeSecret(secretId, "replace", value)}
            onRotate={() => void changeSecret(secretId, "rotate")}
            onDelete={() => void changeSecret(secretId, "delete")}
          />
        );
        return (
          <div className="prefs-groups">
            <div className="prefs-column">
              {/* HS-168-03: the Connections face above credentials + mesh. */}
              <ConnectionsPane
                onFooterUpdate={handleConnectionsFooter}
                onOpenModule={openModule}
                focusProvider={integrationSubject}
                onBeforeCalendarChange={beforeCalendarChange}
                onCalendarChanged={calendarChanged}
              />
              {/* Betterment setup ST1: Calendar's one home is Accounts. The
                  source rows, Add feed and Import image moved here from
                  Meetings, under the Calendar row's Choose calendar. */}
              {calendarSection()}
            </div>
            <div className="prefs-column">
              {/* PHILO-10-04 (B1): the Destinations group, under Tools. */}
              <Destinations />
              {/* Betterment ST7: Telegram is an account destination. Keep its
                  existing cadence_telegram writer; only its Settings home
                  moves from Notices to Accounts. */}
              <GadgetGroup material="inset" label="Telegram">
                {check(["cadence_telegram", "enabled"], "Enabled")}
              </GadgetGroup>
              {/* PHILO-17 REFIT: keys and tokens are technical; they fold. */}
              <FoldGadget title="Credentials">
                <GadgetGroup>
                  {keepSecrets.map(secretRow)}
                </GadgetGroup>
              </FoldGadget>
              {/* HS-139-04: operator-wiring secrets fold behind RAW. */}
              {rawSecrets.length ? (
                <FoldGadget title="More">
                  <GadgetGroup>{rawSecrets.map(secretRow)}</GadgetGroup>
                </FoldGadget>
              ) : null}
            </div>
          </div>
        );
      }
      /* ── System: display + remote access + desk reset + one RAW (diagnostics, mesh, devices) ── */
      case "system": {
        const device = (data.device ?? {}) as Record<string, unknown>;
        const deviceCount = Object.keys(device).length;
        return <SystemModule
          grantAct={grantAct}
          receiptOpen={grantReceiptOpen}
          onGrantAct={(act) => { setGrantAct(act); setGrantReceiptOpen(false); }}
          hubSystem={hub.data.system}
          deviceName={str(["mesh", "device_name"], "Device name")}
          deskModule={<><DeskModule /><BuilderToolsModule
            checked={Boolean(val(["ui", "builder_tools"]) ?? false)}
            onChange={(next) => update(["ui", "builder_tools"], next)}
          /></>}
          rawWell={deviceCount ? (
            <GadgetGroup material="inset" label="Device">
              {walkerRows(device, ["device"])}
            </GadgetGroup>
          ) : null}
        />;
      }
      /* ── People: People MCP access (Conductor R7, canvas K7a) ── */
      case "people":
        return (
          <>
            {/* PHILO-15 B57: his name and the other names for him, after
                first run (the reopened You card shows them without an edit;
                Astra r1 on #1090: this is the place he looks). */}
            <SurfaceColumns variant="preferences" main={<OwnerNameGroup prefs={ownerPrefs} />} side={<PeopleAccessModule />} />
          </>
        );
      /* ── Agents: how many work at once (Betterment AG5) ── */
      case "agents":
        return (
          <GadgetGroup material="inset" label="Working at once">
            {num(["agents", "working_at_once"], "Working at once", { min: 1, max: 20, step: 1 })}
          </GadgetGroup>
        );
      default:
        return null;
    }
  };

  // You has its own owner writer and field receipts. A success from the
  // general preferences writer cannot acknowledge those independent edits.
  const receipt = { saving: saving || Boolean(secretBusy), writtenAt: moduleId === "you" ? "" : writtenAt, refusal };
  const focusHighlight = SETTINGS_FOCUS_PATHS[navigation.focus ?? ""] ?? navigation.focus ?? "";
  const pageSection = (id: SettingsSectionId, label: string, children: ReactNode) => (
    <PrefSection id={id} label={label} hidden={moduleId !== id} quiet={id === "you" || id === "agents"}>{children}</PrefSection>
  );
  const engineLink = (
    <GadgetGroup material="inset" label="HoldSpeak">
      <GadgetRow label="Engines" highlight={focusHighlight === "engines"}>
        <Button variant="secondary" dense onClick={() => openSurfaceOr("configure-runs-on", "/models")} data-testid="settings-engines-page-link">Engines ›</Button>
      </GadgetRow>
      <GadgetRow label="Setup" highlight={focusHighlight === "setup"}>
        <Button variant="secondary" dense onClick={() => openSurfaceOr("configure-setup", "/")} data-testid="settings-setup-page-link">Setup ›</Button>
      </GadgetRow>
    </GadgetGroup>
  );
  const railItems = SETTINGS_SECTIONS.map((section) => ({
    id: section.id,
    label: section.label,
    glyph: <SettingsRailGlyph section={section} />,
  }));
  const settingsPage = (
    <PrefWindow items={railItems} selected={moduleId} onSelect={(id) => openSection(id)} paneOpen={paneOpen} onBack={() => setPaneOpen(false)} frameBack testId="settings-page">
        {refusal && moduleId !== "you" ? <div className="pref-pane-alert"><SurfaceWell><div className="prefs-read-failure" role="alert" data-testid="settings-save-failure"><span>{refusal}</span>{failedChangesRef.current.length ? <Button dense variant="ghost" disabled={saving} onClick={() => void retryFailedChanges()}>Retry</Button> : null}</div></SurfaceWell></div> : null}
        {pageSection("you", "You", <OwnerNameGroup prefs={ownerPrefs} highlight={focusHighlight} />)}
        {pageSection("speak", "Speak", renderModule("voice"))}
        {pageSection("meetings", "Meetings", renderModule("meetings"))}
        {pageSection("notices", "Notices", renderModule("rhythm"))}
        {pageSection("accounts", "Accounts", renderModule("integrations"))}
        {pageSection("agents", "Agents", <>
          {renderModule("agents")}
          <GadgetGroup material="inset" label="Agents act">
            <GadgetRow label="Agents act" highlight={focusHighlight === "agents-act"}>
              <CycleGadget
                label="Agents act"
                value={String(hub.data.posture || authority.data.control_mode || "neutral")}
                disabled={authorityBusy || authority.loading || Boolean(authority.error)}
                options={CONTROL_MODES.map((mode) => ({ value: mode, label: controlModeLabel(mode) }))}
                onChange={(mode) => void setControlMode(mode)}
              />
            </GadgetRow>
          </GadgetGroup>
          <PeopleAccessModule highlight={focusHighlight} />
        </>)}
        {pageSection("desk", "Desk", <>
          {renderModule("sounds")}
          <WallpaperModule showFavorites highlight={focusHighlight} />
        </>)}
        {pageSection("this-mac", "This Mac", <>
          {engineLink}
          {renderModule("system")}
        </>)}
    </PrefWindow>
  );
  return (
    <>
      {hero ? hero(null) : null}
      <div ref={contentRef} className="settings-content settings-page-content" data-settings-view={moduleId || "page"}>
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <SurfaceState loading={hub.loading} error={hub.error} onRetry={() => void hub.reload()}>
          {settingsPage}
        </SurfaceState>
      </SurfaceState>
      </div>
      <PrefStatusBar
        receipt={receipt}
        save={moduleId === "you" ? ownerSaveState(ownerPrefs) : undefined}
        failureTestId={moduleId === "you" ? undefined : null}
        onRetry={moduleId === "you"
          ? (ownerPrefs.state === "Not saved" ? () => void ownerPrefs.owner.flush() : undefined)
          : (failedChangesRef.current.length ? () => void retryFailedChanges() : undefined)}
        idleReceipt={moduleId === "accounts" && connectionsFoot?.checkedAt ? <span data-testid="settings-checked">Checked {clockWord(connectionsFoot.checkedAt)}</span> : undefined}
        grantReceipt={grantAct ? (
          <GrantFootReceipt
            act={grantAct}
            open={grantReceiptOpen}
            onToggle={() => setGrantReceiptOpen((open) => !open)}
          />
        ) : null}
        hubWrittenAt={
          moduleId !== "you" && hub.data.writtenAt != null
            ? new Date(hub.data.writtenAt * 1000).toTimeString().slice(0, 5)
            : null
        }
      />
    </>
  );
}
