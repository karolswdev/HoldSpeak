/** Kind-keyed pullout content registry (HS-117-15).
 * The `satisfies` gate ensures compile-time completeness —
 * adding a new PrimitiveKind without a registry entry is a type error. */
import { createElement, lazy, Suspense } from "react";
import type { PrimitiveKind } from "../../lib/primitives";
import type { PulloutContent } from "./types";
import { SurfaceState } from "../surface";
import { watchChunk } from "../../runtime/freshBuild";
import { MeetingWindow } from "./MeetingWindow";
import { ArtifactPullout } from "./ArtifactPullout";
import { KbPullout } from "./KbPullout";
import { DecisionToReader } from "./DecisionToReader";
import { RecipePullout } from "./RecipePullout";
import { CoderPullout } from "./CoderPullout";
import { DirectoryPullout } from "./DirectoryPullout";
import { IntelligencePullout } from "./IntelligencePullout";
import { FallbackPullout } from "./FallbackPullout";
import { ThreadToAsk } from "./ThreadToAsk";
import { ProjectToRoom } from "./ProjectToRoom";
import { PeoplePullout } from "./PeoplePullout";

/** The note pullout is not on glass at first paint: it and its CodeMirror
 *  editor are their own chunk (measure 2026-11-08), loaded when a note opens,
 *  with the surface's loading face until it arrives. */
const NoteCore = lazy(watchChunk(() => import("./NotePullout").then((m) => ({ default: m.NotePullout }))));

const NotePullout: PulloutContent = (props) =>
  createElement(Suspense, { fallback: createElement(SurfaceState, { loading: true }) }, createElement(NoteCore, props));

/**
 * Pullout-capable kinds use their own content. Window and surface kinds are
 * redirected by `openPullout` before this registry renders; the fallback
 * keeps the registry exhaustive for kinds that deliberately have no detail.
 */
export const PULLOUT_CONTENT: Record<PrimitiveKind, PulloutContent> = {
  meeting: MeetingWindow,
  artifact: ArtifactPullout,
  note: NotePullout,
  kb: KbPullout,
  // The one decision face (2026-11-08): a decision opens its record in the
  // Decisions window reader; the Decision pullout is parked.
  decision: DecisionToReader,
  recipe: RecipePullout,
  // The Sequence and Workflow faces are parked (2026-11-08).
  chain: FallbackPullout,
  workflow: FallbackPullout,
  coder: CoderPullout,
  directory: DirectoryPullout,
  thread: ThreadToAsk,
  // W1-DOORS: a Project opens its Room; the fallback face is parked for it.
  project: ProjectToRoom,
  repository: FallbackPullout,
  roadmap: FallbackPullout,
  story: FallbackPullout,
  workbench: FallbackPullout,
  intelligence: IntelligencePullout,
  people: PeoplePullout,
  game: FallbackPullout,
  layout: FallbackPullout,
} satisfies Record<PrimitiveKind, PulloutContent>;

// Programs (2026-10-28): the pullout families whose object is the hub's,
// not a desk primitive (`pullout:program:<id>`). Pullout.tsx reads them first.
export { PULLOUT_FAMILIES } from "./families";
