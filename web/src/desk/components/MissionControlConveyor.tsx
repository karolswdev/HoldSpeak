// Mission control on the Desk (HS-82-03/04) — the conveyor.
//
// A fixture at the foot of the desk: one belt per rails project,
// phases as segments, the current phase's stories as the items
// riding it, the next actionable story wearing the desk's one
// accent. Live agent sessions pin to the stories they are on
// (awaiting-response is the loudest signal on the desk); events
// tick underneath with gate refusals first-class. Repos that are
// unreachable or schema-drifted render their honest state — never
// an empty belt pretending the rails are idle.
// Design: docs/internal/MISSION_CONTROL_DESK.md §2–§3.
import { useEffect, useState } from "react";
import {
  McEvent,
  McProject,
  McRepo,
  McSession,
  POLL_MS,
  formatEvent,
  gateLightFor,
  isBeltFrame,
  offBeltSessions,
  sessionsByStory,
  useMissionControl,
} from "../missioncontrol";
import { isCoderFrame, useSteering } from "../steering";

const FLIP_STATUSES = ["backlog", "ready", "in-progress", "blocked", "done"];

interface PickTarget {
  repo: string;
  project: string;
  story: string;
}

function SessionPin({ session, manual }: { session: McSession; manual?: boolean }) {
  const armedUntil = useSteering((s) => s.armedKeys[session.key]);
  const armed = Boolean(armedUntil && armedUntil > Date.now());
  return (
    <span
      role="button"
      className={
        "desk-mc-pin" +
        (session.awaitingResponse ? " awaiting" : "") +
        (session.stale ? " stale" : "") +
        (armed ? " armed" : "") +
        (manual ? " manual" : "")
      }
      title={
        `${session.key} — watch live` +
        (manual ? " — manually pinned (not the correlator's verdict)" : "") +
        (session.awaitingResponse
          ? ` — awaiting a response: ${session.lastAssistantText.slice(0, 200)}`
          : "") +
        (session.stale ? " (stale)" : "")
      }
      onClick={(e) => {
        e.stopPropagation(); // the pin attaches; the story span picks
        useSteering.getState().openSession(session.key);
      }}
    >
      {session.awaitingResponse ? "🙋" : "🤖"}
      {session.agent}
    </span>
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
            title={`${p.title} — ${p.storiesDone}/${p.storiesTotal}`}
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
            role="button"
            className={
              "desk-mc-story st-" +
              s.status.replace(/[^a-z-]/g, "") +
              (s.storyId === project.nextStoryId ? " next" : "") +
              (picked && picked.story === s.storyId ? " picked" : "")
            }
            title={`${s.title} [${s.status}]` + (s.evidenceExists ? " ·evidence" : "")}
            onClick={() =>
              onPick(
                picked && picked.story === s.storyId
                  ? null
                  : { repo: repoName, project: project.slug, story: s.storyId },
              )
            }
          >
            {s.storyId}
            {s.evidenceExists && (
              <span
                role="button"
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
              </span>
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
        <span className={"desk-mc-state " + repo.status}>
          ✕ {repo.status}
        </span>
        {repo.detail && <span className="desk-mc-detail">{repo.detail}</span>}
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

/** The filed object, opened in place (HS-86-04) — a pull-out inside
 * the conveyor, never a modal, never a route away. */
function EvidencePanel() {
  const evidence = useMissionControl((s) => s.evidence);
  const evidenceDetail = useMissionControl((s) => s.evidenceDetail);
  const { closeEvidence } = useMissionControl.getState();
  if (evidenceDetail) {
    return (
      <div className="desk-mc-evidence">
        <span className="desk-mc-refusal">✕ {evidenceDetail}</span>
        <button className="desk-mc-btn" onClick={closeEvidence}>close</button>
      </div>
    );
  }
  if (!evidence) return null;
  return (
    <div className="desk-mc-evidence">
      <div className="desk-mc-evidence-head">
        <span className="desk-mc-evidence-path">{evidence.path}</span>
        <button className="desk-mc-btn" onClick={closeEvidence}>close</button>
      </div>
      <pre className="desk-mc-evidence-body">{evidence.text}</pre>
    </div>
  );
}

function ProposalCard() {
  const proposal = useMissionControl((s) => s.proposal);
  const proposalError = useMissionControl((s) => s.proposalError);
  const { decide, dismissProposal } = useMissionControl.getState();
  if (proposalError) {
    return (
      <div className="desk-mc-proposal failed">
        <span className="desk-mc-refusal">✕ {proposalError}</span>
        <button className="desk-mc-btn" onClick={dismissProposal}>dismiss</button>
      </div>
    );
  }
  if (!proposal) return null;
  if (proposal.status === "proposed") {
    return (
      <div className="desk-mc-proposal">
        <span className="desk-mc-preview">{proposal.preview}</span>
        <button className="desk-mc-btn approve" onClick={() => void decide("approved")}>
          Approve
        </button>
        <button className="desk-mc-btn" onClick={() => void decide("rejected")}>
          Reject
        </button>
      </div>
    );
  }
  if (proposal.status === "failed") {
    return (
      <div className="desk-mc-proposal failed">
        <span className="desk-mc-refusal">
          ✕ the rails refused: {proposal.error}
        </span>
        <button className="desk-mc-btn" onClick={dismissProposal}>dismiss</button>
      </div>
    );
  }
  return (
    <div className="desk-mc-proposal">
      <span className="desk-mc-executed">
        {proposal.status === "executed" ? "✓ executed" : proposal.status}
      </span>
      <button className="desk-mc-btn" onClick={dismissProposal}>dismiss</button>
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

export function MissionControlConveyor() {
  const repos = useMissionControl((s) => s.repos);
  const sessions = useMissionControl((s) => s.sessions);
  const events = useMissionControl((s) => s.events);
  const updatedAt = useMissionControl((s) => s.updatedAt);
  const open = useMissionControl((s) => s.open);
  const pinMap = useSteering((s) => s.manualPins);
  const { refresh, toggle } = useMissionControl.getState();
  const [picked, setPicked] = useState<PickTarget | null>(null);

  useEffect(() => {
    const tick = () => {
      void refresh();
      void useSteering.getState().refreshGrants(); // the pins' armed rings
    };
    tick();
    const timer = setInterval(tick, POLL_MS);
    // A `scope:"belt"` frame on the one bus moves the belt now; a
    // `scope:"coder"` frame moves the pins (HS-87-01/02). The poll
    // stays as the fallback heartbeat (HS-86-04).
    const onFrame = (e: Event) => {
      const frame = (e as CustomEvent).detail;
      if (isBeltFrame(frame)) void refresh();
      if (isCoderFrame(frame)) tick();
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
      <button className="desk-mc-tab" onClick={toggle} title="mission control">
        ▦ rails{awaitingCount > 0 ? ` 🙋${awaitingCount}` : ""}
      </button>
    );
  }

  const pins = sessionsByStory(sessions);
  const manualPins = manualPinsByStory(sessions, pinMap, pins);
  const offBelt = offBeltSessions(sessions);

  return (
    <div className="desk-mc">
      <div className="desk-mc-head">
        <span className="desk-mc-title">▦ mission control</span>
        <button className="desk-mc-close" onClick={toggle} title="collapse">
          ▾
        </button>
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
          <span className="desk-mc-flip-label">flip {picked.story} to</span>
          {FLIP_STATUSES.map((st) => (
            <button
              key={st}
              className="desk-mc-btn"
              onClick={() => {
                void useMissionControl
                  .getState()
                  .proposeFlip(picked.repo, picked.project, picked.story, st);
                setPicked(null);
              }}
            >
              {st}
            </button>
          ))}
        </div>
      )}
      <ProposalCard />
      {offBelt.length > 0 && (
        <div className="desk-mc-sessions">
          {offBelt.map((s) => (
            <span key={s.key} className="desk-mc-offbelt" title={s.key}>
              <SessionPin session={s} />
              <span className="desk-mc-bucket">{s.correlation.replace(/_/g, " ")}</span>
            </span>
          ))}
        </div>
      )}
      {events.length > 0 && (
        <div className="desk-mc-ticker">
          {events.slice(0, 6).map((e, i) => (
            <span
              key={e.ts + e.event + i}
              className={
                "desk-mc-event" + (e.event === "gate_refusal" ? " refusal" : "")
              }
            >
              {e.event === "gate_refusal" ? "✕ " : ""}
              {formatEvent(e)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
