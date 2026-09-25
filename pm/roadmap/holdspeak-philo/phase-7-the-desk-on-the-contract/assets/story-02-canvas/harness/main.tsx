/* PHILO-7-02 canvas: the delegation grant on the Remote Access ledger.
 *
 * Composition only. No product file is changed by this harness.
 *
 * - Board 0 ("today") mounts the REAL `RemoteAccessModule` exported from
 *   web/src/pages/cores/SettingsCore.tsx, fed the REAL producer's wire
 *   (fixtures/remote-wire.json, captured by produce_remote_wire.py from
 *   GET /api/settings/remote on the real hub over an isolated database).
 * - Boards 1-7 mount `ProposedRemoteAccess` below: the same JSX as the real
 *   module (SettingsCore.tsx:597-735), composed of the same library species
 *   (GadgetGroup, GadgetRow, CycleGadget, SurfaceLedger, SurfaceLedgerRow,
 *   StateChip, Button, SurfaceWell, Receipt, SurfaceFooter), with the
 *   proposal added: one grant chip, one grant verb, the caption, the
 *   no-credential row, the refusal on the row, the receipt in the foot.
 * - The grant half of the wire is UNBUILT on this tree. It follows the
 *   lifecycle beat's decided shape (design/grant-lifecycle-beat.md:155):
 *   `delegations: [{identity, state, grant_id, expires_at}]` for grant rows
 *   with no credential. The per-credential `delegation` field is a CANVAS
 *   ASSUMPTION (the beat decides the chip's rule, not its field name).
 * - Both frames are the production window: DeskChrome, DeskWindowFrame with
 *   the Settings classes, the foot slot and wing slot exactly as
 *   SurfaceWindowHost wires them (desk/components/SurfaceWindows.tsx:155-211).
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
type Delegation = { state: GrantState; grant_id: string; expires_at: number | null };
type OrphanDelegation = Delegation & { identity: string };
type Wire = {
  enabled: boolean;
  bind_host: string | null;
  port: number | null;
  credentials: (Credential & { delegation?: Delegation | null })[];
  delegations?: OrphanDelegation[];
  active_count: number;
  total_count: number;
};

const REAL: Wire = wireJson as Wire;
// Freeze "now" at two hours after the real capture's last use, so the
// relative ages on the shots are stable (LAST USED 2 H AGO).
const FROZEN_NOW = ((REAL.credentials[0].last_used_at ?? 0) + 2 * 3600) * 1000;
Date.now = () => FROZEN_NOW;

const nativeFetch = window.fetch.bind(window);
window.fetch = async (input, init) => {
  const url = typeof input === "string" ? input : (input as Request).url;
  if (url.startsWith("/api/settings/remote")) {
    return new Response(JSON.stringify(REAL), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
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
    cantAllow: "CAN'T ALLOW",
    cantStop: "CAN'T STOP",
  },
  // B: the canvas's recommendation: name both things the grant controls.
  b: {
    allow: "Allow filing and decisions",
    stop: "Stop filing and decisions",
    live: "FILING AND DECISIONS ALLOWED",
    stopped: "FILING AND DECISIONS STOPPED",
    cantAllow: "CAN'T ALLOW",
    cantStop: "CAN'T STOP",
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
type FootReceipt = { status: "ok" | "danger"; label: string; time: string } | null;
type ReceiptFacts = { outcome: string; act: string; identity: string; time: string } | null;

/** The grant chip: FILING ALLOWED when the time-aware rule says LIVE,
 *  FILING STOPPED for REVOKED or EXPIRED, nothing when never granted. */
function GrantChip({ grant, words }: { grant: Delegation | null | undefined; words: Words }) {
  if (!grant) return null;
  return grant.state === "LIVE" ? (
    <StateChip state="success" label={words.live} data-testid="grant-chip" />
  ) : (
    <StateChip state="idle" label={words.stopped} data-testid="grant-chip" />
  );
}

function RefusalChip({ refusal, words }: { refusal?: Refusal; words: Words }) {
  if (!refusal) return null;
  return (
    <span data-testid="grant-refused" data-code={refusal.code}>
      <StateChip state="failure" label={refusal.verb === "allow" ? words.cantAllow : words.cantStop} />{" "}
      <span className="surface-token" data-chip="">{REFUSAL_TOKEN[refusal.code] ?? refusal.code}</span>
    </span>
  );
}

function GrantVerb({ grant, words }: { grant: Delegation | null | undefined; words: Words }) {
  const live = grant?.state === "LIVE";
  return (
    <Button variant="ghost" dense data-testid="grant-verb">
      {live ? words.stop : words.allow}
    </Button>
  );
}

function ProposedRemoteAccess({
  wire,
  words,
  refusals = {},
  receiptFacts = null,
}: {
  wire: Wire;
  words: Words;
  refusals?: Record<string, Refusal>;
  receiptFacts?: ReceiptFacts;
}) {
  const enabled = wire.enabled;
  const credentials = enabled ? wire.credentials : [];
  const delegations = wire.delegations ?? [];
  const activeCount = credentials.filter((c) => c.active).length;
  const totalCount = wire.credentials.length;
  const addressToken = enabled && wire.port ? `${wire.bind_host || "0.0.0.0"}:${wire.port}` : null;
  // PROPOSED: the ledger renders for any credential OR any delegation row;
  // delegation rows render whatever the remote switch says (the beat, :155).
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
                {countToken(activeCount, "ACTIVE", "ACTIVE")}
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
                <RefusalChip refusal={refusals[cred.identity]} words={words} />
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
                <Button variant="ghost" dense>Revoke</Button>
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
                <RefusalChip refusal={refusals[grant.identity]} words={words} />
                <span className="surface-token" data-chip data-muted>NO CREDENTIAL</span>
              </>}
              trailing={grant.state === "LIVE" ? <GrantVerb grant={grant} words={words} /> : undefined}
            />
          ))}
        </SurfaceLedger>
      ) : null}
      {receiptFacts ? (
        <SurfaceWell head="RECEIPT">
          <div className="grant-canvas-receipt" data-testid="grant-receipt">
            <StateChip state="success" label={receiptFacts.outcome} />
            <span className="surface-token" data-chip>{receiptFacts.act}</span>
            <span className="gadget-fact">{receiptFacts.identity}</span>
            <span className="surface-token" data-chip>BY OWNER</span>
            <span className="surface-token" data-chip data-muted>{receiptFacts.time}</span>
          </div>
        </SurfaceWell>
      ) : null}
      {enabled ? (
        <div className="prefs-issue-start">
          <Button variant="ghost" data-testid="issue-credential-btn">Issue credential</Button>
        </div>
      ) : null}
    </GadgetGroup>
  );
}

/** The Settings foot (PrefStatusBar's layout, settingsPrefs.tsx:646-656)
 *  with the proposed centre: the library Receipt of the last grant act. */
function Foot({ receipt, open }: { receipt: FootReceipt; open?: boolean }) {
  return (
    <SurfaceFooter verbs={<>
      <Button variant="ghost" dense className="prefs-back">« PREFS</Button>
      {receipt ? (
        <span data-testid="foot-receipt" data-open={open || undefined}>
          <Receipt
            status={receipt.status}
            label={receipt.label}
            timestamp={receipt.time}
            onInspect={() => undefined}
          />
        </span>
      ) : null}
    </>} />
  );
}

/* ── the boards ─────────────────────────────────────────────────────── */

const [DESK, SWEEP] = REAL.credentials;
const G = (state: GrantState, id = "deskdeleg_3f9a"): Delegation => ({ state, grant_id: id, expires_at: null });

function boardFor(name: string, words: Words): { body: ReactNode; foot: ReactNode; label: string } {
  const withGrant = (grant: Delegation | null): Wire => ({
    ...REAL,
    credentials: [{ ...DESK, delegation: grant }, { ...SWEEP, delegation: null }],
  });
  switch (name) {
    case "1-never":
      return {
        label: "1 · No grant ever",
        body: <ProposedRemoteAccess wire={withGrant(null)} words={words} />,
        foot: <Foot receipt={null} />,
      };
    case "2-live":
      return {
        label: "2 · Grant live",
        body: <ProposedRemoteAccess wire={withGrant(G("LIVE"))} words={words} />,
        foot: <Foot receipt={{ status: "ok", label: words.live, time: "14:05" }} />,
      };
    case "3-revoked":
      return {
        label: "3 · Grant stopped",
        body: <ProposedRemoteAccess wire={withGrant(G("REVOKED"))} words={words} />,
        foot: <Foot receipt={{ status: "ok", label: words.stopped, time: "14:07" }} />,
      };
    case "4-expired":
      return {
        label: "4 · Grant expired by clock, credential active",
        body: <ProposedRemoteAccess wire={withGrant(G("EXPIRED"))} words={words} />,
        foot: <Foot receipt={null} />,
      };
    case "5-orphan":
      return {
        label: "5 · Grant live, no credential (remote ON)",
        body: (
          <ProposedRemoteAccess
            wire={{
              ...REAL,
              credentials: [{ ...SWEEP, delegation: null }],
              delegations: [{ identity: "desk-agent", ...G("LIVE") }],
              active_count: 1,
              total_count: 1,
            }}
            words={words}
          />
        ),
        foot: <Foot receipt={null} />,
      };
    case "5b-orphan-off":
      return {
        label: "5b · Grant live, no credential (remote OFF)",
        body: (
          <ProposedRemoteAccess
            wire={{
              ...REAL,
              enabled: false,
              credentials: [],
              delegations: [{ identity: "desk-agent", ...G("LIVE") }],
              active_count: 0,
              total_count: 0,
            }}
            words={words}
          />
        ),
        foot: <Foot receipt={null} />,
      };
    case "5c-orphan-expired":
      return {
        label: "5c · No credential, grant past its expiry",
        body: (
          <ProposedRemoteAccess
            wire={{
              ...REAL,
              credentials: [{ ...SWEEP, delegation: null }],
              delegations: [{ identity: "desk-agent", ...G("EXPIRED") }],
              active_count: 1,
              total_count: 1,
            }}
            words={words}
          />
        ),
        foot: <Foot receipt={null} />,
      };
    case "6-refused":
      return {
        label: "6 · Grant and stop refused",
        body: (
          <ProposedRemoteAccess
            wire={withGrant(G("REVOKED"))}
            words={words}
            refusals={{
              "desk-agent": { verb: "stop", code: "desk_delegation_required" },
              "sweep-runner": { verb: "allow", code: "owner_principal_required" },
            }}
          />
        ),
        foot: <Foot receipt={{ status: "danger", label: "REFUSED", time: "14:09" }} />,
      };
    case "7-empty":
      return {
        label: "7 · Last row gone, receipt still readable",
        body: (
          <ProposedRemoteAccess
            wire={{ ...REAL, credentials: [], delegations: [], active_count: 0, total_count: 0 }}
            words={words}
            receiptFacts={{ outcome: "SUCCEEDED", act: words.stopped, identity: "desk-agent", time: "SEP 25 14:07" }}
          />
        ),
        foot: <Foot receipt={{ status: "ok", label: words.stopped, time: "14:07" }} open />,
      };
    default:
      return {
        label: "0 · Today (the real module, the real wire)",
        body: <RemoteAccessModule />,
        foot: <Foot receipt={null} />,
      };
  }
}

function SettingsBody({ body, foot }: { body: ReactNode; foot: ReactNode }) {
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
