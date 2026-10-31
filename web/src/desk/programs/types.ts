/* Programs (PROGRAMS-DESIGN-2026-10-28 §4, §9, §9b, §11): the hub's shapes,
 * as the faces read them. `GET /api/programs`, `GET /api/programs/{id}`,
 * the `program_changed` frame. The words a state reads (`state_word`) come
 * from the hub (`program_service.STEP_WORDS` / `PROGRAM_WORDS`); the faces
 * draw them through `stateWords`. */

export type ProgramState = "drafting" | "running" | "waiting" | "done" | "parked" | "failed";

export type StepState =
  | "planned" | "ready" | "briefed" | "working" | "waiting" | "limited" | "checking" | "check_failed"
  | "review" | "findings" | "pr_open" | "merge_ask" | "merged" | "done" | "parked" | "failed";

export type StationKey = "brief" | "work" | "check" | "review" | "pr" | "merge";

/** The desk's Control mode ladder (design §6, owner 2026-10-28): Secure ·
 *  Normal · YOLO. The desk's own policy wire says `safe` / `neutral`. */
export type Control = "secure" | "normal" | "yolo";

/** One engine decision, "Decided for you" (§6, §8, §9 item 3). */
export interface DecidedRow {
  id: number | string;
  at: string;
  step_id: string | null;
  /** The decision's kind and choice (`add_step` / `add`, `merge` / `merge`). */
  kind?: string | null;
  choice?: string | null;
  /** What was decided (`Merged PR #101 of step 1 (check green)`). */
  line: string;
  /** The rule, in muted words (`YOLO: the engine adds a missing step and says so`). */
  rule: string | null;
  /** It can still be undone (a merge cannot). */
  overturnable: boolean;
  /** When he overturned it; null while it stands. */
  overturned_at?: string | null;
  operation_id?: string | null;
  /** PG16: the proposed decision record this decision made (a Skip, a merge by rule). */
  decision_record_id?: string | null;
}

export interface ProgramCheckpoint {
  id: number | string;
  step_id: string;
  at: string;
  by: "agent" | "engine" | "owner";
  line: string;
  operation_id?: string | null;
  /** An engine decision's own fields (null on a plain checkpoint). */
  kind?: string | null;
  choice?: string | null;
  rule?: string | null;
  overturnable?: boolean;
  overturned_at?: string | null;
  /** PG16: the proposed decision record this checkpoint made. */
  decision_record_id?: string | null;
  /** PG20: the hidden ref this checkpoint pinned the step's worktree to
   *  (`refs/holdspeak/checkpoints/<step>/<n>`), its commit, or why not. */
  ref?: string | null;
  ref_commit?: string | null;
  pin_note?: string | null;
}

/** The program's Runs on engine (pi only): `null` for Claude Code / Codex. */
export interface ProgramEngine {
  id: string | null;
  /** `qwen3.8-27b on karol`. */
  label: string;
  /** `qwen` (the held word: `Ready · waiting for qwen`). */
  short: string;
  model?: string | null;
  /** No engine named: the desk's assignment for coding. */
  assignment?: boolean;
  /** The named engine is not in the library any more. */
  missing?: boolean;
}

/** PG19: one agent of a Runs on list (the first runs it, the next takes
 *  over at a usage limit). */
export interface RunsOnEntry {
  profile: string;
  engine: string | null;
  /** `Claude Code`, `Codex`, `pi`. */
  agent: string;
  /** `Codex`, `pi · qwen`. */
  label: string;
}

/** PG19: the usage limit a step's agent stopped at. */
export interface StepLimit {
  until: string | null;
  /** `14:00` (the hub's clock words). */
  words: string;
  rule: string | null;
  line: string;
  /** A reported share of the window (a warning), else null. */
  share: number | null;
  /** The agent that takes it over next; null: none is left. */
  next: RunsOnEntry | null;
  /** He chose to wait for the reset. */
  waiting: boolean;
  profile: string | null;
  seen_at: string | null;
  /** Normal, may hand off: when HoldSpeak continues on its own. */
  auto_at?: string | null;
}

/** PG19: one handoff of a step to the next agent. */
export interface StepHandoff {
  at: string;
  from: string;
  to: string;
  reason: "usage_limit" | "usage_warning" | "by_hand" | string;
  by: "engine" | "owner" | string;
  brief_ref: string;
  /** The brief the next agent received (redacted). */
  brief: string;
  redacted: Record<string, number>;
  /** `2 keys, 1 token`; empty: nothing was redacted. */
  redacted_words: string;
  earlier_turns: number;
  launch_from: string | null;
  launch_to: string | null;
  until?: string | null;
  /** PG20: the checkpoint ref the next agent continues from. */
  continues_from?: string | null;
  continues_commit?: string | null;
}

export interface ProgramSummary {
  id: string;
  title: string;
  state: ProgramState;
  state_word: string;
  done: number;
  total: number;
  /** Items only he can press (merge, findings, parked, ask review). */
  your_turn: number;
  /** Questions of a step's agent (answered in its lane). */
  asks: number;
  project_id: string | null;
  control: Control;
  /** `Secure`, `Normal`, `YOLO` (the Program wire only). */
  control_word?: string;
  updated_at: string;
  created_at: string;
  last_checkpoint: ProgramCheckpoint | null;
  in_state_seconds: number | null;
  /** Done only: `1 h 12`. */
  done_in?: string;
  /** PG17: the imported merged PRs: `Merged 15 PRs · 28 Oct to 29 Oct`. */
  history?: ProgramHistory;
}

export interface ProgramHistory {
  prs: number;
  first: string;
  last: string;
  words: string;
}

/** PG17: the merged PR an imported step stands for (no agent ran it here). */
export interface StepHistory {
  pr_number: number;
  pr_url: string | null;
  merged_at: string;
  head_commit: string | null;
}

export interface ProgramList {
  programs: ProgramSummary[];
  counts: Partial<Record<ProgramState, number>>;
  worst: ProgramState | null;
  worst_word: string;
}

export interface ProgramFinding {
  id: string;
  level?: "required" | "should" | "note" | string;
  text: string;
  decision?: "fix_now" | "later" | "skip" | null;
  /** PG16: a Skip's proposed decision record. */
  decision_record_id?: string | null;
}

export interface CheckSection {
  name: string;
  /** `green`, `red`, `no result`, `not run`. */
  state: string;
  detail?: string;
}

export interface ProgramStep {
  id: string;
  ordinal: number;
  title: string;
  state: StepState;
  state_word: string;
  /** Index into `stations` of the lit station; -1 = none yet. */
  station: number;
  stations: StationKey[];
  brief: string;
  owns: string[];
  after: number[];
  effort: "low" | "medium" | "high" | null;
  profile: string | null;
  /** `Claude Code`, `Codex`, `pi`. */
  agent: string;
  engine: ProgramEngine | null;
  prefer_idle: boolean;
  held_reason: string | null;
  race: number;
  race_of: string | null;
  /** `merge`: `level` (the Control level decides), `owner`, `auto`, `none`. */
  gate: { check: boolean; review: "none" | "agent" | "person"; review_depth: string | null; merge: string | null };
  launch_id: string | null;
  branch: string | null;
  worktree: string | null;
  pr: { number: number | null; url: string | null } | null;
  check: {
    verdict: string | null;
    log: string | null;
    sections: CheckSection[];
    reasons: string[];
    command: string | null;
    minutes: number | null;
    commit: string | null;
    running: boolean;
  };
  review: { verdict: string | null; round: number | null; reviewer: string | null };
  findings: ProgramFinding[];
  rounds: number;
  parked_reason: string | null;
  parked_by: string | null;
  origin_ref: string | null;
  for_person_id: string | null;
  for_person: string | null;
  report: string | null;
  last_checkpoint: ProgramCheckpoint | null;
  started_at: string | null;
  ended_at: string | null;
  updated_at: string | null;
  elapsed_seconds: number | null;
  elapsed: string;
  /** A race's contenders (top-level steps only). */
  contenders?: ProgramStep[];
  /** PG19: the ordered agents, the limit it stopped at, its handoffs. */
  runs_on?: RunsOnEntry[];
  limit?: StepLimit | null;
  handoffs?: StepHandoff[];
  /** PG17: an imported step: the PR it stands for. */
  history?: StepHistory | null;
}

export type YourTurnKind = "answer" | "merge" | "finding" | "parked" | "ask_review" | "core" | "race" | "add_step" | "close" | "limited";

export interface YourTurnItem {
  id: string;
  kind: YourTurnKind;
  title: string;
  choices: string[];
  program_id: string;
  program_title: string;
  step_id: string;
  ordinal: number;
  step_title: string;
  launch_id: string | null;
  since: string | null;
  project_id: string | null;
  for_person_id: string | null;
  pr: { number: number | null; url: string | null } | null;
  finding_id?: string;
  level?: string;
  /** A core question (the goal, the shape of the work, egress, money,
   *  authority, safety, no rule): its reason. */
  core?: boolean;
  reason?: string | null;
  /** add_step: the proposal's index (sent as `finding_id`). */
  proposal?: number;
  /** limited (PG19): the agent that would take it over, and the reset. */
  next?: RunsOnEntry;
  agent?: string;
  until?: string | null;
  until_words?: string;
  warning?: boolean;
}

export interface ProgramPlace {
  project: { id: string; name: string } | null;
  origin: { ref: string; kind: string; id: string; title: string } | null;
  person: { id: string; name: string } | null;
}

export interface Program extends ProgramSummary {
  goal: string;
  repository: { root: string | null; label: string; base_branch: string | null };
  check_command: string | null;
  default: { profile: string | null; agent: string; engine: ProgramEngine | null; runs_on?: RunsOnEntry[] };
  /** PG19: the agents that may read this repository (empty: every one). */
  allowed_profiles?: string[];
  /** PG19: at Normal, hand off on its own after 10 minutes at a limit. */
  may_handoff?: boolean;
  usage_warning_share?: number | null;
  reviewer: { profile: string | null; agent: string | null; engine: ProgramEngine | null };
  prefer_idle: boolean;
  template: string | null;
  origin_ref: string | null;
  for_person_id: string | null;
  note_id: string | null;
  note_window: string | null;
  place: ProgramPlace;
  steps: ProgramStep[];
  checkpoints: ProgramCheckpoint[];
  your_turn_items: YourTurnItem[];
  decided_for_you?: DecidedRow[];
  /** Phone (PHONE-DESIGN §6): the engine may call him for this Program. */
  may_call?: boolean;
  spend_limit_usd?: number | null;
  /** He closed it (Secure). */
  closed_at?: string | null;
  revision: number;
  status_line: string;
}

/** `program_changed`: one per change; the faces re-read what it names. */
export interface ProgramChangedFrame {
  program_id: string;
  step_id?: string | null;
  state: ProgramState;
  your_turn: number;
}

/** A decide press (`POST …/steps/{sid}/decide`). */
export interface DecideBody {
  kind: Exclude<YourTurnKind, "answer">;
  choice: string;
  finding_id?: string;
  reason?: string;
}

/** The step a Drafting row writes (`POST …/plan`). */
export interface PlanStep {
  id?: string;
  title: string;
  brief?: string;
  owns?: string[];
  after?: number[];
  profile?: string | null;
  engine?: string | null;
  prefer_idle?: boolean;
  effort?: "low" | "medium" | "high";
  race?: number;
}

/** The Programs room line of a person or a project (§9b). */
export interface ProgramRoomRow {
  id: string;
  title: string;
  state: ProgramState;
  state_word: string;
  done: number;
  total: number;
  your_turn: number;
  updated_at?: string;
}

export interface PersonProgramRow extends ProgramRoomRow {
  line: string;
  to_show: { step_id: string; title: string; pr_number: number | null; pr_url: string | null; merged_at: string | null }[];
  to_ask: { step_id: string; title: string; kind: string }[];
}

