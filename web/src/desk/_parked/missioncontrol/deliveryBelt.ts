// PARKED 20261109 (lane subtract/mission-control): the delivery read model projected
// into the Mission control belt's repo rows. Parked from desk/delivery.ts with the belt.
// ── compatibility selectors (§10/§14) ──────────────────────────────
// The belt (MissionControlConveyor) and its direct verbs keep working by
// reading the SAME delivery read model through these projections into the
// legacy McRepo/McStory shapes. The compatibility names stay internal; the
// belt renders exactly what it always did, now over one store.
import type {
  McPhase,
  McProject,
  McRepo,
  McRepoStatus,
  McStory,
} from "./missioncontrol";

/** Map the one freshness enum onto the belt's four-value repo status. */
function beltRepoStatus(status: SourceStatus): McRepoStatus {
  switch (status) {
    case "live":
      return "live";
    case "incompatible":
      return "compatibility";
    case "unavailable":
    case "unauthorized":
      return "unavailable";
    default:
      return "unreachable";
  }
}

function beltProject(p: DeliveryProject): McProject {
  const phase = (ph: DeliveryPhase): McPhase => ({
    number: ph.number,
    title: ph.title,
    status: ph.status === "closed" ? "closed" : "open",
    storiesDone: ph.storiesDone,
    storiesTotal: ph.storiesTotal,
  });
  return {
    slug: p.slug,
    prefix: p.prefix,
    currentPhase: p.currentPhase ? phase(p.currentPhase) : null,
    nextStoryId: p.nextStoryId,
    phases: p.phases.map(phase),
    stories: p.stories.map(
      (s): McStory => ({
        storyId: s.storyId,
        title: s.title,
        status: s.status,
        phase: s.phase,
        evidenceExists: s.evidenceExists,
      }),
    ),
    warnings: p.warnings,
  };
}

/** The delivery read model projected into the belt's repo rows. */
export function deliveryBeltRepos(sources: DeliverySource[]): McRepo[] {
  return sources.map((s) => ({
    name: s.label,
    path: s.sourceId,
    status: beltRepoStatus(s.status),
    detail: s.detail,
    projects: s.status === "live" ? s.projects.map(beltProject) : [],
    receipts: "unknown" as const,
    prs: [],
  }));
}

