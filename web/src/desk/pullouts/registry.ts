/** Kind-keyed pullout content registry (HS-117-15).
 * The `satisfies` gate ensures compile-time completeness —
 * adding a new PrimitiveKind without a registry entry is a type error. */
import type { PrimitiveKind } from "../../lib/primitives";
import type { PulloutContent } from "./types";
import { MeetingPullout } from "./MeetingPullout";
import { ArtifactPullout } from "./ArtifactPullout";
import { NotePullout } from "./NotePullout";
import { KbPullout } from "./KbPullout";
import { DecisionPullout } from "./DecisionPullout";
import { RecipePullout } from "./RecipePullout";
import { ChainPullout } from "./ChainPullout";
import { WorkflowPullout } from "./WorkflowPullout";
import { CoderPullout } from "./CoderPullout";
import { DirectoryPullout } from "./DirectoryPullout";

export const PULLOUT_CONTENT: Record<PrimitiveKind, PulloutContent | null> = {
  meeting: MeetingPullout,
  artifact: ArtifactPullout,
  note: NotePullout,
  kb: KbPullout,
  decision: DecisionPullout,
  recipe: RecipePullout,
  chain: ChainPullout,
  workflow: WorkflowPullout,
  coder: CoderPullout,
  directory: DirectoryPullout,
  project: null,
  repository: null,
  roadmap: null,
  story: null,
  workbench: null,
  game: null,
  layout: null,
} satisfies Record<PrimitiveKind, PulloutContent | null>;
