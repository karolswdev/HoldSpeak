// HS-95-07 / HS-111-01 — the Settings core, rethought as the OS's own
// Prefs program (the verified audit at .tmp/hs-111-01-audit.md §3):
// a drawer face of authored pref modules; a module swaps the WHOLE
// window body; the footer status bar carries the receipt and the
// refusals; every control is a gadget from the surface kit. The pane
// roster is a code constant — the wire never mints a pane again.
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
import { documentBuildId } from "../../lib/buildId";
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
  Receipt,
  countToken,
  humanTime,
  StateChip,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceWell,
} from "../../desk/surface";
import { SurfaceSection } from "../../desk/surface/Surface";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { egressFor } from "../../desk/surface/egress";
import { openSurface } from "../../desk/shell";
import { announceTaskReturn } from "../../desk/returnToTask";
import { HotkeyCapture } from "./settingsBespoke";
import { toggleSfx } from "../../lib/sfx";
// PARKED (HS-170-03): ModelsModule retired — the Concierge is its own window now.
// import { ModelsModule } from "./settingsModels";
import { TtsSettingsBlock } from "./settingsTts";
// PARKED (HS-170-03): CapabilityAssignmentsCore — reached via Concierge Adjust.
// import { CapabilityAssignmentsCore } from "./CapabilityAssignmentsCore";
import { WallpaperModule } from "./settingsWallpaper";
import { RuntimeDocsCore } from "./RuntimeDocsCore";
import { useCoreWings } from "./core-hooks";
import { ConnectionsPane, type ConnectionsFoot } from "./connections";
// HS-139-05: activateLauncher removed (Delivery tile absorbed).
import {
  CADENCE_PRESSURE_OPTIONS,
  INTELLIGENCE_AUTO_OPTIONS,
  LANGUAGE_OPTIONS,
  DeskModule,
  MIR_PROFILE_OPTIONS,
  MODULE_ALIASES,
  PREF_MODULES,
  PrefsFace,
  PrefStatusBar,
  WAKE_ACTION_OPTIONS,
  autoDisplayFact,
  type SettingsHubWire,
} from "./settingsPrefs";

const SECRET_LABELS: Record<string, string> = {
  web_token: "Web pairing token",
  device_psk: "Device audio key",
  telegram_bot_token: "Telegram bot token",
  telegram_pairing_code: "Telegram pairing code",
  failure_webhook_url: "Failure alert webhook",
  failure_webhook_credential: "Failure alert credential",
  slack_webhook_url: "Slack webhook",
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
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** HS-175 counsel C10 -- the chip beside ``Snapshot``: the resolved
 * vision host (LAN / cloud / paired device) or THIS DEVICE when the model
 * runs here.  ``null`` when no vision model resolves (nothing can leave
 * and the upload refuses by name) -- absence is the signal. */
export function snapshotEgressChip(
  egress: { scope?: string; host?: string | null } | null | undefined,
): { label: string; scope: "local" | "cloud" | "mixed"; title: string } | null {
  if (!egress || !egress.scope) return null;
  if (egress.scope === "local") {
    return { label: "THIS DEVICE", scope: "local", title: "The screenshot is read by a vision model on this device." };
  }
  const host = (egress.host || "").trim();
  if (!host) return null;
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
  profile_id: "Runs on",
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

const SETTINGS_WINGS = [
  { id: "settings", label: "Settings" },
  { id: "guide", label: "Guide" },
];

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

type RemoteWire = {
  enabled: boolean;
  bind_host: string | null;
  port: number | null;
  credentials: (RemoteCredential & { delegation?: Delegation | null })[];
  /** Grants LIVE in storage whose identity has no credential row. */
  delegations?: OrphanDelegation[];
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

/** The kernel's refusal codes (verbatim) and their plain face tokens; the
 *  code rides `data-code` for the fence. */
export const GRANT_REFUSAL_TOKEN: Record<string, string> = {
  owner_principal_required: "OWNER ONLY",
  desk_delegation_required: "NO GRANT",
  desk_delegation_revoked: "GRANT STOPPED",
  desk_delegation_expired: "GRANT EXPIRED",
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
};

function receiptClock(createdAt: unknown): { time: string; date: string } {
  const seconds = typeof createdAt === "number" ? createdAt : Date.now() / 1000;
  const d = new Date(seconds * 1000);
  return { time: d.toTimeString().slice(0, 5), date: formatExpiry(seconds) };
}

function grantActFrom(
  body: unknown, outcome: GrantAct["outcome"], verb: GrantVerbKind, identity: string, code?: string,
): GrantAct | null {
  const record = (body && typeof body === "object" ? body : {}) as Record<string, unknown>;
  const receipt = (record.receipt && typeof record.receipt === "object" ? record.receipt : {}) as Record<string, unknown>;
  const operationId = String(record.operation_id ?? receipt.operation_id ?? "");
  if (!operationId) return null;
  return { operation_id: operationId, outcome, verb, code, identity, ...receiptClock(receipt.created_at) };
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
            ? (act.verb === "stop" ? GRANT_WORDS.stopped : GRANT_WORDS.live)
            : (act.verb === "stop" ? GRANT_WORDS.actStop : GRANT_WORDS.actAllow)}
        </span>
        {!ok && act.code ? (
          <span className="surface-token" data-chip>{GRANT_REFUSAL_TOKEN[act.code] ?? act.code}</span>
        ) : null}
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

export function RuntimeIdentityModule() {
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

  if (error) {
    return (
      <GadgetGroup label="Runtime">
        <GadgetRow label="Runtime">
          <StateChip state="failure" label="UNREADABLE" />
        </GadgetRow>
      </GadgetGroup>
    );
  }
  if (!wire) return null;

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
    <GadgetGroup label="Runtime">
      {tokens.length ? (
        <div className="prefs-hub-chips" data-testid="runtime-repair">
          {tokens.map((token) => (
            <StateChip key={token} state="warning" label={token} />
          ))}
        </div>
      ) : null}
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
      <FoldGadget title="RAW" token={tokens.length ? String(tokens.length) : undefined}>
        <GadgetGroup label="Diagnostics">
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
      </FoldGadget>
    </GadgetGroup>
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
  const [remoteOn, setRemoteOn] = useState(hubSystem.remote ?? false);
  return (
    <>
      <div className="surface-display" data-testid="system-display">
        This device
      </div>
      <div className="prefs-hub-chips" data-testid="system-hub-chips">
        <span className="surface-token" data-chip>{hubSystem.host}</span>
        <span className="surface-token" data-chip>{hubSystem.mesh ? "MESH ON" : "MESH OFF"}</span>
        {remoteOn
          ? <StateChip state="success" label="REMOTE ON" />
          : <span className="surface-token" data-chip>REMOTE OFF</span>}
      </div>
      <div className="prefs-rule" aria-hidden="true" />
      <RuntimeIdentityModule />
      <GadgetGroup label="Mesh">
        {deviceName}
      </GadgetGroup>
      <RemoteAccessModule
        onEnabledChange={setRemoteOn}
        grantAct={grantAct}
        receiptOpen={receiptOpen}
        onGrantAct={onGrantAct}
      />
      {deskModule}
      {rawWell}
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
  const [error, setError] = useState("");
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

  const fetchRemote = useCallback(async () => {
    try {
      const data = await apiFetch<RemoteWire>("/api/settings/remote");
      setWire(data);
      setError("");
      onEnabledChange?.(data.enabled);
    } catch (err) {
      setError(readableError(err));
    } finally {
      setLoading(false);
    }
  }, [onEnabledChange]);

  useEffect(() => { void fetchRemote(); }, [fetchRemote]);

  const toggleEnabled = async (next: string) => {
    const enabled = next === "ON";
    setToggleBusy(true);
    try {
      await apiFetch("/api/settings/remote", {
        method: "PUT",
        json: { enabled },
      });
      await fetchRemote();
    } catch (err) {
      setError(readableError(err));
    } finally {
      setToggleBusy(false);
    }
  };

  const issueCredential = async () => {
    if (!issueName.trim()) return;
    setIssuing(true);
    setError("");
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
          identity: issueName.trim(),
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
      setError(readableError(err));
    } finally {
      setIssuing(false);
    }
  };

  /** PHILO-7-02: Allow / Stop filing -- delegation.grant / delegation.revoke. */
  const setGrant = async (identity: string, verb: GrantVerbKind) => {
    setGranting(identity);
    setError("");
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
        setError(readableError(err));
      }
    } finally {
      setGranting(null);
      await fetchRemote();
    }
  };

  const revokeCredential = async (id: string, identity: string) => {
    setRevoking(id);
    setError("");
    try {
      const result = await apiFetch<Record<string, unknown>>(`/api/settings/remote/credentials/${id}`, {
        method: "DELETE",
      });
      // Durable first: the credential's LIVE grant was revoked BEFORE the
      // credential, with its own receipt (credential_revoked).
      if (result?.grant_revoked) {
        const act = grantActFrom(result, "succeeded", "stop", identity);
        if (act) onGrantAct?.(act);
      }
      await fetchRemote();
    } catch (err) {
      setError(readableError(err));
    } finally {
      setRevoking(null);
    }
  };

  const copyToken = () => {
    if (oneTimeToken) {
      void navigator.clipboard.writeText(oneTimeToken);
    }
  };

  if (loading) return null;

  const enabled = wire?.enabled ?? false;
  const allCredentials = wire?.credentials ?? [];
  // PHILO-7-02: a grant is authority, whatever the transport switch says.
  // ON: every credential row. OFF: the credential rows whose effective grant
  // is LIVE. Always: every grant row with no credential.
  const credentials = enabled
    ? allCredentials
    : allCredentials.filter((c) => c.delegation?.state === "LIVE");
  const delegations = wire?.delegations ?? [];
  const activeCount = credentials.filter((c) => c.active).length;
  const totalCount = allCredentials.length;
  const addressToken = enabled && wire?.port
    ? `${wire.bind_host || "0.0.0.0"}:${wire.port}`
    : null;

  return (
    <GadgetGroup label="Remote access">
      {/* The toggle row */}
      <GadgetRow label="Streamable HTTP">
        <CycleGadget
          label="Remote transport"
          value={enabled ? "ON" : "OFF"}
          options={[{ value: "OFF" }, { value: "ON" }]}
          disabled={toggleBusy}
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
      {credentials.length > 0 || delegations.length > 0 ? (
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
          {credentials.map((cred) => (
            <SurfaceLedgerRow
              key={cred.id}
              lead={<StateChip state={cred.active ? "success" : "idle"} label="" icon="●" />}
              primary={cred.identity}
              expands={false}
              data-testid={`credential-row-${cred.id}`}
              cells={<>
                <GrantChip grant={cred.delegation} />
                <GrantRefusalChip refusal={refusals[cred.identity]} />
                <span className="surface-token" data-chip>{paletteLabel(cred.palette)}</span>
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
                <Button
                  variant="ghost"
                  dense
                  disabled={granting === cred.identity}
                  onClick={() => void setGrant(cred.identity, cred.delegation?.state === "LIVE" ? "stop" : "allow")}
                  data-testid="grant-verb"
                >
                  {cred.delegation?.state === "LIVE" ? GRANT_WORDS.stop : GRANT_WORDS.allow}
                </Button>
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
            />
          ))}
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
              <GadgetRow label="Name">
                <StringGadget
                  label="Credential name"
                  value={issueName}
                  placeholder="e.g. sweep-runner"
                  onChange={setIssueName}
                  autoFocus
                />
              </GadgetRow>
              <GadgetRow label="Palette">
                <CycleGadget
                  label="Palette"
                  value={issuePalette}
                  options={PALETTE_OPTIONS}
                  onChange={setIssuePalette}
                />
              </GadgetRow>
              <GadgetRow label="TTL">
                <CycleGadget
                  label="TTL"
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
          ) : (
            <div className="prefs-issue-start">
              <Button
                variant="ghost"
                onClick={() => { setOneTimeToken(null); setIssueOpen(true); }}
                data-testid="issue-credential-btn"
              >
                Issue credential
              </Button>
            </div>
          )}
        </>
      ) : null}

      {error ? (
        <span className="gadget-fact" data-tone="danger" role="alert" data-testid="remote-error">
          {error}
        </span>
      ) : null}
    </GadgetGroup>
  );
}

export function SettingsCore({ hero, scope }: CoreProps) {
  // HS-100-10 — the Runtime guide is the Guide wing (the standalone
  // doc-window died; deep links land here via the registry alias).
  const wings = useCoreWings(
    SETTINGS_WINGS,
    scope === "guide" ? "guide" : "settings",
  );
  if (wings.view === "guide") return <RuntimeDocsCore />;
  return <SettingsFace hero={hero} scope={scope} />;
}

function SettingsFace({ hero, scope }: CoreProps) {
  const integrationSubject =
    scope && scope.startsWith("integration:")
      ? scope.slice("integration:".length)
      : null;
  // HS-139-05: resolve aliases from the retired roster to its successor.
  const resolvedScope = scope ? (MODULE_ALIASES[scope] ?? scope) : scope;
  const scopedModule = PREF_MODULES.some(
    (module) => module.id === resolvedScope,
  )
    ? (resolvedScope ?? null)
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
  const [moduleId, setModuleId] = useState<string | null>(
    integrationSubject ? "integrations" : scopedModule,
  );
  const [highlight, setHighlight] = useState("");
  const [saving, setSaving] = useState(false);
  const [writtenAt, setWrittenAt] = useState("");
  const [refusal, setRefusal] = useState("");
  const [secretBusy, setSecretBusy] = useState("");
  // HS-168-03: connections receipt for the integrations module footer.
  const [connectionsFoot, setConnectionsFoot] = useState<ConnectionsFoot | null>(null);
  const handleConnectionsFooter = useCallback((foot: ConnectionsFoot) => {
    setConnectionsFoot(foot);
  }, []);
  const [authorityBusy, setAuthorityBusy] = useState(false);
  const secrets = (resource.data._secrets ?? {}) as Record<string, SecretState>;

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
  const [calWellError, setCalWellError] = useState("");
  const [calWellSaving, setCalWellSaving] = useState(false);
  // The in-world Remove confirm step (never a modal): the armed source id.
  const [calRemoveFor, setCalRemoveFor] = useState<string | null>(null);
  const loadCalSources = useCallback(() => {
    void apiFetch<typeof calSources>("/api/calendar/sources").then(setCalSources);
  }, []);
  useEffect(() => { loadCalSources(); }, [loadCalSources]);

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
  const repaintPending = () => {
    const visible = projectPendingSettingsChanges(
      authoritativeBaseRef.current,
      [
        ...pendingJobsRef.current.map((pending) => pending.changes),
        debouncedChangesRef.current,
      ],
    );
    resource.setData(visible);
  };
  useEffect(() => {
    if (pendingJobsRef.current.length || debouncedChangesRef.current.length)
      return;
    authoritativeBaseRef.current = resource.data;
    revisionRef.current = resource.data._revision;
  }, [resource.data]);
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
        authoritativeBaseRef.current,
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
      const authoritative = result.settings ?? payload;
      authoritativeBaseRef.current = authoritative as SettingsResponse;
      revisionRef.current = authoritative._revision as string | undefined;
      removePendingJob(job.id);
      repaintPending();
      // The readiness signal AND the focus return, in one call: a face
      // holding an unfinished task re-reads without a reload, and the verb
      // the owner left gets focus back (design D2(a) "Focus return").
      announceTaskReturn(from);
      setWrittenAt(new Date().toTimeString().slice(0, 8));
      return true;
    } catch (error) {
      setRefusal(readableError(error));
      writerFencedRef.current = true;
      removePendingJob(job.id);
      try {
        await readAuthoritativeBase();
      } catch {
        // A later queued job must reconcile before it can write.
      }
      repaintPending();
      return false;
    } finally {
      setSaving(false);
    }
  };
  const save = (changes: Array<[string[], unknown]>): Promise<boolean> => {
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
    setRefusal("");
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      const pending = debouncedChangesRef.current;
      debouncedChangesRef.current = [];
      if (pending.length) void save(pending);
    }, 700);
  };
  const update = (path: string[], next: unknown) => updateMany([[path, next]]);
  const commitMany = async (changes: Array<[string[], unknown]>) => {
    installSettingsChanges(resource.data, changes, resource.setData);
    setRefusal("");
    clearTimeout(saveTimer.current);
    const pending = [...debouncedChangesRef.current, ...changes];
    debouncedChangesRef.current = [];
    return save(pending);
  };
  const reconcileSettings = async () => {
    const reconcile = async () => {
      try {
        await readAuthoritativeBase();
        repaintPending();
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

  const changeSecret = async (
    secretId: string,
    action: "replace" | "rotate" | "delete",
    value?: string,
  ) => {
    setSecretBusy(secretId);
    setRefusal("");
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
      await resource.reload();
      setWrittenAt(new Date().toTimeString().slice(0, 8));
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setSecretBusy("");
    }
  };

  const setControlMode = async (controlMode: string) => {
    setAuthorityBusy(true);
    setRefusal("");
    try {
      const result = await apiFetch<Record<string, unknown>>(
        "/api/authority/control-mode",
        {
          method: "PUT",
          json: { control_mode: controlMode },
        },
      );
      authority.setData({ ...authority.data, ...result });
      setWrittenAt(new Date().toTimeString().slice(0, 8));
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setAuthorityBusy(false);
    }
  };

  // A scope names the focused module. Integration links retain their
  // subject alias while the palette can address every module directly.
  // HS-139-05: aliases from the retired 14-tile roster land here too.
  useEffect(() => {
    if (integrationSubject) setModuleId("integrations");
    else if (scopedModule) setModuleId(scopedModule);
  }, [integrationSubject, scopedModule]);

  // HS-139-05: deep-index and filter removed — all tiles stay visible at once.
  const openModule = (id: string) => {
    setModuleId(id);
    setHighlight("");
  };

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
  const hl = (path: string[]) => highlight === path.join(".");
  const check = (path: string[], label: string, fact?: string) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={fact}
      highlight={hl(path)}
    >
      <CheckGadget
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
    <GadgetRow key={path.join(".")} label={label} highlight={hl(path)}>
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
          <GadgetGroup key={nextPath.join(".")} label={title(key)}>
            {walkerRows(item as Record<string, unknown>, nextPath)}
          </GadgetGroup>
        );
      if (typeof item === "boolean") return check(nextPath, title(key));
      if (typeof item === "number") return num(nextPath, title(key));
      if (Array.isArray(item)) return csv(nextPath, title(key));
      return str(nextPath, title(key));
    });

  /* ── the authored owner-facing modules ── */
  const renderModule = (id: string): ReactNode => {
    const data = resource.data;
    switch (id) {
      /* ── Voice: hotkey + language + voice typing + wake word ── */
      case "voice": {
        const symbols = (val(["dictation", "spoken_symbols"]) ?? []) as Array<{
          spoken?: string;
          symbol?: string;
          attach?: string;
        }>;
        const symbolsPath = ["dictation", "spoken_symbols"];
        const patchSymbol = (index: number, patch: Record<string, string>) =>
          update(
            symbolsPath,
            symbols.map((entry, row) =>
              row === index ? { ...entry, ...patch } : entry,
            ),
          );
        const macroItems = (val(["dictation", "macros", "items"]) ??
          []) as unknown[];
        return (
          <>
            <HotkeyCapture
              value={(data.hotkey ?? {}) as Record<string, unknown>}
              onCommit={(next) =>
                update(["hotkey"], {
                  ...(data.hotkey as Record<string, unknown>),
                  ...next,
                })
              }
              onRefuse={setRefusal}
            />
            <GadgetGroup label="Transcription">
              {cyc(["model", "language"], "Language", LANGUAGE_OPTIONS)}
            </GadgetGroup>
            <GadgetGroup label="Typing">
              {check(
                ["dictation", "preview_before_type"],
                "Preview before type",
              )}
              {check(
                ["dictation", "macros", "enabled"],
                "Voice commands",
                countToken(macroItems.length, "CONFIGURED") ?? undefined,
              )}
            </GadgetGroup>
            <GadgetGroup label="Spoken symbols">
              <GadgetRow wide label="Dictionary" highlight={hl(symbolsPath)}>
                <GadgetTable
                  head={["SPOKEN", "SYMBOL", "ATTACH"]}
                  deleteLabel="FORGET?"
                  onDelete={(index) =>
                    update(
                      symbolsPath,
                      symbols.filter((_, row) => row !== index),
                    )
                  }
                  onAdd={() =>
                    update(symbolsPath, [
                      ...symbols,
                      { spoken: "", symbol: "", attach: "none" },
                    ])
                  }
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
              </GadgetRow>
            </GadgetGroup>
            <GadgetGroup label="Wake word">
              {check(
                ["wake_word", "enabled"],
                "Enabled",
                "models download once",
              )}
              {cyc(
                ["wake_word", "action"],
                "Action",
                WAKE_ACTION_OPTIONS,
                "type lands in the focused app",
              )}
            </GadgetGroup>
            {/* HS-139-04/05: all voice RAW wells merged. */}
            <FoldGadget title="RAW" token="10">
              <GadgetGroup label="Transcription">
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
              <GadgetGroup label="Pipeline">
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
              <GadgetGroup label="Wake word">
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
          <>
            <GadgetGroup label="Sounds">
              <GadgetRow
                label="DESK SOUNDS"
                highlight={hl(["ui", "desk_sounds"])}
              >
                <CheckGadget
                  label="DESK SOUNDS"
                  checked={Boolean(val(["ui", "desk_sounds"]) ?? true)}
                  onChange={(next) => {
                    update(["ui", "desk_sounds"], next);
                    toggleSfx(next);
                  }}
                />
              </GadgetRow>
            </GadgetGroup>
            <GadgetGroup label="Presence">
              {check(["presence", "enabled"], "Presence")}
              {check(["presence", "mascot"], "Mascot")}
            </GadgetGroup>
            <TtsSettingsBlock />
          </>
        );
      case "wallpaper":
        return <WallpaperModule />;
      /* ── Meetings: display fact + intel row + capture + calendar + actuators + RAW ── */
      case "meetings": {
        const autoVal = String(val(["meeting", "intelligence_auto"]) ?? "room_linked");
        const meetingsHub = (hub.data as Record<string, unknown>).meetings as Record<string, unknown> | undefined;
        // HS-172: null host = no model assigned; real host = chip.
        // The hub returns a host only when a model is actually assigned;
        // until the wire fix lands, fall back to defaultSet as the signal.
        const hubHost = meetingsHub?.host ? String(meetingsHub.host) : null;
        const hasModel = Boolean(hubHost) && hubHost !== "THIS DEVICE"
          ? true
          : Boolean(hub.data.models?.defaultSet);
        const intelHost = hasModel ? hubHost : null;
        const lastRunAt = meetingsHub?.lastRunAt ? String(meetingsHub.lastRunAt) : null;
        const lastRunS = meetingsHub?.lastRunS != null ? Number(meetingsHub.lastRunS) : null;
        const lastRunReceipt = lastRunAt
          ? `LAST RAN ${lastRunAt.slice(11, 16)}${lastRunS != null ? " · " + lastRunS + " S" : ""}`
          : null;
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
        const calSourceLabel = (entry: { label: string; url: string }, host: string | null) =>
          entry.label || host || (entry.url.split(/[\\/]/).pop() ?? "") || "CALENDAR";
        const openCalWell = (target: string, prefill: string) => {
          setCalRemoveFor(null);
          setCalWellFor(target);
          setCalWellValue(prefill);
          setCalWellError("");
        };
        const closeCalWell = () => {
          setCalWellFor(null);
          setCalWellValue("");
          setCalWellError("");
        };
        const saveCalWell = async () => {
          const url = calWellValue.trim();
          if (!url || calWellFor === null) return;
          setCalWellSaving(true);
          setCalWellError("");
          const nextSources =
            calWellFor === "new"
              ? [...sources, { id: crypto.randomUUID(), label: "", url, enabled: true }]
              : sources.map((s) => (s.id === calWellFor ? { ...s, url } : s));
          const ok = await commitMany([[sourcesPath, nextSources]]);
          setCalWellSaving(false);
          if (ok) {
            closeCalWell();
            setTimeout(loadCalSources, 300);
          } else {
            setCalWellError("REFUSED");
          }
        };
        const calWell = (
          <div className="prefs-calendar-well" data-testid="calendar-well">
            <StringGadget
              label="Calendar URL or file path"
              value={calWellValue}
              placeholder="Paste an ICS URL or a file path"
              onChange={setCalWellValue}
              mic
            />
            {calWellError ? <StateChip state="failure" label={refusal || calWellError} /> : null}
            <div className="prefs-calendar-well-actions">
              <Button variant="ghost" dense onClick={closeCalWell}>Cancel</Button>
              <Button dense disabled={calWellSaving || !calWellValue.trim()} onClick={() => void saveCalWell()}>Save</Button>
            </div>
          </div>
        );
        return (
          <>
            <div className="surface-display" data-testid="meetings-auto-display">
              {autoDisplayFact(autoVal)}
            </div>
            <div className="prefs-rule" aria-hidden="true" />
            {/* HS-202-04 (F06): the registry's word for a meeting's result
                is Summary on every face (`docs/product-language.json:23`);
                `intelligence` stays the wire key underneath. */}
            <GadgetRow label="Summary">
              <CycleGadget
                label="Auto-run the summary"
                value={autoVal}
                options={INTELLIGENCE_AUTO_OPTIONS}
                onChange={(next) => update(["meeting", "intelligence_auto"], next)}
              />
              {hasModel && intelHost ? (
                <EgressChip
                  label={egressFor(intelHost).label}
                  scope={egressFor(intelHost).scope}
                />
              ) : !hasModel ? (
                <>
                  <StateChip state="warning" label="NO MODEL" data-testid="settings-no-model" />
                  <Button variant="ghost" dense onClick={() => openSurface("open-concierge")} data-testid="settings-choose-model">
                    Choose model
                  </Button>
                </>
              ) : null}
              {lastRunReceipt ? (
                <span className="gadget-fact" data-testid="settings-last-ran">{lastRunReceipt}</span>
              ) : null}
            </GadgetRow>
            <div className="prefs-rule" aria-hidden="true" />
            <GadgetGroup label="Capture + export">
              <GadgetRow label="Mic device" fact="device name">
                <StringGadget
                  label="Mic device"
                  value={String(val(["meeting", "mic_device"]) ?? "")}
                  onChange={(next) => update(["meeting", "mic_device"], next || null)}
                />
              </GadgetRow>
              <GadgetRow label="System audio" fact="device name">
                <StringGadget
                  label="System audio device"
                  value={String(val(["meeting", "system_audio_device"]) ?? "")}
                  onChange={(next) => update(["meeting", "system_audio_device"], next || null)}
                />
              </GadgetRow>
              <GadgetRow label="Auto export">
                <CheckGadget
                  label="Auto export"
                  checked={Boolean(val(["meeting", "auto_export"]))}
                  onChange={(next) => update(["meeting", "auto_export"], next)}
                />
              </GadgetRow>
              <GadgetRow label="Format">
                <CycleGadget
                  label="Export format"
                  value={String(val(["meeting", "export_format"]) ?? "txt")}
                  options={[
                    { value: "txt", label: "TXT" },
                    { value: "markdown", label: "MD" },
                    { value: "json", label: "JSON" },
                    { value: "srt", label: "SRT" },
                  ]}
                  onChange={(next) => update(["meeting", "export_format"], next)}
                />
              </GadgetRow>
            </GadgetGroup>
            {/* HS-175-03: CALENDAR section replaces the 146 Calendar GadgetGroup.
                Source rows, the Connect calendar well, Auto-record, Snapshot. */}
            <SurfaceSection label="CALENDAR" className="prefs-calendar-section">
              <ul className="surface-rows prefs-calendar-sources">
                {sources.map((entry, index) => {
                  const fact = calFacts.get(entry.id);
                  const stat = calStats.get(entry.id);
                  const host = fact?.egress && fact.host ? String(fact.host) : null;
                  const label = calSourceLabel(entry, host);
                  const type = label.toUpperCase().endsWith("SNAPSHOT") ? "SNAPSHOT" : "ICS";
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
                          <span className="surface-token" data-chip>{type}</span>
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
                          {type !== "SNAPSHOT" ? (
                            <Button variant="ghost" dense data-testid="calendar-source-edit" onClick={(e) => { e.stopPropagation(); openCalWell(entry.id, entry.url); }}>Edit</Button>
                          ) : null}
                          <Button variant="ghost" dense data-testid="calendar-source-toggle" onClick={(e) => { e.stopPropagation(); patchSource(index, { enabled: !entry.enabled }); }}>{entry.enabled ? "Disable" : "Enable"}</Button>
                          <Button variant="ghost" dense data-testid="calendar-source-remove" onClick={(e) => { e.stopPropagation(); closeCalWell(); setCalRemoveFor(entry.id); }}>Remove</Button>
                        </>
                      }
                      open={editing || removing}
                      onToggle={() => {
                        if (type === "SNAPSHOT") { if (editing) closeCalWell(); return; }
                        if (editing) closeCalWell(); else openCalWell(entry.id, entry.url);
                      }}
                    >
                      {editing ? calWell : null}
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
                {/* Connect calendar row + the same in-world well (the "new" use) */}
                <SurfaceLedgerRow
                  data-testid="calendar-connect-row"
                  lead={<span />}
                  primary="Connect calendar"
                  wrap
                  trailing={
                    calWellFor !== "new" ? (
                      <>
                        <Button variant="ghost" onClick={(e) => { e.stopPropagation(); openCalWell("new", ""); }} data-testid="calendar-add-btn">Add</Button>
                        {/* HS-175 counsel C10: the vision model's egress on the face
                            BEFORE the upload (Article III:2, A.9) -- read from the
                            same resolution the dispatch uses. */}
                        {(() => {
                          const chip = snapshotEgressChip(calSources?.snapshot_egress);
                          return chip ? (
                            <span data-testid="calendar-snapshot-egress" style={{ display: "inline-flex", alignItems: "center" }}>
                              <EgressChip label={chip.label} scope={chip.scope} title={chip.title} className="prefs-snapshot-egress" />
                            </span>
                          ) : null;
                        })()}
                        <Button variant="ghost" dense data-testid="calendar-snapshot-btn" onClick={(e) => {
                          e.stopPropagation();
                          const input = document.createElement("input");
                          input.type = "file";
                          input.accept = ".png,.jpg,.jpeg,.webp";
                          input.multiple = true;
                          input.onchange = async () => {
                            const files = input.files;
                            if (!files?.length) return;
                            const fd = new FormData();
                            for (let i = 0; i < Math.min(files.length, 3); i++) fd.append("files", files[i]);
                            try {
                              const result = await apiFetch<Record<string, unknown>>("/api/calendar/snapshot", { method: "POST", body: fd });
                              openSurface("review-calendar-snapshot", JSON.stringify(result));
                            } catch (error) { setRefusal(readableError(error)); }
                          };
                          input.click();
                        }}>Snapshot</Button>
                      </>
                    ) : null
                  }
                  open={calWellFor === "new"}
                  onToggle={() => (calWellFor === "new" ? closeCalWell() : openCalWell("new", ""))}
                >
                  {calWellFor === "new" ? calWell : null}
                </SurfaceLedgerRow>
                {/* Auto-record row */}
                <SurfaceLedgerRow
                  data-testid="settings-auto-record"
                  lead={<span />}
                  primary="Auto-record"
                  wrap
                  cells={
                    <span style={{ display: "inline-flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                      <CycleGadget
                        label="Auto-record mode"
                        value={calSources?.auto_record ?? String(val(["meeting", "auto_record"]) ?? "off")}
                        options={[
                          { value: "all_calendar", label: "ARM ALL CALENDAR MEETINGS" },
                          { value: "room_linked", label: "ARM ROOM MEETINGS ONLY" },
                          { value: "off", label: "OFF" },
                        ]}
                        onChange={(next) => { update(["meeting", "auto_record"], next); setTimeout(loadCalSources, 900); }}
                      />
                      {(calSources?.auto_record ?? String(val(["meeting", "auto_record"]) ?? "off")) !== "off" ? (
                        <span className="surface-token" data-chip data-tone="muted">{calSources?.auto_record_lead_minutes ?? 5} MIN BEFORE</span>
                      ) : null}
                      {(calSources?.auto_record ?? String(val(["meeting", "auto_record"]) ?? "off")) === "room_linked" ? (() => {
                        const mt = calSources ? countToken(calSources.matched_this_week, "MATCHED THIS WEEK") : null;
                        return mt ? <span className="surface-token" data-chip data-testid="matched-this-week">{mt}</span> : null;
                      })() : null}
                    </span>
                  }
                  expands={false}
                />
              </ul>
            </SurfaceSection>
            <GadgetGroup label="Actuators">
              {check(["meeting", "allow_actuators"], "Allow actuators")}
            </GadgetGroup>
            {/* HS-139-04: all operator knobs fold behind one RAW well. */}
            <FoldGadget title="RAW" token="20">
              <GadgetGroup label="Capture">
                {check(["meeting", "diarization_enabled"], "Diarization")}
                {check(["meeting", "diarize_mic"], "Diarize mic")}
                {prop(["meeting", "similarity_threshold"], "Similarity", {
                  min: 0,
                  max: 1,
                  step: 0.05,
                })}
              </GadgetGroup>
              {/* HS-202-04 (F06): same rule, the advanced sheet. */}
              <GadgetGroup label="Summary">
                {check(["meeting", "intel_cloud_store"], "Cloud store")}
              </GadgetGroup>
              <GadgetGroup label="Deferred queue">
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
                    min: 0,
                  },
                )}
                {str(
                  ["meeting", "intel_retry_failure_webhook_header_name"],
                  "Webhook header",
                )}
              </GadgetGroup>
              <GadgetGroup label="Routing">
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
              <GadgetGroup label="Actuators">
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
            <GadgetGroup label="Cadence">
              {check(["cadence", "enabled"], "Enabled")}
              {cyc(
                ["cadence", "pressure"],
                "Pressure",
                CADENCE_PRESSURE_OPTIONS,
              )}
              {num(["cadence", "quiet_hours_start"], "Quiet from", {
                unit: "h",
                min: 0,
                max: 23,
              })}
              {num(["cadence", "quiet_hours_end"], "Quiet until", {
                unit: "h",
                min: 0,
                max: 23,
              })}
              {num(["cadence", "max_nudges_per_day"], "Max nudges", {
                unit: "/day",
                min: 0,
              })}
            </GadgetGroup>
            <GadgetGroup label="Telegram">
              {check(["cadence_telegram", "enabled"], "Enabled")}
            </GadgetGroup>
            {/* HS-139-04: operator knobs fold behind RAW. */}
            <FoldGadget title="RAW" token="3">
              <GadgetGroup>
                {check(["cadence", "use_llm"], "Use LLM")}
                {num(["cadence", "tick_interval_seconds"], "Tick interval", {
                  unit: "s",
                  min: 30,
                  step: 30,
                })}
                {csv(["cadence_telegram", "allowed_chat_ids"], "Allowed chats")}
              </GadgetGroup>
            </FoldGadget>
          </>
        );
      /* ── Models: PARKED (HS-170-03) — the Concierge is its own window now.
         Opening models/assignments redirects to the Concierge surface. ── */
      case "models":
      case "assignments": {
        import("../../desk/shell").then(({ openSurface }) => {
          openSurface("open-concierge");
        });
        return null;
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
          <>
            {/* HS-168-03: the Connections face above credentials + mesh. */}
            <ConnectionsPane
              onFooterUpdate={handleConnectionsFooter}
              onOpenModule={openModule}
            />
            <GadgetGroup label="Credentials">
              <div className="prefs-egress-line">
                <EgressChip />
                <span className="gadget-fact">values stay on this hub</span>
              </div>
              {keepSecrets.map(secretRow)}
            </GadgetGroup>
            {/* HS-139-04: operator-wiring secrets fold behind RAW. */}
            {rawSecrets.length ? (
              <FoldGadget title="RAW" token={String(rawSecrets.length)}>
                <GadgetGroup>{rawSecrets.map(secretRow)}</GadgetGroup>
              </FoldGadget>
            ) : null}
          </>
        );
      }
      /* ── System: display + device name + remote access + desk reset + devices RAW ── */
      case "system": {
        const device = (data.device ?? {}) as Record<string, unknown>;
        const deviceCount = Object.keys(device).length;
        return <SystemModule
          grantAct={grantAct}
          receiptOpen={grantReceiptOpen}
          onGrantAct={(act) => { setGrantAct(act); setGrantReceiptOpen(false); }}
          hubSystem={hub.data.system}
          deviceName={str(["mesh", "device_name"], "Device name")}
          deskModule={<DeskModule />}
          rawWell={deviceCount ? (
            <FoldGadget title="RAW" token={String(deviceCount)}>
              <GadgetGroup label="Device">
                {walkerRows(device, ["device"])}
              </GadgetGroup>
            </FoldGadget>
          ) : null}
        />;
      }
      default:
        return null;
    }
  };

  const module = moduleId
    ? PREF_MODULES.find((entry) => entry.id === moduleId)
    : null;
  const receipt = { saving, writtenAt, refusal };
  return (
    <>
      {hero ? hero(null) : null}
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        {module ? (
          <div className="prefs-module">
            <h2 className="gadget-pane-title">{module.label}</h2>
            {renderModule(module.id)}
          </div>
        ) : (
          <PrefsFace
            onOpen={openModule}
            hub={hub.data}
            posture={String(hub.data.posture || authority.data.control_mode || "neutral")}
            postureBusy={authorityBusy || authority.loading}
            onPosture={(mode) => void setControlMode(mode)}
            precedence={
              Array.isArray(authority.data.precedence)
                ? (authority.data.precedence as string[])
                : []
            }
          />
        )}
      </SurfaceState>
      {/* HS-168-03: connections module shows its own receipt footer. */}
      {moduleId === "integrations" ? (
        <SurfaceFooter verbs={<>
          <EgressChip
            label={connectionsFoot?.egressHost ? connectionsFoot.egressHost.toUpperCase() : undefined}
            scope={connectionsFoot?.egressHost ? "cloud" : "local"}
          />
          {connectionsFoot?.checkedAt ? (
            <Receipt status="ok" label="Checked" timestamp={connectionsFoot.checkedAt} />
          ) : (
            <span className="prefs-receipt">NOT CHECKED</span>
          )}
        </>} />
      ) : (
        <PrefStatusBar
          onBack={
            module
              ? () => {
                  setModuleId(null);
                  setHighlight("");
                }
              : undefined
          }
          receipt={receipt}
          grantReceipt={module?.id === "system" && grantAct ? (
            <GrantFootReceipt
              act={grantAct}
              open={grantReceiptOpen}
              onToggle={() => setGrantReceiptOpen((open) => !open)}
            />
          ) : null}
          hubWrittenAt={
            hub.data.writtenAt != null
              ? new Date(hub.data.writtenAt * 1000).toTimeString().slice(0, 5)
              : null
          }
        />
      )}
    </>
  );
}
