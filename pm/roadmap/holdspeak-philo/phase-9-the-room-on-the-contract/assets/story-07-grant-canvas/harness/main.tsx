/* PHILO-9-07 canvas: the project delegation grant on the Remote Access ledger.
 *
 * Composition only; no product file changes.
 *
 * - Board 0 ("today") mounts the REAL `RemoteAccessModule`
 *   (web/src/pages/cores/SettingsCore.tsx:621, with Phase 7's built desk grant)
 *   on the REAL producer's wire (fixtures/remote-wire.json, captured by
 *   produce_wire.py from GET /api/settings/remote on the rig hub, isolated HOME).
 * - The other boards mount `ProposedRemoteAccess` below: the real module's
 *   JSX (SettingsCore.tsx:780-898), the same library species, plus the
 *   proposal: per-project grants in the credential row's in-place expansion.
 * - The project-grant half of the wire is UNBUILT. The canvas DEFINES it
 *   (README, "The wire contract"): the server projects each STORED
 *   kernel_project_delegations row to its EFFECTIVE state with the Phase 7
 *   time-aware rule. `project()` below is that rule; every board derives its
 *   chips from stored rows and a clock, never from a posed state.
 * - The frame is the production window, wired as SurfaceWindowHost wires it
 *   (web/src/desk/components/SurfaceWindows.tsx).
 */
import { createRoot } from "react-dom/client";
import { useState, type ReactNode } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "./main.css";
import wireJson from "./fixtures/remote-wire.json";
import projectsJson from "./fixtures/projects.json";
import { Button } from "@w/components/signal/Signal";
import { CycleGadget, GadgetGroup, GadgetRow } from "@w/desk/surface/gadgets";
import {
  Receipt,
  countToken,
  FootSlotContext,
  StateChip,
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceWell,
  Disclosure,
} from "@w/desk/surface";
import { WingSlotContext } from "@w/desk/surface/wings";
import { TitleSlotContext } from "@w/desk/surface/title";
import { useCoreWings } from "@w/pages/cores/core-hooks";
import { RemoteAccessModule, GRANT_WORDS } from "@w/pages/cores/SettingsCore";
import { DeskChrome } from "@w/desk/components/DeskChrome";
import { DeskWindowFrame, Dock } from "@w/desk/components/DeskWindow";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";

/* ── the real producer's wire, and the frozen clock ─────────────────── */

type GrantState = "LIVE" | "REVOKED" | "EXPIRED";
type Delegation = { state: GrantState; grant_id: string; expires_at: number | null };
type Credential = {
  id: string;
  identity: string;
  palette: string | string[] | null;
  expires_at: number;
  last_used_at: number | null;
  active: boolean;
  delegation: Delegation | null;
};
type Project = { id: string; name: string; is_archived?: number | boolean | null };
type RealWire = {
  enabled: boolean;
  bind_host: string | null;
  port: number | null;
  credentials: Credential[];
  delegations: (Delegation & { identity: string })[];
  active_count: number;
  total_count: number;
};

/** A row of kernel_project_delegations as STORED (charter "The project
 *  delegation grant": the desk table's columns plus project_id). */
type StoredProjectGrant = {
  identity: string;
  project_id: string;
  state: GrantState;
  grant_id: string;
  expires_at: number | null;
};
/** The wire: the EFFECTIVE projection of the latest stored row. */
type ProjectDelegation = Delegation & { project_id: string; project_name: string; project_archived?: boolean };
type OrphanProjectDelegation = ProjectDelegation & { identity: string };
type ProposedCredential = Omit<Credential, "palette"> & {
  palette: string;
  project_delegations: ProjectDelegation[];
};
type Wire = {
  enabled: boolean;
  bind_host: string | null;
  port: number | null;
  credentials: ProposedCredential[];
  /** Phase 7's desk-grant orphans, kept as built (SettingsCore.tsx:279, :869). */
  delegations: (Delegation & { identity: string })[];
  project_delegations: OrphanProjectDelegation[];
};
/** A kernel_desk_delegations row as STORED (Phase 7's table). */
type StoredDeskGrant = { identity: string; state: GrantState; grant_id: string; expires_at: number | null };

const REAL = wireJson as RealWire;
const PROJECTS = (projectsJson as Project[]).filter((p) => !p.is_archived);
const [PAYMENTS, HIRING] = [
  PROJECTS.find((p) => p.name === "Payments ledger cutover")!,
  PROJECTS.find((p) => p.name === "Hiring loop")!,
];
// Freeze "now" two hours after the capture's real last use.
const NOW_S = (REAL.credentials[0].last_used_at ?? 0) + 2 * 3600;
Date.now = () => NOW_S * 1000;
const PAST = NOW_S - 3600; // a real expires_at one hour before now

/** The ISSUED palette name, as the repaired producer stores it (story 07:
 *  "store the issued palette name, never reverse the map"). The real wire
 *  says ALL for desk-agent; the issue route answered DESK
 *  (fixtures/produce-log.json). */
const ISSUED_PALETTE: Record<string, string> = { "desk-agent": "DESK", "sweep-runner": "PROJECT" };
/** Palette compatibility (a correctness rule, settled): a grant's controls
 *  show only where the credential's palette holds the tools the grant covers.
 *  Measured on this tree with holdspeak.mcp.palettes.resolve_palette:
 *  project.run_steward / stop_steward / publish_update are in PROJECT, SWEEP,
 *  DESK and ALL; the desk family (desk.*, zone.*, decision.*, note.*, kb.*)
 *  is in DESK and ALL only (PROJECT and SWEEP hold none of it). */
const PROJECT_CAPABLE = new Set(["PROJECT", "SWEEP", "DESK", "ALL"]);
const DESK_CAPABLE = new Set(["DESK", "ALL"]);

/** The server's projection (Phase 7's rule, per (identity, project)): a stored
 *  LIVE row whose expires_at <= now is EXPIRED; REVOKED/EXPIRED pass through. */
function project(row: StoredProjectGrant | undefined, now: number): Delegation | null {
  if (!row) return null;
  const expired = row.state === "EXPIRED" || (row.state === "LIVE" && row.expires_at != null && row.expires_at <= now);
  return { state: expired ? "EXPIRED" : row.state, grant_id: row.grant_id, expires_at: row.expires_at };
}

/** GET /api/settings/remote as story 07 would return it. */
function serve(identities: string[], stored: StoredProjectGrant[], enabled = true, deskStored: StoredDeskGrant[] = [],
               archived: string[] = []): Wire {
  const nameOf = (id: string) => PROJECTS.find((p) => p.id === id)?.name ?? id;
  const latest = (identity: string, projectId: string) =>
    stored.filter((g) => g.identity === identity && g.project_id === projectId).at(-1);
  const creds = REAL.credentials.filter((c) => identities.includes(c.identity));
  const withCred = new Set(creds.map((c) => c.identity));
  const pairs = [...new Set(stored.map((g) => `${g.identity}\u0000${g.project_id}`))].map((k) => k.split("\u0000"));
  return {
    enabled,
    bind_host: REAL.bind_host,
    port: REAL.port,
    credentials: creds.map((c) => ({
      ...c,
      palette: ISSUED_PALETTE[c.identity] ?? String(c.palette),
      project_delegations: pairs
        .filter(([identity]) => identity === c.identity)
        .map(([identity, pid]) => ({ project_id: pid, project_name: nameOf(pid), project_archived: archived.includes(pid),
                                     ...project(latest(identity, pid), NOW_S)! })),
    })),
    // Phase 7's rule, unchanged: every desk grant LIVE in storage whose
    // identity has no credential row, projected (a past expiry says EXPIRED).
    delegations: deskStored
      .filter((d) => d.state === "LIVE" && !withCred.has(d.identity))
      .map((d) => {
        const expired = d.expires_at != null && d.expires_at <= NOW_S;
        return { identity: d.identity, state: expired ? "EXPIRED" as const : "LIVE" as const, grant_id: d.grant_id, expires_at: d.expires_at };
      }),
    project_delegations: pairs
      .filter(([identity, pid]) => !withCred.has(identity) && latest(identity, pid)?.state === "LIVE")
      .map(([identity, pid]) => ({ identity, project_id: pid, project_name: nameOf(pid), ...project(latest(identity, pid), NOW_S)! })),
  };
}

const nativeFetch = window.fetch.bind(window);
window.fetch = async (input, init) => {
  const url = typeof input === "string" ? input : (input as Request).url;
  if (url.startsWith("/api/settings/remote")) {
    return new Response(JSON.stringify(REAL), { status: 200, headers: { "content-type": "application/json" } });
  }
  if (url.startsWith("/api/")) {
    return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
  }
  return nativeFetch(input, init);
};

/* ── the words (two sets; the owner picks one) ──────────────────────── */

const WORDS = {
  // A (recommended): names the owner's own ruling, "Run, stop, publish".
  a: {
    allow: "Allow run and publish",
    stop: "Stop run and publish",
    live: "RUN AND PUBLISH ALLOWED",
    stopped: "RUN AND PUBLISH STOPPED",
    actAllow: "ALLOW RUN AND PUBLISH",
    actStop: "STOP RUN AND PUBLISH",
  },
  // B: shorter; names the place, not the acts.
  b: {
    allow: "Allow project work",
    stop: "Stop project work",
    live: "PROJECT WORK ALLOWED",
    stopped: "PROJECT WORK STOPPED",
    actAllow: "ALLOW PROJECT WORK",
    actStop: "STOP PROJECT WORK",
  },
} as const;
type Words = (typeof WORDS)["a"];

/** The refusal codes (the charter's project siblings of Phase 7's) and their
 *  plain face tokens. The code rides `data-code` for the fence. */
const REFUSAL_TOKEN: Record<string, string> = {
  owner_principal_required: "OWNER ONLY",
  project_delegation_required: "NO GRANT",
  project_delegation_revoked: "GRANT STOPPED",
  project_delegation_expired: "GRANT EXPIRED",
  invalid_arguments: "BAD REQUEST",
};

/* ── the real module's helpers, verbatim (SettingsCore.tsx:406-436) ─── */

function formatExpiry(epochSeconds: number): string {
  const d = new Date(epochSeconds * 1000);
  const months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  return `${months[d.getMonth()]} ${d.getDate()}`;
}
function relativeAge(epochSeconds: number): string {
  const seconds = Math.max(0, Math.floor((Date.now() - epochSeconds * 1000) / 1000));
  if (seconds < 60) return `${seconds} S AGO`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} M AGO`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} H AGO`;
  return `${Math.floor(seconds / 86400)} D AGO`;
}

/* ── the proposal ────────────────────────────────────────────────────── */

type Refusal = { verb: "allow" | "stop"; code: string };
type ActReceipt = {
  operation_id: string;
  outcome: "succeeded" | "refused";
  verb: "allow" | "stop";
  code?: string;
  identity: string;
  project: string;
  /** Set when the grant ended because the owner revoked the credential. */
  reason?: string;
  time: string;
  date: string;
};

/** Phase 7's desk grant chip, unchanged (built; its words are the real constant). */
function DeskGrantChip({ grant }: { grant: Delegation | null }) {
  if (!grant) return null;
  return grant.state === "LIVE"
    ? <StateChip state="success" label={GRANT_WORDS.live} data-testid="grant-chip" />
    : <StateChip state="idle" label={GRANT_WORDS.stopped} data-testid="grant-chip" />;
}

function ProjectGrantChip({ grant, words }: { grant: Delegation | null; words: Words }) {
  if (!grant) return null;
  return grant.state === "LIVE"
    ? <StateChip state="success" label={words.live} data-testid="project-grant-chip" />
    : <StateChip state="idle" label={words.stopped} data-testid="project-grant-chip" />;
}

/** The collapsed row's summary: only authority that is LIVE. One project by
 *  name; more by count (never a zero). */
function ProjectSummary({ grants, words }: { grants: ProjectDelegation[]; words: Words }) {
  const live = grants.filter((g) => g.state === "LIVE");
  if (live.length === 0) return null;
  return (
    <span data-testid="project-grant-summary">
      <StateChip state="success" label={words.live} />{" "}
      <span className="surface-token" data-chip>
        {live.length === 1 ? live[0].project_name.toUpperCase() : countToken(live.length, "PROJECT", "PROJECTS")}
      </span>
    </span>
  );
}

function RefusalChip({ refusal }: { refusal?: Refusal }) {
  if (!refusal) return null;
  return (
    <span data-testid="grant-refused" data-code={refusal.code}>
      <StateChip state="failure" label={refusal.verb === "allow" ? "CANNOT ALLOW" : "CANNOT STOP"} />{" "}
      <span className="surface-token" data-chip>{REFUSAL_TOKEN[refusal.code] ?? refusal.code}</span>
    </span>
  );
}

function ReceiptWell({ act, words }: { act: ActReceipt; words: Words }) {
  const ok = act.outcome === "succeeded";
  return (
    <SurfaceWell head="RECEIPT">
      <div className="grant-canvas-receipt" data-testid="grant-receipt" data-operation-id={act.operation_id} data-outcome={act.outcome} data-code={act.code}>
        {ok ? <StateChip state="success" label="SUCCEEDED" /> : <StateChip state="failure" label="REFUSED" />}
        <span className="surface-token" data-chip>
          {ok ? (act.verb === "stop" ? words.stopped : words.live) : act.verb === "stop" ? words.actStop : words.actAllow}
        </span>
        {!ok && act.code ? <span className="surface-token" data-chip>{REFUSAL_TOKEN[act.code]}</span> : null}
        {act.reason ? <span className="surface-token" data-chip>{act.reason}</span> : null}
        <span className="gadget-fact">{act.project}</span>
        <span className="gadget-fact">{act.identity}</span>
        <span className="surface-token" data-chip>BY OWNER</span>
        <span className="surface-token" data-chip data-muted>{act.date} {act.time}</span>
      </div>
    </SurfaceWell>
  );
}

/** The credential row's in-place expansion: one line per project the owner
 *  can grant. The pick is in the world: no popover, no modal. */
function ProjectLines({
  cred, words, refusals,
}: { cred: ProposedCredential; words: Words; refusals: Record<string, Refusal> }) {
  // The Settings grammar (GadgetRow, as the Remote access group itself):
  // the project's name is the label; its grant chip and verb are the gadget.
  // Added 2026-09-28 (Muad'Dib's ruling): an archived project keeps its
  // grant, so a LIVE grant on it stays listed -- ARCHIVED, Stop only.
  const archivedLive = cred.project_delegations.filter((g) => g.project_archived && g.state === "LIVE");
  const lines = [
    ...PROJECTS.filter((p) => !archivedLive.some((g) => g.project_id === p.id)).map((p) => ({ id: p.id, name: p.name, archived: false })),
    ...archivedLive.map((g) => ({ id: g.project_id, name: g.project_name, archived: true })),
  ];
  return (
    <div data-testid={`project-lines-${cred.identity}`}>
      {lines.map((p) => {
        const grant = cred.project_delegations.find((g) => g.project_id === p.id) ?? null;
        return (
          <GadgetRow key={p.id} label={p.name}>
            <span className="grant-canvas-line" data-testid={`project-line-${p.id}`}>
              {p.archived ? <span className="surface-token" data-chip>ARCHIVED</span> : null}
              <ProjectGrantChip grant={grant} words={words} />
              <RefusalChip refusal={refusals[`${cred.identity}/${p.id}`]} />
              <Button variant="ghost" dense data-testid="project-grant-verb">
                {grant?.state === "LIVE" ? words.stop : words.allow}
              </Button>
            </span>
          </GadgetRow>
        );
      })}
    </div>
  );
}

function ProposedRemoteAccess({
  wire, words, open = [], refusals = {}, openReceipt = null,
}: {
  wire: Wire;
  words: Words;
  open?: string[];
  refusals?: Record<string, Refusal>;
  openReceipt?: ActReceipt | null;
}) {
  const enabled = wire.enabled;
  // Phase 7's visibility, widened to project grants: OFF keeps every row
  // that carries LIVE authority (desk or project); orphan rows always show.
  const credentials = enabled
    ? wire.credentials
    : wire.credentials.filter((c) => c.delegation?.state === "LIVE" || c.project_delegations.some((g) => g.state === "LIVE"));
  const orphans = wire.project_delegations;
  const deskOrphans = wire.delegations;
  const activeCount = credentials.filter((c) => c.active).length;
  const totalCount = wire.credentials.length;
  // Phase 7's ledger condition, widened: any credential OR any grant row.
  const showLedger = credentials.length > 0 || orphans.length > 0 || deskOrphans.length > 0;
  return (
    <GadgetGroup label="Remote access">
      <GadgetRow label="Streamable HTTP">
        <CycleGadget label="Remote transport" value={enabled ? "ON" : "OFF"} options={[{ value: "OFF" }, { value: "ON" }]} onChange={() => undefined} />
        {enabled && totalCount > 0 ? (
          <span className="surface-token" data-chip data-testid="remote-total-count">{countToken(totalCount, "CREDENTIAL", "CREDENTIALS")}</span>
        ) : null}
      </GadgetRow>
      {showLedger ? (
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
            const capable = PROJECT_CAPABLE.has(cred.palette);
            const deskCapable = DESK_CAPABLE.has(cred.palette);
            const isOpen = capable && open.includes(cred.identity);
            const bodyId = `project-lines-body-${cred.id}`;
            return (
              <SurfaceLedgerRow
                key={cred.id}
                lead={<StateChip state={cred.active ? "success" : "idle"} label="" icon="●" />}
                primary={cred.identity}
                expands={false}
                open={isOpen}
                data-testid={`credential-row-${cred.id}`}
                cells={<>
                  {deskCapable ? <DeskGrantChip grant={cred.delegation} /> : null}
                  <ProjectSummary grants={cred.project_delegations} words={words} />
                  <span className="surface-token" data-chip data-testid="palette-token">{cred.palette}</span>
                  {cred.active
                    ? <span className="surface-token" data-chip>EXPIRES {formatExpiry(cred.expires_at)}</span>
                    : <StateChip state="warning" label="EXPIRED" />}
                  <span className="surface-token" data-chip data-muted>
                    {cred.last_used_at ? `LAST USED ${relativeAge(cred.last_used_at)}` : "NEVER USED"}
                  </span>
                </>}
                trailing={<>
                  {capable ? (
                    // The library Disclosure's trigger (HS-200-15: a body
                    // rendered in the ledger row's own expansion slot).
                    <Disclosure
                      label="Projects"
                      ariaLabel={`Projects: ${cred.identity}`}
                      open={isOpen}
                      onOpenChange={() => undefined}
                      controlsId={bodyId}
                      variant="default"
                    >
                      {null}
                    </Disclosure>
                  ) : null}
                  {deskCapable ? (
                    <Button variant="ghost" dense data-testid="grant-verb">
                      {cred.delegation?.state === "LIVE" ? GRANT_WORDS.stop : GRANT_WORDS.allow}
                    </Button>
                  ) : null}
                  <Button variant="ghost" dense data-testid="credential-revoke">{GRANT_WORDS.revokeCredential}</Button>
                </>}
              >
                {capable ? <div id={bodyId}><ProjectLines cred={cred} words={words} refusals={refusals} /></div> : null}
              </SurfaceLedgerRow>
            );
          })}
          {deskOrphans.map((grant) => (
            // Phase 7's desk-grant orphan row, as built (SettingsCore.tsx:869-892).
            <SurfaceLedgerRow
              key={grant.grant_id}
              lead={<StateChip state="idle" label="" icon="●" />}
              primary={grant.identity}
              expands={false}
              data-testid={`delegation-row-${grant.grant_id}`}
              cells={<>
                <DeskGrantChip grant={grant} />
                <span className="surface-token" data-chip data-muted>{GRANT_WORDS.noCredential}</span>
              </>}
              trailing={grant.state === "LIVE"
                ? <Button variant="ghost" dense data-testid="grant-verb">{GRANT_WORDS.stop}</Button>
                : undefined}
            />
          ))}
          {orphans.map((grant) => (
            <SurfaceLedgerRow
              key={grant.grant_id}
              lead={<StateChip state="idle" label="" icon="●" />}
              primary={grant.identity}
              expands={false}
              data-testid={`project-delegation-row-${grant.grant_id}`}
              cells={<>
                <ProjectGrantChip grant={grant} words={words} />
                <span className="surface-token" data-chip>{grant.project_name.toUpperCase()}</span>
                <span className="surface-token" data-chip data-muted>{GRANT_WORDS.noCredential}</span>
              </>}
              trailing={grant.state === "LIVE"
                ? <Button variant="ghost" dense data-testid="project-grant-verb">{words.stop}</Button>
                : undefined}
            />
          ))}
        </SurfaceLedger>
      ) : null}
      {openReceipt ? <ReceiptWell act={openReceipt} words={words} /> : null}
      {enabled ? (
        <div className="prefs-issue-start">
          <Button variant="ghost" data-testid="issue-credential-btn">Issue credential</Button>
        </div>
      ) : null}
    </GadgetGroup>
  );
}

/** The Settings foot with the last grant act's receipt in the centre slot
 *  (Phase 7's ratified receipt Button, unchanged). */
function Foot({ act, open }: { act: ActReceipt | null; open?: boolean }) {
  const word = act ? (act.outcome === "succeeded" ? (act.verb === "stop" ? "STOPPED" : "ALLOWED") : "REFUSED") : "";
  return (
    <SurfaceFooter
      receipt={act ? (
        <Button variant="ghost" dense aria-expanded={open || false} aria-label={`Receipt ${word.toLowerCase()} ${act.time}`} data-testid="foot-receipt">
          <Receipt status={act.outcome === "succeeded" ? "ok" : "danger"} label={word} timestamp={act.time} />
        </Button>
      ) : null}
      verbs={<Button variant="ghost" dense className="prefs-back">« PREFS</Button>}
    />
  );
}

/* ── the boards ─────────────────────────────────────────────────────── */

const BOTH = ["desk-agent", "sweep-runner"];
/** desk-agent's real desk grant (the captured wire), as a stored row. */
const DESK_LIVE: StoredDeskGrant = {
  identity: "desk-agent", state: "LIVE", expires_at: null,
  grant_id: REAL.credentials.find((c) => c.identity === "desk-agent")?.delegation?.grant_id ?? "deskdeleg",
};
const g = (state: GrantState, project_id = PAYMENTS.id, expires_at: number | null = null, identity = "sweep-runner", grant_id = "projdeleg_5b1c"): StoredProjectGrant =>
  ({ identity, project_id, state, grant_id, expires_at });
const act = (over: Partial<ActReceipt>): ActReceipt => ({
  operation_id: "op_4e7a", outcome: "succeeded", verb: "allow", identity: "sweep-runner",
  project: PAYMENTS.name, time: "14:05", date: "SEP 27", ...over,
});

type Board = { body: ReactNode; foot: ReactNode };
function boardFor(name: string, words: Words): Board {
  const P = (wire: Wire, extra: Partial<Parameters<typeof ProposedRemoteAccess>[0]> = {}) => (
    <ProposedRemoteAccess wire={wire} words={words} {...extra} />
  );
  switch (name) {
    case "1-never":
      return { body: P(serve(BOTH, []), { open: ["sweep-runner"] }), foot: <Foot act={null} /> };
    case "2-live":
      return { body: P(serve(BOTH, [g("LIVE")])), foot: <Foot act={act({})} /> };
    case "3-live-open":
      return { body: P(serve(BOTH, [g("LIVE")]), { open: ["sweep-runner"] }), foot: <Foot act={act({})} /> };
    case "4-stopped":
      return { body: P(serve(BOTH, [g("REVOKED")]), { open: ["sweep-runner"] }), foot: <Foot act={act({ verb: "stop", time: "14:07" })} /> };
    case "5-expired":
      // Stored LIVE with a real past expires_at; the projection says EXPIRED.
      return { body: P(serve(BOTH, [g("LIVE", PAYMENTS.id, PAST)]), { open: ["sweep-runner"] }), foot: <Foot act={null} /> };
    case "6-orphan":
      // Both credential rows are gone with their grants still LIVE (a restart
      // or a lost credential; never an owner revoke, which revokes the grant
      // first). Phase 7's desk orphan and the project orphan both stay, each
      // with its Stop.
      return { body: P(serve([], [g("LIVE")], true, [DESK_LIVE])), foot: <Foot act={null} /> };
    case "7-orphan-off":
      return { body: P(serve([], [g("LIVE")], false, [DESK_LIVE])), foot: <Foot act={null} /> };
    case "10-last-orphan-stopped": {
      // Stop on the last orphan: the row goes; with nothing left the ledger
      // goes; the receipt stays in the footer and its well (rendered open).
      const stopped = act({ verb: "stop", time: "14:13", operation_id: "op_b310" });
      return { body: P(serve([], [g("LIVE"), g("REVOKED")], false), { openReceipt: stopped }), foot: <Foot act={stopped} open /> };
    }
    case "11-credential-revoked": {
      // The owner revokes sweep-runner's credential: its project grant is
      // revoked first (reason credential_revoked), then the row is removed.
      // No orphan remains; the receipt stays (rendered open).
      const revoked = act({ verb: "stop", time: "14:15", operation_id: "op_c7a2", reason: "CREDENTIAL REVOKED" });
      return { body: P(serve(["desk-agent"], [g("LIVE"), g("REVOKED")]), { openReceipt: revoked }), foot: <Foot act={revoked} open /> };
    }
    case "7b-off-credential":
      return { body: P(serve(BOTH, [g("LIVE")], false), { open: ["sweep-runner"] }), foot: <Foot act={null} /> };
    case "8-refused": {
      // The owner's Stop on Payments is refused: another owner request
      // stopped it first. The reread shows STOPPED; the refusal stays on the
      // line and in the footer receipt (rendered open).
      const refused = act({ outcome: "refused", verb: "stop", code: "project_delegation_required", time: "14:11", operation_id: "op_9e02" });
      return {
        body: P(serve(BOTH, [g("LIVE"), g("REVOKED")]), {
          open: ["sweep-runner"],
          refusals: { [`sweep-runner/${PAYMENTS.id}`]: { verb: "stop", code: "project_delegation_required" } },
          openReceipt: refused,
        }),
        foot: <Foot act={refused} open />,
      };
    }
    case "12-archived":
      // Added 2026-09-28 by Muad'Dib's ruling: Payments archived with its grant
      // still LIVE (archive keeps grants); the line stays, ARCHIVED, Stop only.
      return { body: P(serve(BOTH, [g("LIVE")], true, [], [PAYMENTS.id]), { open: ["sweep-runner"] }), foot: <Foot act={null} /> };
    case "12b-archived-off":
      return { body: P(serve(BOTH, [g("LIVE")], false, [], [PAYMENTS.id]), { open: ["sweep-runner"] }), foot: <Foot act={null} /> };
    case "9-two-projects":
      return {
        body: P(serve(BOTH, [g("LIVE"), g("LIVE", HIRING.id, null, "sweep-runner", "projdeleg_77d0")])),
        foot: <Foot act={act({ project: HIRING.name, time: "14:09" })} />,
      };
    default:
      return { body: <RemoteAccessModule />, foot: <Foot act={null} /> };
  }
}

function SettingsBody({ body, foot }: Board) {
  useCoreWings([{ id: "settings", label: "Settings" }, { id: "guide", label: "Guide" }], "settings");
  return (
    <>
      <div className="prefs-module">
        <h2 className="gadget-pane-title">System</h2>
        {body}
      </div>
      {foot}
    </>
  );
}

function Canvas() {
  const params = new URLSearchParams(location.search);
  const board = params.get("board") ?? "0-today";
  const words = WORDS[(params.get("words") as "a" | "b") ?? "a"] ?? WORDS.a;
  const { body, foot } = boardFor(board, words);
  const [wings, setWings] = useState<ReactNode>(null);
  const [footEl, setFootEl] = useState<HTMLElement | null>(null);
  return (
    <RuntimeBusProvider>
      <div className="grant-canvas desk-next" data-testid="grant-canvas" data-board={board}>
        <DeskChrome showDailyStarts={false} />
        <DeskWindowFrame
          id="surface-settings"
          glyph="⚙"
          title="Settings"
          label="Settings"
          eyebrow="Configuration"
          minW={560}
          defaultH={600}
          wings={wings}
          open
          entrance={false}
          onClose={() => undefined}
          className="desk-surface-window desk-settings-window grant-canvas-window"
        >
          <FootSlotContext.Provider value={footEl}>
            <div className="desk-surface-body" data-testid="settings-body">
              <TitleSlotContext.Provider value={() => undefined}>
                <WingSlotContext.Provider value={setWings}>
                  <SettingsBody body={body} foot={foot} />
                </WingSlotContext.Provider>
              </TitleSlotContext.Provider>
            </div>
            <footer ref={setFootEl} className="desk-surface-foot surface-footer" />
          </FootSlotContext.Provider>
        </DeskWindowFrame>
        <Dock />
      </div>
    </RuntimeBusProvider>
  );
}

createRoot(document.getElementById("root")!).render(<Canvas />);
