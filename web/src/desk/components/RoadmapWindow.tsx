import { useEffect, useMemo, useState } from "react";
import { fetchRoadmap, type RoadmapDetail, type RoadmapPhase } from "../roadmap";
import { usePrimitiveDetail } from "../hooks/usePrimitiveDetail";
import { useDesk } from "../store";
import { SurfaceState } from "../surface/Surface";
import { SurfaceWings } from "../surface/wings";
import { DeskWindowFrame } from "./DeskWindow";
import "./RoadmapWindow.css";

const WINGS = [
  { id: "timeline", label: "Timeline" },
  { id: "stories", label: "Stories" },
  { id: "health", label: "Health" },
];
const STORY_ORDER = ["blocked", "in-progress", "ready", "backlog", "done"] as const;

function Status({ value }: { value: string }) {
  return <span className="desk-roadmap-status" data-status={value}>{value}</span>;
}

function PhaseRow({ phase, expanded, onToggle }: { phase: RoadmapPhase; expanded: boolean; onToggle: () => void }) {
  return (
    <li className="desk-roadmap-phase">
      <button type="button" className="desk-roadmap-phase-row" onClick={onToggle} aria-expanded={expanded}>
        <span className="desk-roadmap-chevron" aria-hidden="true">{expanded ? "▾" : "▸"}</span>
        <strong>PH {phase.number}</strong>
        <span className="desk-roadmap-phase-title" title={phase.title}>{phase.title}</span>
        <span className="desk-roadmap-count">{phase.storiesDone}/{phase.storiesTotal}</span>
        <Status value={phase.status} />
      </button>
      {expanded ? (
        <ul className="desk-roadmap-stories" aria-label={`Phase ${phase.number} stories`}>
          {phase.stories.map((story) => (
            <li key={story.id}>
              <span className="desk-roadmap-story-id">{story.id}</span>
              <span className="desk-roadmap-story-title" title={story.title}>{story.title}</span>
              {story.hasEvidence ? <span className="desk-roadmap-evidence" title="Evidence captured">▣</span> : null}
              <Status value={story.status} />
            </li>
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function RoadmapWindow({ slug, origin }: { slug: string; origin?: { x: number; y: number } | null }) {
  const [active, setActive] = useState("timeline");
  const detailHook = usePrimitiveDetail("roadmap", slug, fetchRoadmap);
  const detail = detailHook.data;
  const error = detailHook.error ?? "";
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  // Auto-expand the current phase when detail first arrives.
  useEffect(() => {
    if (detail) setExpanded(new Set([detail.currentPhase]));
  }, [detail]);

  const activePhase = useMemo(
    () => detail?.phases.find((phase) => phase.number === detail.currentPhase) ?? null,
    [detail],
  );
  const issueCount = detail?.healthIssues.length ?? detail?.issues.length ?? 0;
  const close = () => useDesk.getState().closeRoadmapWindow(slug);

  return (
    <DeskWindowFrame
      id={`roadmap:${slug}`}
      glyph="▤"
      label={`Roadmap ${detail?.name || slug}`}
      title={detail?.name || slug}
      minW={520}
      minH={360}
      open
      origin={origin}
      onClose={close}
      wings={<SurfaceWings wings={WINGS} active={active} onChange={setActive} />}
      className="desk-roadmap-window"
    >
      <div className="desk-roadmap-body">
        {detailHook.loading && !detail ? <SurfaceState loading /> : null}
        {error ? <SurfaceState error={error} /> : null}
        {detail && active === "timeline" ? (
          <ul className="desk-roadmap-phases">
            {detail.phases.map((phase) => (
              <PhaseRow
                key={phase.number}
                phase={phase}
                expanded={expanded.has(phase.number)}
                onToggle={() => setExpanded((current) => {
                  const next = new Set(current);
                  if (next.has(phase.number)) next.delete(phase.number); else next.add(phase.number);
                  return next;
                })}
              />
            ))}
          </ul>
        ) : null}
        {detail && active === "stories" ? (
          <div className="desk-roadmap-story-groups">
            {detail.nextStoryId ? <div className="desk-roadmap-next">WHAT'S NEXT <strong>{detail.nextStoryId}</strong></div> : null}
            {activePhase ? STORY_ORDER.map((status) => {
              const stories = activePhase.stories.filter((story) => story.status === status);
              if (!stories.length) return null;
              return <section key={status}><h4>{status}</h4><ul>{stories.map((story) => <li key={story.id}><span>{story.id}</span><span>{story.title}</span>{story.id === detail.nextStoryId ? <b>NEXT</b> : null}</li>)}</ul></section>;
            }) : <SurfaceState empty emptyLabel="No active phase" />}
          </div>
        ) : null}
        {detail && active === "health" ? (
          detail.healthIssues.length ? <ul className="desk-roadmap-health">{detail.healthIssues.map((issue, index) => <li key={`${issue.path}:${index}`} data-severity={issue.severity}><Status value={issue.severity} /><code>{issue.path || "roadmap"}</code><span>{issue.issue}</span></li>)}</ul> : <SurfaceState empty emptyLabel="0 issues" />
        ) : null}
      </div>
      <footer className="desk-roadmap-footer">
        <span>{issueCount} {issueCount === 1 ? "issue" : "issues"}</span>
        {detail?.nextStoryId ? <span className="desk-roadmap-next-chip">WHAT'S NEXT · {detail.nextStoryId}</span> : null}
      </footer>
    </DeskWindowFrame>
  );
}
