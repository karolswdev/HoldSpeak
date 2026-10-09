/** PHILO-14 C4 — the Conductor drawer (ratified board A-4: the Conductor
 *  window, a drawer of agent icons; A-1: the drawer with its count and the
 *  automaton badge on the screen).
 *
 *  The drawer's frame and species (lane A2): the head (`2 AT WORK · 1 ASK`,
 *  `3 OF 3` at the launch cap, never a zero), Icons | List, the body as an
 *  IconGrid of DeskIcons or an ObjectList, the footer with the selection's
 *  verbs. The members are the agents (`members.ts`): ready, live, stale.
 *
 *  This window is where agents live: the Agents application and the
 *  Arrival's AGENTS section fold into it (PROPOSAL §3, Movement C).
 */
import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  AppHead,
  DeskIcon,
  EgressChip,
  FilterBar,
  IconGrid,
  ObjectList,
  StatusStrip,
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  objectSprite,
  type ObjectSort,
  type ObjectSortKey,
} from "../surface";
import { DeskWindowFrame } from "../components/DeskWindow";
import { useAgentFlights } from "../agentFlights";
import { AGENT_HOST, AGENT_INSTALL, AGENT_NAME, needsHooks, type AgentId, type AgentRow } from "../firstrun/agentsStep";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { useDesk } from "../store";
import { useCompactViewport } from "../useCompactViewport";
import { useOnCoderFrame, useOnDeskChanged } from "../useDeskChangedRefresh";
import { conductorHead, conductorMembers, headWords, type ConductorMember } from "./members";
import { answerMember, answers, openMember, stopMember, stops } from "./open";
import { CONDUCTOR_WINDOW_ID, useConductor } from "./store";
import "../drawer/drawer.css";
import "./conductor.css";

export type ConductorView = "icons" | "list";
const PREF_KEY = "conductor";

/** The reads, live while the window is open. */
function useConductorReads() {
  const state = useConductor();
  useEffect(() => {
    void useConductor.getState().readDetect();
    void useConductor.getState().readFlights();
  }, []);
  const reread = () => void useConductor.getState().readFlights();
  useOnCoderFrame(reread);
  useOnDeskChanged(reread);
  return state;
}

/** The receipt of a selected member: its Stop, its hooks install that the
 *  hub refused (with Retry), or a stale launch's close. */
export function MemberReceipt({ member }: { member: ConductorMember | null }) {
  const stop = useConductor((s) => (member ? s.stops[member.ref] : undefined));
  const failure = useConductor((s) => s.installFailure);
  const failedFor = useConductor((s) => s.installFailedAgent);
  const installing = useConductor((s) => s.installing);
  const done = useConductor((s) => s.installDone);
  if (failure && failedFor && (member?.detect ? failedFor === member.detect.id : !member)) {
    const agent = failedFor;
    return (
      <span className="drawer-receipt cw-receipt" data-tone="fail" role="status" data-testid="conductor-install-failed">
        HOOKS NOT INSTALLED · {failure}
        <Button dense variant="ghost" loading={installing === agent} onClick={() => void useConductor.getState().installHooks(agent)}>
          Retry
        </Button>
      </span>
    );
  }
  if (stop) {
    return (
      <span className="drawer-receipt cw-receipt" data-tone={stop.tone === "ok" ? undefined : "fail"} role="status" data-testid="conductor-stop-receipt">
        {stop.word} · {stop.text}
      </span>
    );
  }
  if (member?.receipt) {
    return <span className="drawer-receipt cw-receipt" data-testid="conductor-receipt">{member.receipt}</span>;
  }
  // PHILO-15 B35: the install's receipt, beside the agent it installed (or
  // with nothing selected, where the row verb was pressed).
  if (done && (!member || member.detect?.id === done.agent)) {
    return (
      <span className="drawer-receipt cw-receipt" role="status" data-testid="conductor-install-done">
        HOOKS INSTALLED · {AGENT_NAME[done.agent].toUpperCase()} · {done.at}
      </span>
    );
  }
  return null;
}

/** PHILO-15 B34: with nothing selected, every ready agent that lacks hooks
 *  has its own Install hooks verb (it was hidden until a selection). */
export function InstallHooksVerbs({ agents }: { agents: AgentRow[] }) {
  const installing = useConductor((s) => s.installing);
  return (
    <>
      {agents.filter(needsHooks).map((row) => (
        <Button
          key={row.id}
          dense
          variant="primary"
          data-testid="conductor-install-hooks"
          loading={installing === row.id}
          disabled={Boolean(installing) && installing !== row.id}
          onClick={() => void useConductor.getState().installHooks(row.id)}
        >
          {`Install hooks · ${AGENT_NAME[row.id]}`}
        </Button>
      ))}
    </>
  );
}

/** The verbs of one selected member (every verb names what it does). The
 *  Stop confirmation REPLACES the verb row (it is the only question then),
 *  and it is bound to the member pressed, whatever is selected after. */
export function MemberVerbs({ member, onInfo }: { member: ConductorMember | null; onInfo?: () => void }) {
  const installing = useConductor((s) => s.installing);
  const { copy, receipt } = useCopyReceipt();
  const [confirmFor, setConfirmFor] = useState<ConductorMember | null>(null);
  const [stopping, setStopping] = useState(false);
  useEffect(() => {
    if (!stopping) setConfirmFor((now) => (now && now.id !== member?.id ? null : now));
  }, [member?.id, stopping]);
  if (confirmFor) {
    const pressed = confirmFor;
    return (
      <>
        <Button dense variant="ghost" disabled={stopping} onClick={() => setConfirmFor(null)}>
          Back
        </Button>
        <Button
          dense
          variant="danger"
          loading={stopping}
          data-testid="conductor-stop-confirm"
          onClick={() => {
            setStopping(true);
            void stopMember(pressed).finally(() => {
              setStopping(false);
              setConfirmFor(null);
            });
          }}
        >
          Stop · sure? (ends the agent's session)
        </Button>
      </>
    );
  }
  const detect = member?.detect;
  return (
    <>
      {receipt}
      {onInfo ? (
        <Button dense variant="ghost" disabled={!member} onClick={onInfo}>
          Get Info
        </Button>
      ) : null}
      {detect && !detect.installed ? (
        <Button dense variant="secondary" aria-label={`Copy install: ${member!.name}`} onClick={() => void copy(AGENT_INSTALL[detect.id])}>
          Copy install
        </Button>
      ) : null}
      {detect && needsHooks(detect) ? (
        <Button
          dense
          variant="primary"
          loading={installing === detect.id}
          onClick={() => void useConductor.getState().installHooks(detect.id)}
        >
          Install hooks
        </Button>
      ) : null}
      {member && stops(member) ? (
        <Button dense variant="danger" data-testid="conductor-stop" onClick={() => setConfirmFor(member)}>
          Stop
        </Button>
      ) : null}
      {member && answers(member) ? (
        <Button dense variant="primary" onClick={() => answerMember(member)}>
          Answer
        </Button>
      ) : null}
      {member && member.role !== "ready" ? (
        <Button dense variant="secondary" onClick={() => openMember(member)}>
          Open
        </Button>
      ) : null}
    </>
  );
}

/** Phase 16: the Conductor's one big fact: `2 at work`; with none at work,
 *  the asks; with neither, the agents ready. Never a zero. */
export function headFact(head: { atWork: number; ask: number }, members: readonly ConductorMember[]): string {
  if (head.atWork > 0) return `${head.atWork} at work`;
  if (head.ask > 0) return `${head.ask} ${head.ask === 1 ? "asks" : "ask"}`;
  const ready = members.filter((m) => m.role === "ready").length;
  return ready > 0 ? `${ready} ready` : "No agent";
}

/** `ASKED 6 MIN AGO`, `ASKED 3 H AGO`, `ASKED OCT 5`; `ASKS` with no age. */
export function askedWord(when: string | undefined): string {
  if (!when) return "ASKS";
  return /\d+ (MIN|H)$/.test(when) ? `ASKED ${when} AGO` : `ASKED ${when}`;
}

/** The kind plate of an agent: `CC` Claude Code, `CX` Codex, `PI` pi. */
export function agentPlate(agent: string): string {
  if (agent === "claude") return "CC";
  if (agent === "codex") return "CX";
  if (agent === "pi") return "PI";
  return agent.slice(0, 3).toUpperCase() || "AGT";
}

export function ConductorWindow() {
  const reads = useConductorReads();
  const sessions = useAgentFlights((s) => s.sessions);
  const flights = useAgentFlights((s) => s.flights);
  const compact = useCompactViewport();
  const saved = useDesk((s) => s.zoneViewPrefs[PREF_KEY]?.view);
  const view: ConductorView = saved ?? (compact ? "list" : "icons");
  const [sort, setSort] = useState<ObjectSort>({ key: "name", dir: "asc" });
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const flightsKnown = reads.flightsState === "ok";
  const members = useMemo(
    () =>
      conductorMembers({
        detect: reads.detect?.agents ?? null,
        // Unknown stays unknown: a failed read lists no agent as gone.
        sessions: flightsKnown ? sessions : [],
        flights: flightsKnown ? flights : [],
        launchedAt: reads.launchedAt,
        history: flightsKnown ? reads.history : [],
        endedAt: reads.endedAt,
      }),
    [reads.detect, reads.launchedAt, reads.history, reads.endedAt, sessions, flights, flightsKnown],
  );
  const head = conductorHead(members, flightsKnown ? reads.launches : null);
  const selected = useMemo(() => members.find((m) => m.id === selectedId) ?? null, [members, selectedId]);
  useEffect(() => {
    if (selectedId && !selected) setSelectedId(null);
  }, [selectedId, selected]);

  const loading = (reads.flightsState === "idle" || reads.flightsState === "loading") && !members.length;
  const failed = [
    reads.detectState === "failed" ? { part: "AGENTS", token: reads.detectFailure } : null,
    reads.flightsState === "failed" ? { part: "SESSIONS", token: "" } : null,
  ].filter((f): f is { part: string; token: string } => f !== null);
  const retry = () => {
    if (reads.detectState === "failed") void useConductor.getState().readDetect();
    if (reads.flightsState === "failed") void useConductor.getState().readFlights();
  };
  const info = (member: ConductorMember | null) => {
    if (member) useConductor.getState().openInfo(member);
  };
  const onSort = (key: ObjectSortKey) =>
    setSort((now) => (now.key === key ? { key, dir: now.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }));
  const words = headWords(head);
  const byId = (id: string) => members.find((m) => m.id === id) ?? null;
  // Phase 16: the harnesses this desk has (installed agents), and The ask:
  // each live agent that asks (or holds a call), with its question.
  const harnesses = (reads.detect?.agents ?? []).filter((a) => a.installed).length;
  const asks = members
    .filter((m) => m.role === "live" && (m.live === "ask" || m.live === "held"))
    .map((member) => ({
      member,
      question: sessions.find((row) => row.key === member.sessionKey)?.question ?? "",
    }));

  return (
    <DeskWindowFrame
      id={CONDUCTOR_WINDOW_ID}
      title="Conductor"
      label="Conductor"
      kindWord="Drawer"
      glyph="◉"
      icon={<img className="drawer-winicon" src={objectSprite("conductor", "conductor")} alt="" />}
      className="desk-pullout drawer-window conductor-window"
      minW={340}
      minH={280}
      defaultW={760}
      defaultH={480}
      origin={reads.origin}
      open
      unmountOnMinimize
      // PHILO-16 (A1) §4.3: an agent that asks (or holds a call) lights the bar.
      lamp={head.ask > 0 ? "ask" : undefined}
      onClose={() => useConductor.getState().closeWindow()}
    >
      <div className="desk-pullout-body drawer-body" data-testid="conductor-window">
        <div className="drawer-scroll">
          {/* Phase 16 (the interior kit; the canvas window "Conductor"):
              AppHead → FilterBar → the IconGrid of agents → The ask. */}
          <AppHead fact={headFact(head, members)} data-testid="conductor-head">
            <StatusStrip
              items={[
                ...failed.map((f) => ({
                  key: `fail-${f.part}`,
                  lamp: "fail" as const,
                  text: `${f.part} ·`,
                  value: `NOT READ${f.token ? ` · ${f.token}` : ""}`,
                  testId: "conductor-not-read",
                })),
                // `2 AT WORK` is the fact; the ask is a lamp (it needs him).
                ...words.filter((w) => !w.endsWith(" AT WORK")).map((w) => ({
                  key: w,
                  lamp: w.endsWith(" ASK") ? ("ask" as const) : undefined,
                  text: w,
                })),
                harnesses > 0 ? { key: "harnesses", text: `${harnesses} ${harnesses === 1 ? "HARNESS" : "HARNESSES"}` } : null,
              ]}
            />
          </AppHead>
          <FilterBar
            label="Conductor view"
            data-testid="conductor-filter"
            value={view}
            onChange={(next) => useDesk.getState().setZoneViewPref(PREF_KEY, { view: next as ConductorView })}
            options={[
              { value: "icons", label: "Icons" },
              { value: "list", label: "List" },
            ]}
            trailing={failed.length ? (
              <Button dense variant="ghost" onClick={retry}>
                Retry
              </Button>
            ) : null}
          />
          {loading ? (
            <SurfaceState loading />
          ) : !members.length && failed.length ? null : !members.length ? (
            <SurfaceState empty emptyLabel="No agent found" />
          ) : view === "icons" ? (
            <IconGrid well label="Conductor" onClear={() => setSelectedId(null)}>
              {members.map((m) => (
                <DeskIcon
                  key={m.id}
                  id={m.id}
                  kind={m.kind}
                  name={m.name}
                  kindWord={m.kindWord}
                  sprite={m.sprite}
                  spriteSelected={m.spriteSelected}
                  selected={m.id === selectedId}
                  lamp={m.lamp ? { tone: m.lamp.tone, label: m.lamp.label } : undefined}
                  ariaExtra={m.receipt}
                  onSelect={() => setSelectedId(m.id)}
                  onOpen={() => openMember(m)}
                />
              ))}
            </IconGrid>
          ) : (
            <ObjectList
              label="Conductor"
              rows={members}
              sort={sort}
              onSort={onSort}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onOpen={(id) => {
                const m = byId(id);
                if (m) openMember(m);
              }}
            />
          )}
          {asks.length ? (
            <SurfaceSection label="The ask" data-testid="conductor-asks">
              <SurfaceLedger label="The ask" cols="kit">
                <ul className="surface-ledger-rows">
                  {asks.map(({ member, question }) => (
                    <SurfaceLedgerRow
                      key={member.id}
                      data-testid="conductor-ask-row"
                      kind={agentPlate(member.agent)}
                      kindTitle={member.kindWord}
                      primary={question || member.name}
                      meta={askedWord(member.when)}
                      metaTone="ask"
                      wrap
                      expands={false}
                      selected={member.id === selectedId}
                      lineLabel={`Select: ${member.name}`}
                      onToggle={() => setSelectedId(member.id)}
                    />
                  ))}
                </ul>
              </SurfaceLedger>
            </SurfaceSection>
          ) : null}
        </div>
      </div>
      <SurfaceFooter
        egress={selected?.role === "live" ? <EgressChip label={AGENT_HOST[selected.agent as AgentId] ?? AGENT_HOST.claude} scope="cloud" /> : null}
        className="cw-footer"
        receipt={<MemberReceipt member={selected} />}
        verbs={
          <>
            {selected ? null : <InstallHooksVerbs agents={reads.detect?.agents ?? []} />}
            <MemberVerbs member={selected} onInfo={() => info(selected)} />
          </>
        }
      />
    </DeskWindowFrame>
  );
}
