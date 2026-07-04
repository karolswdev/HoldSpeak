// Mission control on the Desk (HS-82-03) — the conveyor.
//
// A fixture at the foot of the desk: one belt per rails project,
// phases as segments, the current phase's stories as the items
// riding it, the next actionable story wearing the desk's one
// accent. Repos that are unreachable or schema-drifted render
// their honest state — never an empty belt pretending the rails
// are idle. Design: docs/internal/MISSION_CONTROL_DESK.md §2.
import { useEffect } from "react";
import {
  McProject,
  McRepo,
  POLL_MS,
  useMissionControl,
} from "../missioncontrol";

function PhaseBelt({ project }: { project: McProject }) {
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
            className={
              "desk-mc-story st-" +
              s.status.replace(/[^a-z-]/g, "") +
              (s.storyId === project.nextStoryId ? " next" : "")
            }
            title={`${s.title} [${s.status}]` + (s.evidenceExists ? " ·evidence" : "")}
          >
            {s.storyId}
            {s.evidenceExists ? " ✓" : ""}
          </span>
        ))}
      </div>
    </div>
  );
}

function RepoBlock({ repo }: { repo: McRepo }) {
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
      {repo.projects.map((p) => (
        <PhaseBelt key={repo.name + p.slug} project={p} />
      ))}
    </>
  );
}

export function MissionControlConveyor() {
  const repos = useMissionControl((s) => s.repos);
  const updatedAt = useMissionControl((s) => s.updatedAt);
  const open = useMissionControl((s) => s.open);
  const { refresh, toggle } = useMissionControl.getState();

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), POLL_MS);
    return () => clearInterval(timer);
  }, []);

  if (updatedAt === null || repos.length === 0) return null; // no rails on this desk

  if (!open) {
    return (
      <button className="desk-mc-tab" onClick={toggle} title="mission control">
        ▦ rails
      </button>
    );
  }

  return (
    <div className="desk-mc">
      <div className="desk-mc-head">
        <span className="desk-mc-title">▦ mission control</span>
        <button className="desk-mc-close" onClick={toggle} title="collapse">
          ▾
        </button>
      </div>
      {repos.map((r) => (
        <RepoBlock key={r.name} repo={r} />
      ))}
    </div>
  );
}
