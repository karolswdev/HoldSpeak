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
  DeskIcon,
  EgressChip,
  FilterTokens,
  IconGrid,
  LampGadget,
  ObjectList,
  SurfaceFooter,
  SurfaceState,
  objectSprite,
  type ObjectSort,
  type ObjectSortKey,
} from "../surface";
import { DeskWindowFrame } from "../components/DeskWindow";
import { useAgentFlights } from "../agentFlights";
import { AGENT_HOST, AGENT_INSTALL, needsHooks, type AgentId } from "../firstrun/agentsStep";
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
  if (member?.detect && failure && failedFor === member.detect.id) {
    const agent = member.detect.id;
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
  return null;
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
      onClose={() => useConductor.getState().closeWindow()}
    >
      <div className="desk-pullout-body drawer-body" data-testid="conductor-window">
        <div className="drawer-scroll">
          <div className="drawer-head">
            <div className="drawer-facts" data-testid="conductor-head">
              {failed.map((f) => (
                <span key={f.part} className="drawer-fact" data-tone="fail" data-testid="conductor-not-read">
                  {f.part} · <b>NOT READ</b>
                  {f.token ? ` · ${f.token}` : ""}
                </span>
              ))}
              {/* `2 AT WORK · 1 ASK · 3 OF 3`: the ask is a lamp (it needs him). */}
              {words.map((w) =>
                w.endsWith(" ASK") ? (
                  <LampGadget key={w} label={w} on tone="ask" />
                ) : (
                  <span key={w} className="drawer-fact">
                    <b>{w}</b>
                  </span>
                ),
              )}
            </div>
            <span className="drawer-head-verbs">
              {failed.length ? (
                <Button dense variant="ghost" onClick={retry}>
                  Retry
                </Button>
              ) : null}
              <FilterTokens
                label="Conductor view"
                value={view}
                onChange={(next) => useDesk.getState().setZoneViewPref(PREF_KEY, { view: next as ConductorView })}
                options={[
                  { value: "icons", label: "Icons" },
                  { value: "list", label: "List" },
                ]}
              />
            </span>
          </div>
          {loading ? (
            <SurfaceState loading />
          ) : !members.length && failed.length ? null : !members.length ? (
            <SurfaceState empty emptyLabel="No agent found" />
          ) : view === "icons" ? (
            <IconGrid label="Conductor" onClear={() => setSelectedId(null)}>
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
        </div>
      </div>
      <SurfaceFooter
        egress={selected?.role === "live" ? <EgressChip label={AGENT_HOST[selected.agent as AgentId] ?? AGENT_HOST.claude} scope="cloud" /> : null}
        className="cw-footer"
        receipt={<MemberReceipt member={selected} />}
        verbs={<MemberVerbs member={selected} onInfo={() => info(selected)} />}
      />
    </DeskWindowFrame>
  );
}
