/**
 * The DeskOS Primitive Framework — the canonical web-side wire contract.
 *
 * One framework, every surface (desktop · iPad · web) implements THIS
 * identically. Every primitive is first-class and authorable on the web
 * Desk; primitives live on the desktop hub (the canonical store) and sync
 * through it. Wire format is snake_case JSON with ISO-8601 UTC stamps; the
 * camelCase below is the in-app TS shape, mapped at the API boundary by the
 * `fromWire*` adapters in `desk-client.ts`.
 *
 * Keep this in lock-step with the iPad/desktop object models — when the
 * shape changes here, it changes there. The `SyncClass` of each primitive
 * decides how the hub reconciles it.
 * Product labels come from `productLanguage.ts`; legacy discriminators remain
 * unchanged so existing hubs and clients keep syncing.
 */
import { productLabel } from "./productLanguage";

/** How the desktop hub reconciles a primitive across devices. */
export type SyncClass =
  | "content" // body-of-record (meeting, artifact, note)
  | "organization" // grouping (KB)
  | "capability" // a thing that can run (agent, chain, workflow)
  | "presence" // a live stream (coder)
  | "local"; // never leaves the device (game, layout)

/** The shared desk primitive kinds, plus the two local-only kinds. */
export type PrimitiveKind =
  | "meeting"
  | "artifact"
  | "note"
  | "decision"
  | "directory"
  | "kb"
  | "project"
  | "recipe"
  | "chain"
  | "workflow"
  | "coder"
  | "game"
  | "layout"
  | "roadmap"
  | "story"
  | "repository"
  | "workbench"
  | "intelligence";

/** How a primitive kind opens on the Desk (HS-117-16). */
export type SurfaceDeclaration =
  | { type: "pullout" }
  | { type: "window"; windowKey: string }
  | { type: "surface"; surfaceKey: string }
  | { type: "none" };

/** Static metadata for each kind — drives the type-legible Desk language. */
export interface PrimitiveDescriptor {
  kind: PrimitiveKind;
  label: string;
  /** Plural section heading on the Desk. */
  plural: string;
  syncClass: SyncClass;
  /** One-line "what is this" used in empty states + tooltips. */
  blurb: string;
  /** Lucide-style inline SVG path data (24×24 viewBox). */
  icon: string;
  /** Whether the web Desk can author this primitive today. */
  authorable: boolean;
  /** How this kind opens on the desk: pullout card, dedicated window,
   * whole-page surface, or none (HS-117-16). */
  surface: SurfaceDeclaration;
}

// ── content ────────────────────────────────────────────────────────────

export interface MeetingSegment {
  speaker?: string;
  text: string;
  startedAt?: string;
}

export interface Meeting {
  kind: "meeting";
  id: string;
  title: string;
  startedAt: string; // ISO-8601 UTC
  endedAt?: string | null;
  segments?: MeetingSegment[];
  segmentCount?: number;
  actionItemCount?: number;
  durationSeconds?: number | null;
  tags?: string[];
  intelStatus?: string | null;
}

/** 15 server artifact types — synthesized from a meeting's intel. */
export type ArtifactType = string;

export interface Artifact {
  kind: "artifact";
  id: string;
  meetingId?: string | null;
  artifactType: ArtifactType;
  title: string;
  bodyMarkdown: string;
  status: string;
  confidence?: number | null;
  sources?: unknown[];
}

/** NEW primitive — a free-standing markdown note, authored on any surface. */
export interface Note {
  kind: "note";
  id: string;
  title: string;
  bodyMarkdown: string;
  tags: string[];
  createdAt: string; // ISO-8601 UTC
  lastModified?: string | null;
}

export interface Decision {
  kind: "decision";
  id: string;
  title: string;
  status: "proposed" | "accepted" | "superseded" | "deprecated";
  deciders: string[];
  decidedAt?: string;
  contextMarkdown: string;
  decisionMarkdown: string;
  alternatives: Array<{ name: string; reason: string }>;
  consequencesMarkdown: string;
  supersededBy?: string;
  tags: string[];
  createdAt: string;
}

// ── organization ───────────────────────────────────────────────────────

/**
 * NEW primitive — a Directory (the iPad's "zone", a folder that holds
 * primitives). Its identity (`id, name, parentId`) and its MEMBERSHIP (which
 * primitives are filed in it) sync through the hub; its geometry/paint is
 * per-device layout and never canonical.
 */
export interface Directory {
  kind: "directory";
  id: string;
  name: string;
  nameNormalized: string;
  parentId?: string | null;
  /** Primitive ids filed in this directory (membership; syncs). */
  memberIds: string[];
  createdAt: string;
}

export interface KB {
  kind: "kb";
  id: string;
  name: string;
  memberIds: string[];
  createdAt: string;
  lastModified?: string | null;
}

/** A durable body of work whose relationships form its long memory. */
export interface Project {
  kind: "project";
  id: string;
  name: string;
  description: string;
  keywords: string[];
  teamMembers: string[];
  meetingCount: number;
  createdAt: string;
  updatedAt: string;
  lastModified?: string | null;
}

/** A registered local git source, opened as a Desk drawer. */
export interface Repository {
  kind: "repository";
  id: string;
  name: string;
  sourceId: string;
  branch: string;
  createdAt: string;
  lastModified?: string | null;
}

// ── capability ─────────────────────────────────────────────────────────

/** A saved Persona. The `recipe` discriminator is a compatibility wire name. */
export interface Persona {
  kind: "recipe";
  id: string;
  name: string;
  avatar: string;
  role: string;
  systemPrompt: string;
  userTemplate: string;
  tools: string[];
  kbId?: string | null;
  profileId?: string;
  capability?: unknown | null;
}

export interface Chain {
  kind: "chain";
  id: string;
  name: string;
  steps: string[]; // agentId[]
  capability?: unknown | null;
}

/** The canonical `graph_json` wire (HSM-22-01 golden fixtures): Swift
 * tagged-union node kinds + the two edge sets, snake_case keys. An OBJECT on
 * the wire — never a string (the HSM-22-03 type fix; the old
 * `graphJson?: string` drifted from every producer and parser). */
export interface WorkflowGraphJson {
  id: string;
  name: string;
  entry: string;
  nodes: Array<{
    id: string;
    kind: Record<string, Record<string, unknown>>;
    failure_policy?: string | null;
    runs_on?: string;
  }>;
  exec_edges: Array<{ from: { node: string; name: string }; to: string }>;
  data_edges: unknown[];
}

export interface Workflow {
  kind: "workflow";
  id: string;
  name: string;
  prompt?: string;
  graphJson?: WorkflowGraphJson;
  hasGraph?: boolean;
  capability?: unknown | null;
}

// ── presence / stream ──────────────────────────────────────────────────

export type CoderEventKind =
  | "userPrompt"
  | "assistant"
  | "tool"
  | "result"
  | "command"
  | "approval"
  | "notification"
  | "usage"
  | "ended";

export interface CoderEvent {
  kind: CoderEventKind;
  text?: string;
  at?: string;
}

export type CoderAgent = "claude" | "codex";

export interface Coder {
  kind: "coder";
  id: string;
  title?: string;
  agent: CoderAgent;
  sessionId: string;
  project?: string;
  model?: string;
  state: string; // running | waiting | idle | ended …
  /** Set when the coder is awaiting a spoken/typed answer. */
  question?: string | null;
  /** True when this is the selected reply target. */
  selected?: boolean;
  pinned?: boolean;
  stale?: boolean;
  events?: CoderEvent[];
}

// ── local-only ─────────────────────────────────────────────────────────

export interface Game {
  kind: "game";
  id: string;
  name: string;
}

/** Per-device card positions — NOT shared through the hub. */
export interface Layout {
  kind: "layout";
  id: string;
  positions: Record<string, { x: number; y: number }>;
}

/** A Delivery Workbench project surfaced on the desk (HS-117-01). */
export interface Roadmap {
  kind: "roadmap";
  id: string;
  title: string;
  slug: string;
  name: string;
  phaseCount: number;
  currentPhase: number;
  currentPhaseTitle: string;
  storiesDone: number;
  storiesTotal: number;
  health: string;
  issues: string[];
  nextStoryId: string | null;
}

/** A Delivery story card surfaced on the desk (HS-117-01). */
export interface Story {
  kind: "story";
  id: string;
  title: string;
  status: string;
  hasEvidence: boolean;
  phase: number;
}

/** An agent workbench — scheduled or interactive (HS-117-01). */
export interface Workbench {
  kind: "workbench";
  id: string;
  name: string;
  recipeId?: string | null;
  profileId?: string | null;
  resolverProfileId?: string | null;
  schedule?: unknown | null;
  scheduleEnabled?: boolean;
  itemCount?: number;
  pendingCount?: number;
  lastRun?: string | null;
  createdAt?: string;
  lastModified?: string | null;
}

/** The Desk-local singleton that opens the intelligence pullout. */
export interface Intelligence {
  kind: "intelligence";
  id: string;
  name: string;
}

export type Primitive = (
  | Meeting
  | Artifact
  | Note
  | Decision
  | Directory
  | KB
  | Project
  | Repository
  | Persona
  | Chain
  | Workflow
  | Coder
  | Game
  | Layout
  | Roadmap
  | Story
  | Workbench
  | Intelligence
) & { spriteState?: string | null };

/**
 * The descriptor table — the single source of the Desk's visual language.
 * Icons are 24×24 stroke paths (rendered with currentColor).
 */
export const PRIMITIVES = {
  meeting: {
    kind: "meeting",
    label: "Meeting",
    plural: "Meetings",
    syncClass: "content",
    blurb: "A captured conversation with transcript and intelligence.",
    icon: "M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H8l-5 4z",
    authorable: false,
    surface: { type: "pullout" },
  },
  artifact: {
    kind: "artifact",
    label: "Artifact",
    plural: "Artifacts",
    syncClass: "content",
    blurb:
      "A synthesized output (summary, decisions, actions …) from a meeting.",
    icon: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M9 13h6M9 17h6",
    authorable: false,
    surface: { type: "pullout" },
  },
  note: {
    kind: "note",
    label: "Note",
    plural: "Notes",
    syncClass: "content",
    blurb: "A free-standing markdown note you write anywhere.",
    icon: "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z",
    authorable: true,
    surface: { type: "pullout" },
  },
  decision: {
    kind: "decision",
    label: "Decision",
    plural: "Decisions",
    syncClass: "content",
    blurb: "Architecture decision record",
    icon: "M5 3h14v18H5zM8 8h8M8 12h8M8 16h5",
    authorable: true,
    surface: { type: "pullout" },
  },
  directory: {
    kind: "directory",
    label: productLabel("zone"),
    plural: productLabel("zone", true),
    syncClass: "organization",
    blurb: "A findable Desk placement for items, filed and synced.",
    // an open folder holding contents (24×24 stroke path)
    icon: "M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM3 11h18",
    authorable: true,
    surface: { type: "pullout" },
  },
  kb: {
    kind: "kb",
    label: productLabel("knowledge"),
    plural: productLabel("knowledge", true),
    syncClass: "organization",
    blurb: "A named collection of material used to ground answers.",
    icon: "M2 7l10-4 10 4-10 4zM2 7v10l10 4 10-4V7M2 12l10 4 10-4",
    authorable: true,
    surface: { type: "pullout" },
  },
  project: {
    kind: "project",
    label: "Project",
    plural: "Projects",
    syncClass: "organization",
    blurb: "A body of work with meetings, decisions, and cited memory.",
    icon: "M4 4h16v16H4zM8 2v4M16 2v4M8 10h8M8 14h5",
    authorable: false,
    surface: { type: "surface", surfaceKey: "open-project-memory" },
  },
  repository: {
    kind: "repository",
    label: "Repository",
    plural: "Repositories",
    syncClass: "organization",
    blurb: "A registered git repository with files, pull requests, and issues.",
    icon: "M4 3h16v18H4zM8 7h8M8 11h8M8 15h5",
    authorable: true,
    surface: { type: "window", windowKey: "RepositoryWindow" },
  },
  recipe: {
    kind: "recipe",
    label: productLabel("persona"),
    plural: productLabel("persona", true),
    syncClass: "capability",
    blurb: "Saved instructions, tools, and Knowledge for reusable work.",
    icon: "M12 8V4H8M4 8a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2zM9 13h.01M15 13h.01M9 17h6",
    authorable: true,
    surface: { type: "pullout" },
  },
  chain: {
    kind: "chain",
    label: productLabel("sequence"),
    plural: productLabel("sequence", true),
    syncClass: "capability",
    blurb:
      "An advanced linear Workflow whose output flows through ordered steps.",
    icon: "M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1",
    authorable: true,
    surface: { type: "pullout" },
  },
  workflow: {
    kind: "workflow",
    label: "Workflow",
    plural: "Workflows",
    syncClass: "capability",
    blurb: "Saved multi-step behavior that runs on selected material.",
    icon: "M6 3v12M18 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 15a9 9 0 0 0 9 9",
    authorable: true,
    surface: { type: "pullout" },
  },
  coder: {
    kind: "coder",
    label: productLabel("coder_session"),
    plural: productLabel("coder_session", true),
    syncClass: "presence",
    blurb: "A live Claude or Codex session. Answer the coder by voice.",
    icon: "M16 18l6-6-6-6M8 6l-6 6 6 6",
    authorable: false,
    surface: { type: "pullout" },
  },
  game: {
    kind: "game",
    label: "Game",
    plural: "Games",
    syncClass: "local",
    blurb: "A Desk game stored only on this device.",
    icon: "M6 12h4M8 10v4M15 13h.01M18 11h.01M17.32 5H6.68a4 4 0 0 0-3.98 3.59L2 14a3 3 0 0 0 5.4 1.8L8 15h8l.6.8A3 3 0 0 0 22 14l-.7-5.41A4 4 0 0 0 17.32 5z",
    authorable: false,
    surface: { type: "none" },
  },
  roadmap: {
    kind: "roadmap",
    label: "Roadmap",
    plural: "Roadmaps",
    syncClass: "organization",
    blurb: "Delivery Workbench project",
    icon: "M4 4h16v16H4zM7 8h10M7 12h7M7 16h10",
    authorable: false,
    surface: { type: "window", windowKey: "RoadmapWindow" },
  },
  story: {
    kind: "story",
    label: "Story",
    plural: "Stories",
    syncClass: "local",
    blurb: "Delivery story card",
    icon: "M6 3h12v18H6zM9 8h6M9 12h6M9 16h4",
    authorable: false,
    surface: { type: "none" },
  },
  workbench: {
    kind: "workbench",
    label: "Workbench",
    plural: "Workbenches",
    syncClass: "capability",
    blurb: "An agent workbench with a schedule, targets, and items.",
    icon: "M3 6h18M3 6v12a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6M3 6l3-3h12l3 3M8 10h8M8 14h5",
    authorable: true,
    surface: { type: "window", windowKey: "WorkbenchWindow" },
  },
  intelligence: {
    kind: "intelligence",
    label: "Intelligence",
    plural: "Intelligence",
    syncClass: "local",
    blurb: "A desk-wide brief, follow-through, and receipt view.",
    icon: "M4 4h16v16H4zM8 8h8M8 12h5M8 16h3",
    authorable: false,
    surface: { type: "pullout" },
  },
  layout: {
    kind: "layout",
    label: "Layout",
    plural: "Layouts",
    syncClass: "local",
    blurb: "Per-device card positions. Never synced.",
    icon: "M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z",
    authorable: false,
    surface: { type: "none" },
  },
} as const satisfies Record<PrimitiveKind, PrimitiveDescriptor>;

/** Exhaustive kind → concrete type map (HS-117-01). */
export type PrimitiveMap = {
  meeting: Meeting;
  artifact: Artifact;
  note: Note;
  decision: Decision;
  directory: Directory;
  kb: KB;
  project: Project;
  repository: Repository;
  recipe: Persona;
  chain: Chain;
  workflow: Workflow;
  coder: Coder;
  game: Game;
  layout: Layout;
  roadmap: Roadmap;
  story: Story;
  workbench: Workbench;
  intelligence: Intelligence;
};

/** Look up the surface declaration for a kind (HS-117-16). */
export function surfaceOf(kind: PrimitiveKind): PrimitiveDescriptor["surface"] {
  return PRIMITIVES[kind].surface;
}

/** Extract a display label from any primitive (title or name, whichever exists). */
export function primitiveLabel(p: Primitive): string {
  if ("title" in p && p.title) return p.title;
  if ("name" in p && p.name) return p.name;
  return p.id;
}

/** @deprecated Compatibility name for code that still mirrors the recipe wire. */
export type Agent = Persona;

/** Order of the Desk's primitive sections, grouped by sync class. */
export const DESK_GROUPS = [
  { label: "Content", kinds: ["meeting", "artifact", "note", "decision"] },
  { label: "Capabilities", kinds: ["recipe", "chain", "workflow", "workbench"] },
  { label: "Organization", kinds: ["directory", "kb", "project", "repository"] },
  { label: "Live", kinds: ["coder"] },
  { label: "Delivery", kinds: ["roadmap", "story"] },
  { label: "Local", kinds: ["game", "layout", "intelligence"] },
] as const satisfies readonly { readonly label: string; readonly kinds: readonly PrimitiveKind[] }[];

/** Compile-time proof that every PrimitiveKind appears in exactly one
 * DESK_GROUPS entry (HS-117-14). A missing kind is a type error here. */
type _DeskGroupKinds = (typeof DESK_GROUPS)[number]["kinds"][number];
type _AssertAllGrouped =
  [Exclude<PrimitiveKind, _DeskGroupKinds>] extends [never] ? true : never;
const _deskGroupsExhaustive: _AssertAllGrouped = true;
void _deskGroupsExhaustive;
