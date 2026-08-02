// Mission control on the Desk (HS-82-03/04) — the rails panel.
//
// A fixture at the foot of the desk: one belt per rails project,
// phases as segments, the current phase's stories as the items
// riding it, the next actionable story wearing the desk's one
// accent. HS-111-06 (audit §3.1): the attention ladder is the law
// here — needs-you sessions are the ONLY individually rendered
// off-belt layer (steady inverted video, nothing blinks); the rest
// of the registry folds into per-agent census token lines with the
// full roster behind a folded well; events tick in a bounded ledger
// with gate refusals first-class. Repos that are unreachable or
// schema-drifted render their honest state — never an empty belt
// pretending the rails are idle.
// Design: docs/internal/MISSION_CONTROL_DESK.md §2–§3.
import { useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  McEvent,
  McProject,
  McRepo,
  McSession,
  POLL_MS,
  gateLightFor,
  isBeltFrame,
  offBeltSessions,
  sessionsByStory,
  useMissionControl,
} from "../missioncontrol";
import { isCoderFrame, useSteering } from "../steering";
import { useProjections } from "../projections";
import {
  ConfirmVerb,
  SurfaceCode,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceWell,
} from "../surface/Surface";
import { FoldGadget, GadgetRow, MxRadio } from "../surface/gadgets";

const FLIP_STATUSES = ["backlog", "ready", "in-progress", "blocked", "done"];

/** Honest repo states as axis-named tokens, never a sentence. */
function repoStateToken(value: string): string {
  const tokens: Record<string, string> = {
    unreachable: "REPO UNREACHABLE",
    schema_drift: "REPO SCHEMA MISMATCH",
    unauthorized: "REPO UNAUTHORIZED",
  };
  return tokens[value] || `REPO ${value.replace(/_/g, " ").toUpperCase()}`;
}

interface PickTarget {
  repo: string;
  project: string;
  story: string;
}

/** The on-belt pin: a mono token riding its story cell — the agent's
 * name, NEEDS YOU tone when awaiting, inverted video when armed.
 * The emoji species died here (audit B2). */
function SessionPin({
  session,
  manual,
}: {
  session: McSession;
  manual?: boolean;
}) {
  const armedUntil = useSteering((s) => s.armedKeys[session.key]);
  const armed = Boolean(armedUntil && armedUntil > Date.now());
  return (
    <button
      type="button"
      className={
        "desk-mc-pin" +
        (session.awaitingResponse ? " awaiting" : "") +
        (session.stale ? " stale" : "") +
        (armed ? " armed" : "") +
        (manual ? " manual" : "")
      }
      title={
        `${session.key}: watch live` +
        (manual ? "; manually pinned (not the correlator's verdict)" : "") +
        (session.stale ? " (stale)" : "")
      }
      onClick={(e) => {
        e.stopPropagation(); // the pin attaches; the story span picks
        useSteering.getState().openSession(session.key);
      }}
    >
      ⌁{session.agent}
      {session.awaitingResponse ? " NEEDS YOU" : ""}
    </button>
  );
}

function PhaseBelt({
  project,
  pins,
  manualPins,
  repoName,
  picked,
  onPick,
}: {
  project: McProject;
  pins: Record<string, McSession[]>;
  manualPins: Record<string, McSession[]>;
  repoName: string;
  picked: PickTarget | null;
  onPick: (t: PickTarget | null) => void;
}) {
  const current = project.currentPhase;
  const beltStories = current
    ? project.stories.filter((s) => s.phase === current.number)
    : [];
  return (
    <div className="desk-mc-project">
      <div className="desk-mc-phases">
        <span className="desk-mc-slug">{project.slug}</span>
        {project.phases.map((p) => (
          <span
            key={p.number}
            className={
              "desk-mc-phase" +
              (p.status === "closed" ? " closed" : "") +
              (current && p.number === current.number ? " current" : "")
            }
            title={`${p.title}: ${p.storiesDone}/${p.storiesTotal}`}
          >
            {p.number}
          </span>
        ))}
        {project.warnings > 0 && (
          <span className="desk-mc-warn" title="roadmap warnings">
            ⚠ {project.warnings}
          </span>
        )}
      </div>
      <div className="desk-mc-belt">
        {beltStories.map((s) => (
          <span
            key={s.storyId}
            className={
              "desk-mc-story st-" +
              s.status.replace(/[^a-z-]/g, "") +
              (s.storyId === project.nextStoryId ? " next" : "") +
              (picked && picked.story === s.storyId ? " picked" : "")
            }
          >
            <button
              type="button"
              className="desk-mc-story-pick"
              title={
                `${s.title} [${s.status}]` +
                (s.evidenceExists ? " ·evidence" : "")
              }
              onClick={() =>
                onPick(
                  picked && picked.story === s.storyId
                    ? null
                    : {
                        repo: repoName,
                        project: project.slug,
                        story: s.storyId,
                      },
                )
              }
            >
              {s.storyId}
            </button>
            {s.evidenceExists && (
              <button
                type="button"
                className="desk-mc-evidence-open"
                title="open the evidence in place"
                onClick={(ev) => {
                  ev.stopPropagation();
                  void useMissionControl
                    .getState()
                    .openEvidence(repoName, project.slug, s.storyId);
                }}
              >
                ✓
              </button>
            )}
            {(pins[s.storyId] || []).map((sess) => (
              <SessionPin key={sess.key} session={sess} />
            ))}
            {(manualPins[s.storyId] || []).map((sess) => (
              <SessionPin key={"m-" + sess.key} session={sess} manual />
            ))}
          </span>
        ))}
      </div>
    </div>
  );
}

/** The lane-head station lights (HS-86-04): PR, CI, gate — receipts
 * only; each light is absent when its receipt is. */
function StationLights({ repo, events }: { repo: McRepo; events: McEvent[] }) {
  const gate = gateLightFor(events, repo.name);
  return (
    <span className="desk-mc-lights">
      {repo.receipts === "live" && repo.prs.length > 0 && (
        <a
          className="desk-mc-light pr"
          href={repo.prs[0].url}
          target="_blank"
          rel="noreferrer"
          title={repo.prs.map((p) => `#${p.number} ${p.title}`).join("\n")}
        >
          ⛓ {repo.prs.length}
        </a>
      )}
      {repo.receipts === "live" && repo.prs.length > 0 && (
        <span
          className={"desk-mc-light ci-" + repo.prs[0].ci}
          title={`CI on #${repo.prs[0].number} (${repo.prs[0].branch})`}
        >
          ●
        </span>
      )}
      {repo.receipts === "unavailable" && (
        <span className="desk-mc-light off" title="gh receipts unavailable">
          ⛓ ∅
        </span>
      )}
      {gate.state === "pass" && (
        <span className="desk-mc-light gate-pass" title="last gate: pass">
          ▣
        </span>
      )}
      {gate.state === "refusal" && (
        <span className="desk-mc-light gate-refusal" title="last gate: refusal">
          ▣ ✕ {gate.rule}
        </span>
      )}
    </span>
  );
}

function RepoBlock({
  repo,
  pins,
  manualPins,
  picked,
  onPick,
  events,
}: {
  repo: McRepo;
  pins: Record<string, McSession[]>;
  manualPins: Record<string, McSession[]>;
  picked: PickTarget | null;
  onPick: (t: PickTarget | null) => void;
  events: McEvent[];
}) {
  if (repo.status !== "live") {
    return (
      <div className="desk-mc-honest">
        <span className="desk-mc-slug">{repo.name}</span>
        <span className="surface-token" data-tone="danger">
          ✕ {repoStateToken(repo.status)}
        </span>
        {repo.detail && (
          <span className="surface-token">{repo.detail}</span>
        )}
      </div>
    );
  }
  return (
    <>
      <div className="desk-mc-repo-head">
        <span className="desk-mc-repo-name">{repo.name}</span>
        <StationLights repo={repo} events={events} />
      </div>
      {repo.projects.map((p) => (
        <PhaseBelt
          key={repo.name + p.slug}
          project={p}
          pins={pins}
          manualPins={manualPins}
          repoName={repo.name}
          picked={picked}
          onPick={onPick}
        />
      ))}
    </>
  );
}

/** The filed object, opened in place (HS-86-04) — the SurfaceWell
 * species inside the panel, never a modal, never a route away. */
function EvidencePanel() {
  const evidence = useMissionControl((s) => s.evidence);
  const evidenceDetail = useMissionControl((s) => s.evidenceDetail);
  const { closeEvidence } = useMissionControl.getState();
  if (evidenceDetail) {
    return (
      <div className="desk-mc-evidence">
        <span className="desk-arm-refusal">✕ {evidenceDetail}</span>
        <Button dense variant="ghost" onClick={closeEvidence}>
          Close
        </Button>
      </div>
    );
  }
  if (!evidence) return null;
  return (
    <div className="desk-mc-evidence">
      <SurfaceWell
        head={
          <>
            <span className="surface-token">{`EVIDENCE ${evidence.storyId}`}</span>
            <span className="desk-mc-evidence-path">{evidence.path}</span>
            <Button dense variant="ghost" onClick={closeEvidence}>
              Close
            </Button>
          </>
        }
      >
        {/* HS-111-07 — evidence wire wears the well's own code grammar. */}
        <div className="desk-mc-evidence-body">
          <SurfaceCode>{evidence.text}</SurfaceCode>
        </div>
      </SurfaceWell>
    </div>
  );
}

/** The receipt slab: the proposal's fate in the two-step flip leg.
 * Wire untouched — proposeFlip/decide byte-identical. */
function ProposalCard() {
  const proposal = useMissionControl((s) => s.proposal);
  const proposalError = useMissionControl((s) => s.proposalError);
  const { decide, dismissProposal } = useMissionControl.getState();
  if (proposalError) {
    return (
      <div className="desk-mc-proposal failed">
        <span className="desk-arm-refusal">✕ {proposalError}</span>
        <Button dense variant="ghost" onClick={dismissProposal}>
          Dismiss
        </Button>
      </div>
    );
  }
  if (!proposal) return null;
  if (proposal.status === "proposed") {
    return (
      <div className="desk-mc-proposal">
        <span className="surface-token" data-tone="warn">
          PROPOSED
        </span>
        <span className="desk-mc-preview">{proposal.preview}</span>
        <Button dense onClick={() => void decide("approved")}>
          Approve
        </Button>
        <Button dense variant="ghost" onClick={() => void decide("rejected")}>
          Reject
        </Button>
      </div>
    );
  }
  if (proposal.status === "failed") {
    return (
      <div className="desk-mc-proposal failed">
        <span className="desk-arm-refusal">
          ✕ Status change failed. {proposal.error}
        </span>
        <Button dense variant="ghost" onClick={dismissProposal}>
          Dismiss
        </Button>
      </div>
    );
  }
  return (
    <div className="desk-mc-proposal">
      <span className="surface-token" data-tone="ok">
        {proposal.status === "executed"
          ? "EXECUTED"
          : proposal.status.toUpperCase()}
      </span>
      <Button dense variant="ghost" onClick={dismissProposal}>
        Dismiss
      </Button>
    </div>
  );
}

/** Manually-pinned sessions grouped by their pinned story (HS-87-05),
 * skipping any already correlated there — a manual pin never disguises
 * itself as the correlator's verdict, and a session gone from the
 * registry drops (the pin re-asserts when it returns). */
export function manualPinsByStory(
  sessions: McSession[],
  pins: Record<string, string>,
  correlated: Record<string, McSession[]>,
): Record<string, McSession[]> {
  const map: Record<string, McSession[]> = {};
  for (const [key, storyId] of Object.entries(pins)) {
    const sess = sessions.find((s) => s.key === key);
    if (!sess) continue;
    if ((correlated[storyId] || []).some((c) => c.key === key)) continue;
    (map[storyId] ||= []).push(sess);
  }
  return map;
}

export interface AgentCensus {
  agent: string;
  total: number;
  /** Bucket token -> count (IDLE folds stale; the correlator's own
   * bucket words otherwise, uppercased). */
  buckets: Array<{ token: string; count: number }>;
  sessions: McSession[];
}

/** HS-111-06 — the census fold (audit §3.1): off-belt, non-awaiting
 * sessions collapse into one token line per agent. Pure and additive:
 * the bucket rules (`offBeltSessions`, correlation verdicts) are
 * untouched — this only counts them. */
export function censusByAgent(sessions: McSession[]): AgentCensus[] {
  const byAgent = new Map<string, McSession[]>();
  for (const s of offBeltSessions(sessions)) {
    if (s.awaitingResponse) continue; // the needs-you layer renders these
    const agent = s.agent || "unknown";
    const list = byAgent.get(agent) || [];
    list.push(s);
    byAgent.set(agent, list);
  }
  return [...byAgent.entries()]
    .sort((a, b) => b[1].length - a[1].length)
    .map(([agent, list]) => {
      const counts = new Map<string, number>();
      for (const s of list) {
        const token = s.stale
          ? "IDLE"
          : s.correlation.replace(/_/g, " ").toUpperCase() || "UNKNOWN";
        counts.set(token, (counts.get(token) || 0) + 1);
      }
      return {
        agent,
        total: list.length,
        buckets: [...counts.entries()]
          .sort((a, b) => b[1] - a[1])
          .map(([token, count]) => ({ token, count })),
        sessions: list,
      };
    });
}

/** The needs-you cells + the census lines (audit §3.1): the only loud
 * layer is steady inverted video; the flood is a count. */
function OffBeltPanel({ sessions }: { sessions: McSession[] }) {
  const offBelt = offBeltSessions(sessions);
  const needsYou = offBelt.filter((s) => s.awaitingResponse);
  const census = censusByAgent(sessions);
  if (!offBelt.length) return null;
  return (
    <div className="desk-mc-sessions">
      {needsYou.map((s) => (
        <button
          key={s.key}
          type="button"
          className="desk-mc-needs"
          title={`${s.key}: ${s.lastAssistantText.slice(0, 200)}`}
          onClick={() => useSteering.getState().openSession(s.key)}
        >
          NEEDS YOU · {s.agent} ·{" "}
          {s.storyIds[0] || s.key.split(":", 2)[1]?.slice(0, 8) || s.key}
        </button>
      ))}
      {census.map((row) => (
        <FoldGadget
          key={row.agent}
          title={`${row.agent.toUpperCase()} ${row.total} · ${row.buckets
            .map((b) => `${b.token} ${b.count}`)
            .join(" · ")}`}
        >
          <SurfaceLedger cols="facts" count={`ROSTER ${row.total}`}>
            <ul className="surface-ledger-rows">
              {row.sessions.map((s) => (
                <SurfaceLedgerRow
                  key={s.key}
                  primary={s.key}
                  cells={
                    <span className="surface-ledger-cell">
                      <span className="surface-token">
                        {s.stale
                          ? "IDLE"
                          : s.correlation.replace(/_/g, " ").toUpperCase()}
                      </span>
                    </span>
                  }
                  onToggle={() => useSteering.getState().openSession(s.key)}
                />
              ))}
            </ul>
          </SurfaceLedger>
        </FoldGadget>
      ))}
    </div>
  );
}

/** The bounded event ledger (audit §3.1): the ticker grew a head count
 * and honest refusal tones — same species as the process monitor. */
function EventLedger({ events }: { events: McEvent[] }) {
  if (!events.length) return null;
  const refusals = events.filter((e) => e.event === "gate_refusal").length;
  return (
    <SurfaceLedger
      cols="events"
      count={`EVENTS ${events.length}${refusals ? ` · REFUSALS ${refusals}` : ""}`}
    >
      <ul className="surface-ledger-rows">
        {events.slice(0, 6).map((e, i) => {
          const time = e.ts.includes("T")
            ? e.ts.split("T")[1].replace("Z", "")
            : e.ts;
          const material = Object.entries(e.detail || {})
            .filter(([, v]) => v !== null && v !== undefined)
            .map(([k, v]) => `${k}=${v}`)
            .join(" ");
          const refusal = e.event === "gate_refusal";
          return (
            <SurfaceLedgerRow
              key={e.ts + e.event + i}
              time={time}
              primary={
                <span
                  className="surface-token"
                  data-tone={refusal ? "danger" : undefined}
                >
                  {refusal ? "✕ " : ""}
                  {e.event.replace(/_/g, " ").toUpperCase()}
                </span>
              }
              cells={
                <span className="surface-ledger-cell">
                  {[e.story, material].filter(Boolean).join(" · ")}
                </span>
              }
            />
          );
        })}
      </ul>
    </SurfaceLedger>
  );
}

export function MissionControlConveyor() {
  const repos = useMissionControl((s) => s.repos);
  const sessions = useMissionControl((s) => s.sessions);
  const events = useMissionControl((s) => s.events);
  const updatedAt = useMissionControl((s) => s.updatedAt);
  const open = useMissionControl((s) => s.open);
  const pinMap = useSteering((s) => s.manualPins);
  const attentionCount = useProjections((s) => s.ambientTotal);
  const { refresh, toggle } = useMissionControl.getState();
  const [picked, setPicked] = useState<PickTarget | null>(null);
  const [flipStatus, setFlipStatus] = useState("");

  useEffect(() => {
    const tick = () => {
      void refresh();
      void useSteering.getState().refreshGrants(); // the pins' armed rings
      void useProjections.getState().refreshAmbient();
    };
    tick();
    const timer = setInterval(tick, POLL_MS);
    // A `scope:"belt"` frame on the one bus moves the belt now; a
    // `scope:"coder"` frame moves the pins (HS-87-01/02). The poll
    // stays as the fallback heartbeat (HS-86-04).
    const onFrame = (e: Event) => {
      const frame = (e as CustomEvent).detail;
      if (isBeltFrame(frame)) void refresh();
      if (isCoderFrame(frame)) {
        tick();
        void useProjections.getState().refresh(true);
      }
    };
    document.addEventListener("hs-broadcast", onFrame);
    return () => {
      clearInterval(timer);
      document.removeEventListener("hs-broadcast", onFrame);
    };
  }, []);

  if (updatedAt === null || repos.length === 0) return null; // no rails on this desk

  const awaitingCount = sessions.filter((s) => s.awaitingResponse).length;

  if (!open) {
    return (
      <button className="desk-mc-tab" onClick={toggle} title="Rails panel">
        <span className="surface-token">RAILS</span>
        {awaitingCount > 0 ? (
          <span className="surface-token" data-tone="warn">
            {`NEEDS YOU ${awaitingCount}`}
          </span>
        ) : null}
        <span className="surface-token">{`RUNS ${sessions.length}`}</span>
        {attentionCount > 0 ? (
          <span className="surface-token">{`ATTN ${attentionCount}`}</span>
        ) : null}
      </button>
    );
  }

  const pins = sessionsByStory(sessions);
  const manualPins = manualPinsByStory(sessions, pinMap, pins);

  return (
    <div className="desk-mc">
      <div className="desk-mc-head">
        <span className="desk-mc-title">
          <span className="surface-token">RAILS</span>
          {awaitingCount > 0 ? (
            <span className="surface-token" data-tone="warn">
              {`NEEDS YOU ${awaitingCount}`}
            </span>
          ) : null}
          <span className="surface-token">{`RUNS ${sessions.length}`}</span>
        </span>
        {attentionCount > 0 ? (
          <Button
            dense
            variant="ghost"
            onClick={() => useProjections.getState().setOpen(true)}
          >
            ◎ {attentionCount}
          </Button>
        ) : null}
        <Button dense variant="ghost" aria-label="Collapse" onClick={toggle}>
          ▾
        </Button>
      </div>
      {repos.map((r) => (
        <RepoBlock
          key={r.name}
          repo={r}
          pins={pins}
          manualPins={manualPins}
          picked={picked}
          onPick={setPicked}
          events={events}
        />
      ))}
      <EvidencePanel />
      {picked && (
        <div className="desk-mc-flip">
          <GadgetRow label={`FLIP ${picked.story}`} wide>
            <MxRadio
              label={`Flip ${picked.story} to`}
              value={flipStatus}
              options={FLIP_STATUSES.map((st) => ({
                value: st,
                label: st.toUpperCase(),
              }))}
              onChange={setFlipStatus}
            />
            <ConfirmVerb
              label="PROPOSE"
              confirmLabel="PROPOSE?"
              disabled={!flipStatus}
              onConfirm={() => {
                if (!flipStatus) return;
                void useMissionControl
                  .getState()
                  .proposeFlip(
                    picked.repo,
                    picked.project,
                    picked.story,
                    flipStatus,
                  );
                setPicked(null);
                setFlipStatus("");
              }}
            />
          </GadgetRow>
        </div>
      )}
      <ProposalCard />
      <OffBeltPanel sessions={sessions} />
      <EventLedger events={events} />
    </div>
  );
}
