/* PHILO-7-02 canvas (round two): the delegation grant on the Remote Access
 * ledger.
 *
 * Composition only. The one library change this canvas carries is CSS (the
 * 12 px floor in five species, and `.btn > .surface-receipt`); no product TSX
 * changes.
 *
 * - Board 0 ("today") mounts the REAL `RemoteAccessModule` exported from
 *   web/src/pages/cores/SettingsCore.tsx, fed the REAL producer's wire
 *   (fixtures/remote-wire.json, captured by produce_remote_wire.py from
 *   GET /api/settings/remote on the real hub over an isolated database).
 * - The other boards mount `ProposedRemoteAccess` below: the same JSX as the
 *   real module (SettingsCore.tsx:597-735), composed of the same library
 *   species, with the proposal added.
 * - The grant half of the wire is UNBUILT. The canvas DEFINES it (README,
 *   "The wire contract"): the server projects each STORED grant row to its
 *   EFFECTIVE state with the beat's time-aware rule (`by_identity(now)`,
 *   design/grant-lifecycle-beat.md:52 row 2, :58, :155). `project()` below is
 *   that rule; every board derives its chip from a stored row and a clock,
 *   never from a posed state.
 * - The frame is the production window: DeskChrome, DeskWindowFrame with the
 *   Settings classes, the foot and wing slots wired as SurfaceWindowHost
 *   wires them (desk/components/SurfaceWindows.tsx:155-211).
 */
import { createRoot } from "react-dom/client";
import { useState, type ReactNode } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "./main.css";
import wireJson from "./fixtures/remote-wire.json";
import { Button } from "@w/components/signal/Signal";
import {
  CycleGadget,
  GadgetGroup,
  GadgetRow,
} from "@w/desk/surface/gadgets";
import {
  Receipt,
  countToken,
  FootSlotContext,
  StateChip,
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceWell,
} from "@w/desk/surface";
import { WingSlotContext } from "@w/desk/surface/wings";
import { TitleSlotContext } from "@w/desk/surface/title";
import { useCoreWings } from "@w/pages/cores/core-hooks";
import { RemoteAccessModule } from "@w/pages/cores/SettingsCore";
import { DeskChrome } from "@w/desk/components/DeskChrome";
import { DeskWindowFrame, Dock } from "@w/desk/components/DeskWindow";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";

/* ── the real producer's wire, and the frozen clock ─────────────────── */

type Credential = {
  id: string;
  identity: string;
  palette: string | string[] | null;
  expires_at: number;
  last_used_at: number | null;
  active: boolean;
};
type GrantState = "LIVE" | "REVOKED" | "EXPIRED";
/** A row of kernel_desk_delegations as STORED (the beat's table, :26-36). */
type StoredGrant = { identity: string; state: GrantState; grant_id: string; expires_at: number | null };
/** The wire: the EFFECTIVE projection of the latest stored row. */
type Delegation = { state: GrantState; grant_id: string; expires_at: number | null };
type OrphanDelegation = Delegation & { identity: string };
type Wire = {
  enabled: boolean;
  bind_host: string | null;
  port: number | null;
  credentials: (Credential & { delegation: Delegation | null })[];
  delegations: OrphanDelegation[];
  active_count: number;
  total_count: number;
};
type RealWire = Omit<Wire, "credentials" | "delegations"> & { credentials: Credential[] };

const REAL = wireJson as RealWire;
// Freeze "now" at two hours after the real capture's last use, so the
// relative ages on the shots are stable (LAST USED 2 H AGO).
const NOW_S = (REAL.credentials[0].last_used_at ?? 0) + 2 * 3600;
Date.now = () => NOW_S * 1000;
const PAST = NOW_S - 3600; // a real expires_at one hour before now

/** The server's projection (the canvas's statement of the wire contract):
 *  the beat's check order, row 2 BEFORE row 3 — a stored LIVE row whose
 *  expires_at <= now is EXPIRED; REVOKED and EXPIRED pass through. */
function project(row: StoredGrant | undefined, now: number): Delegation | null {
  if (!row) return null; // never granted: `_required`, no chip
  const expired = row.state === "EXPIRED" || (row.state === "LIVE" && row.expires_at != null && row.expires_at <= now);
  return { state: expired ? "EXPIRED" : row.state, grant_id: row.grant_id, expires_at: row.expires_at };
}

/** GET /api/settings/remote as story 02 would return it: the real credential
 *  rows, each with its identity's effective grant; plus `delegations` for
 *  every stored-LIVE grant whose identity has no credential row (beat :155). */
function serve(credentials: Credential[], stored: StoredGrant[], enabled = true): Wire {
  const latest = (identity: string) => stored.filter((g) => g.identity === identity).at(-1);
  const withCred = new Set(credentials.map((c) => c.identity));
  return {
    ...REAL,
    enabled,
    credentials: credentials.map((c) => ({ ...c, delegation: project(latest(c.identity), NOW_S) })),
    delegations: stored
      .filter((g) => g.state === "LIVE" && !withCred.has(g.identity))
      .map((g) => ({ identity: g.identity, ...project(g, NOW_S)! })),
    active_count: credentials.filter((c) => c.active).length,
    total_count: credentials.length,
  };
}

const nativeFetch = window.fetch.bind(window);
window.fetch = async (input, init) => {
  const url = typeof input === "string" ? input : (input as Request).url;
  if (url.startsWith("/api/settings/remote")) {
    // Board 0: today's module reads today's wire (two credentials, as before).
    const today = { ...REAL, credentials: REAL.credentials.slice(0, 2), active_count: 2, total_count: 2 };
    return new Response(JSON.stringify(today), { status: 200, headers: { "content-type": "application/json" } });
  }
  if (url.startsWith("/api/")) {
    return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
  }
  return nativeFetch(input, init);
};

/* ── the words (two sets; the owner picks one) ──────────────────────── */

const WORDS = {
  // A: the charter's proposal (current-phase-status.md:269).
  a: {
    allow: "Allow filing",
    stop: "Stop filing",
    live: "FILING ALLOWED",
    stopped: "FILING STOPPED",
    actAllow: "ALLOW FILING",
    actStop: "STOP FILING",
  },
  // B: recommended (Astra r1 finding 6 supports it): name both things.
  b: {
    allow: "Allow filing and decisions",
    stop: "Stop filing and decisions",
    live: "FILING AND DECISIONS ALLOWED",
    stopped: "FILING AND DECISIONS STOPPED",
    actAllow: "ALLOW FILING AND DECISIONS",
    actStop: "STOP FILING AND DECISIONS",
  },
} as const;
type Words = (typeof WORDS)["a"];

/** The refusal codes (verbatim, design/grant-lifecycle-beat.md:182) and
 *  their plain face tokens. The code rides `data-code` for the fence. */
const REFUSAL_TOKEN: Record<string, string> = {
  owner_principal_required: "OWNER ONLY",
  desk_delegation_required: "NO GRANT",
  desk_delegation_revoked: "GRANT STOPPED",
  desk_delegation_expired: "GRANT EXPIRED",
  invalid_arguments: "BAD REQUEST",
};

/* ── the real module's helpers, verbatim (SettingsCore.tsx:273-300) ─── */

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
function paletteLabel(palette: string | string[] | null): string {
  if (!palette) return "ALL";
  if (typeof palette === "string") return palette;
  if (palette.length === 0) return "ALL";
  return palette[0];
}

/* ── the proposal ────────────────────────────────────────────────────── */

type Refusal = { verb: "allow" | "stop"; code: string };
/** The last grant act's receipt, as the route returns it ({operation_id, receipt}). */
type ActReceipt = {
  operation_id: string;
  outcome: "succeeded" | "refused";
  verb: "allow" | "stop";
  code?: string;
  identity: string;
  time: string; // HH:MM
  date: string; // SEP 25
};

function GrantChip({ grant, words }: { grant: Delegation | null; words: Words }) {
  if (!grant) return null;
  return grant.state === "LIVE" ? (
    <StateChip state="success" label={words.live} data-testid="grant-chip" />
  ) : (
    <StateChip state="idle" label={words.stopped} data-testid="grant-chip" />
  );
}

function RefusalChip({ refusal }: { refusal?: Refusal }) {
  if (!refusal) return null;
  return (
    <span data-testid="grant-refused" data-code={refusal.code}>
      <StateChip state="failure" label={refusal.verb === "allow" ? "CANNOT ALLOW" : "CANNOT STOP"} />{" "}
      <span className="surface-token" data-chip="">{REFUSAL_TOKEN[refusal.code] ?? refusal.code}</span>
    </span>
  );
}

function GrantVerb({ grant, words }: { grant: Delegation | null; words: Words }) {
  return (
    <Button variant="ghost" dense data-testid="grant-verb">
      {grant?.state === "LIVE" ? words.stop : words.allow}
    </Button>
  );
}

/** The receipt well: the operation's receipt, readable after its row is
 *  gone. One species for both outcomes. */
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
        <span className="gadget-fact">{act.identity}</span>
        <span className="surface-token" data-chip>BY OWNER</span>
        <span className="surface-token" data-chip data-muted>{act.date} {act.time}</span>
      </div>
    </SurfaceWell>
  );
}

function ProposedRemoteAccess({
  wire,
  words,
  refusals = {},
  openReceipt = null,
}: {
  wire: Wire;
  words: Words;
  refusals?: Record<string, Refusal>;
  openReceipt?: ActReceipt | null;
}) {
  const enabled = wire.enabled;
  // PROPOSED: with remote OFF the ledger keeps every row that carries
  // authority (an effective LIVE grant), credential-backed or not. With
  // remote ON it shows every credential row, as today.
  const credentials = enabled ? wire.credentials : wire.credentials.filter((c) => c.delegation?.state === "LIVE");
  const delegations = wire.delegations;
  const activeCount = credentials.filter((c) => c.active).length;
  const totalCount = wire.credentials.length;
  const addressToken = enabled && wire.port ? `${wire.bind_host || "0.0.0.0"}:${wire.port}` : null;
  // The beat's ledger condition (:155): any credential OR any delegation row.
  const showLedger = credentials.length > 0 || delegations.length > 0;
  return (
    <GadgetGroup label="Remote access">
      <GadgetRow label="Streamable HTTP">
        <CycleGadget
          label="Remote transport"
          value={enabled ? "ON" : "OFF"}
          options={[{ value: "OFF" }, { value: "ON" }]}
          onChange={() => undefined}
        />
        {enabled && addressToken ? <span className="gadget-fact">{addressToken}</span> : null}
        {enabled && totalCount > 0 ? (
          <span className="surface-token" data-chip data-testid="remote-total-count">
            {countToken(totalCount, "CREDENTIAL", "CREDENTIALS")}
          </span>
        ) : null}
      </GadgetRow>
      {showLedger ? (
        <SurfaceLedger
          count={<>
            AGENTS
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
                <GrantChip grant={cred.delegation} words={words} />
                <RefusalChip refusal={refusals[cred.identity]} />
                <span className="surface-token" data-chip>{paletteLabel(cred.palette)}</span>
                {cred.active ? (
                  <span className="surface-token" data-chip>EXPIRES {formatExpiry(cred.expires_at)}</span>
                ) : (
                  <StateChip state="warning" label="EXPIRED" />
                )}
                <span className="surface-token" data-chip data-muted>
                  {cred.last_used_at ? `LAST USED ${relativeAge(cred.last_used_at)}` : "NEVER USED"}
                </span>
              </>}
              trailing={<>
                <GrantVerb grant={cred.delegation} words={words} />
                <Button variant="ghost" dense data-testid="credential-revoke">Revoke credential</Button>
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
                <GrantChip grant={grant} words={words} />
                <RefusalChip refusal={refusals[grant.identity]} />
                <span className="surface-token" data-chip data-muted>NO CREDENTIAL</span>
              </>}
              trailing={grant.state === "LIVE" ? <GrantVerb grant={grant} words={words} /> : undefined}
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

/** The Settings foot (PrefStatusBar, settingsPrefs.tsx:646-656) with the
 *  proposal: the last grant act's receipt in the footer's CENTRE slot (the
 *  species' own `receipt` slot, SurfaceFooter.tsx:24), away from the resize
 *  grip, as ONE plated library Button whose face is the library Receipt. */
function Foot({ act, open }: { act: ActReceipt | null; open?: boolean }) {
  return (
    <SurfaceFooter
      receipt={act ? (
        <Button
          variant="ghost"
          dense
          aria-expanded={open || false}
          aria-label={`Receipt ${act.outcome === "succeeded" ? (act.verb === "stop" ? "stopped" : "allowed") : "refused"} ${act.time}`}
          data-testid="foot-receipt"
        >
          <Receipt
            status={act.outcome === "succeeded" ? "ok" : "danger"}
            label={act.outcome === "succeeded" ? (act.verb === "stop" ? "STOPPED" : "ALLOWED") : "REFUSED"}
            timestamp={act.time}
          />
        </Button>
      ) : null}
      verbs={<Button variant="ghost" dense className="prefs-back">« PREFS</Button>}
    />
  );
}

/* ── the boards ─────────────────────────────────────────────────────── */

const [DESK, SWEEP, REVIEW] = REAL.credentials;
const TWO = [DESK, SWEEP];
const g = (identity: string, state: GrantState, expires_at: number | null = null, grant_id = "deskdeleg_3f9a"): StoredGrant =>
  ({ identity, state, grant_id, expires_at });
const act = (over: Partial<ActReceipt>): ActReceipt => ({
  operation_id: "op_7c41", outcome: "succeeded", verb: "stop", identity: "desk-agent", time: "14:07", date: "SEP 25", ...over,
});

type Board = { body: ReactNode; foot: ReactNode };
function boardFor(name: string, words: Words): Board {
  const P = (wire: Wire, extra: Partial<Parameters<typeof ProposedRemoteAccess>[0]> = {}) => (
    <ProposedRemoteAccess wire={wire} words={words} {...extra} />
  );
  switch (name) {
    case "1-never":
      return { body: P(serve(TWO, [])), foot: <Foot act={null} /> };
    case "2-live":
      return {
        body: P(serve(TWO, [g("desk-agent", "LIVE")])),
        foot: <Foot act={act({ verb: "allow", time: "14:05" })} />,
      };
    case "3-revoked":
      return {
        body: P(serve(TWO, [g("desk-agent", "REVOKED")])),
        foot: <Foot act={act({})} />,
      };
    case "4-expired":
      // Stored LIVE with a real past expires_at; the projection says EXPIRED.
      return { body: P(serve(TWO, [g("desk-agent", "LIVE", PAST)])), foot: <Foot act={null} /> };
    case "4b-cred-expired":
      // The real expired credential (active=false, from the producer) with a
      // LIVE grant: both truths (beat :147, :154).
      return { body: P(serve([DESK, SWEEP, REVIEW], [g("review-agent", "LIVE", null, "deskdeleg_8d20")])), foot: <Foot act={null} /> };
    case "5-orphan":
      return { body: P(serve([SWEEP], [g("desk-agent", "LIVE")])), foot: <Foot act={null} /> };
    case "5b-orphan-off":
      return { body: P(serve([], [g("desk-agent", "LIVE")], false)), foot: <Foot act={null} /> };
    case "5c-orphan-expired":
      return { body: P(serve([SWEEP], [g("desk-agent", "LIVE", PAST)])), foot: <Foot act={null} /> };
    case "5d-off-credential":
      // Remote OFF, the credential retained, its grant LIVE: the row stays.
      return { body: P(serve(TWO, [g("desk-agent", "LIVE")], false)), foot: <Foot act={null} /> };
    case "6-refused":
      return {
        body: P(serve(TWO, [g("desk-agent", "REVOKED")]), {
          refusals: {
            "desk-agent": { verb: "stop", code: "desk_delegation_required" },
            "sweep-runner": { verb: "allow", code: "owner_principal_required" },
          },
        }),
        foot: <Foot act={act({ outcome: "refused", code: "owner_principal_required", verb: "allow", identity: "sweep-runner", time: "14:09" })} />,
      };
    case "6b-refused-gone": {
      // A LIVE grant with no credential; the owner's Stop is refused because
      // another owner request revoked it first. The reread removes the row;
      // the refusal survives in the foot receipt and its well.
      const refused = act({ outcome: "refused", code: "desk_delegation_required", time: "14:11", operation_id: "op_9e02" });
      return {
        body: P(serve([SWEEP], [g("desk-agent", "REVOKED")]), { openReceipt: refused }),
        foot: <Foot act={refused} open />,
      };
    }
    case "7-empty": {
      const stopped = act({});
      return {
        body: P(serve([], [g("desk-agent", "REVOKED")]), { openReceipt: stopped }),
        foot: <Foot act={stopped} open />,
      };
    }
    default:
      return { body: <RemoteAccessModule />, foot: <Foot act={null} /> };
  }
}

function SettingsBody({ body, foot }: Board) {
  // The real Settings wings (SettingsCore.tsx:233-236) published into the
  // real head slot by the real hook.
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
