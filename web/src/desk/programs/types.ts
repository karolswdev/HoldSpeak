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

/** PG-REQ: the kinds of proof (design §3, §4). */
export type RequirementKind = "check" | "review" | "shot" | "word";
export type RequirementState = "not_yet" | "met" | "unmet" | "waived";
export type RequirementScope = "program" | "every_step" | "step";

/** PG-REQ §11: what proves a requirement's state (a log, the reviewer's
 *  line, a shot, his press), with the commit it was judged on. */
export interface RequirementEvidence {
  kind?: "log" | "finding" | "shot" | "press" | string;
  line?: string;
  by?: string;
  at?: string;
  commit?: string | null;
  command?: string;
  case?: string;
  width?: number;
  ref?: string;
  round?: number;
  /** The log text or the shot image (`GET …/requirements/{rid}/evidence`). */
  url?: string;
}

/** PG-REQ §11: one sentence of his and the way it is proven. */
export interface Requirement {
  id: string;
  ordinal: number;
  /** `R3`. */
  label: string;
  program_id: string;
  step_id: string | null;
  scope: RequirementScope;
  text: string;
  kind: RequirementKind;
  /** `Check`, `Review`, `Shot`, `Your word`. */
  kind_word: string;
  required: boolean;
  spec: { command?: string; expect?: string; case?: string; width?: number };
  parent_id: string | null;
  /** An every-step parent: each step's copy and its state. */
  steps?: { step_id: string; ordinal: number; state: RequirementState }[];
  state: RequirementState;
  /** `Not yet`, `Checking`, `Met`, `Unmet`, `Waived`, `Waits for you`. */
  state_word: string;
  running: boolean;
  judged_commit: string | null;
  stale: boolean;
  evidence: RequirementEvidence;
  waived_reason: string | null;
  rounds: number;
  by: "owner" | "agent" | "template" | string;
  /** The presses his state allows (`met`, `unmet`, `waive`, `send_back`). */
  choices: string[];
}

/** Required ones, counted (`4 of 5 met`; waived counts as met). */
export interface RequirementsMet {
  met: number;
  total: number;
  unmet: number;
  waived: number;
  /** What waits on his word or his press. */
  his: number;
}

/** What this repository can prove (a Shot needs a shot command). */
export interface CanProve {
  check: boolean;
  review: boolean;
  shot: boolean;
  word: boolean;
  shot_reason?: string | null;
}

/** A line he (or an agent) added to a started step's brief. */
export interface StepAmendment {
  at: string;
  by: string;
  line: string;
  /** When it was typed to the agent; null while it waits for a turn boundary. */
  sent_at: string | null;
}

export interface ProgramSummary {
  id: string;
  title: string;
  state: ProgramState;
  state_word: string;
  /** Merged and done steps only; a skipped step is never done. */
  done: number;
  /** Steps he skipped (their dependents ran on). */
  skipped?: number;
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
  /** PG-REQ: omitted when the Program has no required requirement. */
  requirements_met?: RequirementsMet | null;
  /** PG-REQ §7: Find, Project ▾, Person ▾. */
  project?: { id: string; name: string } | null;
  for_person?: { id: string; name: string } | null;
  persons?: { id: string; name: string }[];
  search_words?: string;
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
  /** PG-LANG §5.4 (LANG6): the size of a step not handed yet, by rule. */
  estimate?: PlanSize | null;
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
  /** PG-REQ: its own requirements and its every-step copies. */
  requirements?: Requirement[];
  requirements_met?: RequirementsMet | null;
  /** PG-REQ §8: the fields its state leaves open, and why the rest are frozen. */
  editable?: string[];
  frozen?: Record<string, string>;
  amendments?: StepAmendment[];
  /** PG-WINDOW W1: what the agent did, at most three plain lines from its
   *  ledger in the order they happened (brief_words.step_story). */
  story?: { at: string | null; line: string }[];
}

export type YourTurnKind = "answer" | "merge" | "finding" | "parked" | "ask_review" | "core" | "commit" | "race" | "add_step" | "close" | "limited"
  // PG-REQ §9: his word, a requirement left after the rounds, and what an agent proposes.
  | "requirement_word" | "requirement_left" | "requirement_proposed" | "step_change" | "step_amend";

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
  /** PG-REQ: the requirement an item is about. */
  requirement_id?: string;
  /** PG-REQ: an agent's proposal (`POST …/proposals/{id}/decide`). */
  proposal_id?: number | string;
  /** PG-DIRECTION DIR3: an open briefing page for the item (absent when none). */
  page?: { package_id: string; expires_at: string };
  /** PG-WINDOW W1: the brief in his terms (brief_words.item_brief), the
   *  same lines the briefing page reads. */
  brief?: ItemBrief | null;
}

export interface ItemBrief {
  goal: string;
  doing: string;
  happened: string;
  question: string;
  /** The ordinals of the steps that wait on this answer. */
  blocked: number[];
  blocked_words: string;
  /** Each choice's consequence, in his terms. */
  consequences: Record<string, string>;
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
  /** PG-LANG LANG5: the rows a call left for his press ("later", or a row
   *  that lowers the bar); the change well opens with them. */
  held_shape?: (ShapeAnswer & { source: "call"; at?: number }) | null;
  /** Phone (PHONE-DESIGN §6): the engine may call him for this Program. */
  may_call?: boolean;
  spend_limit_usd?: number | null;
  /** He closed it (Secure). */
  closed_at?: string | null;
  /** PG-REQ: the Program's own and the every-step parents, in ordinal order. */
  requirements?: Requirement[];
  can_prove?: CanProve;
  /** PG-LANG LANG9: the interview rounds (§6.2). */
  rounds?: ProgramRound[];
  revision: number;
  status_line: string;
}

/** PG-LANG LANG9: one question of a round; `became`: what its answer proposed. */
export interface ProgramRoundQuestion {
  id: string;
  text: string;
  why: string | null;
  choices: string[];
  answer: string | null;
  answered_by: string | null;
  at: string | null;
  skipped: boolean;
  became: string[];
}

export type RoundState = "open" | "asking" | "done" | "skipped";

/** PG-LANG LANG9: one interview round on the Program wire. */
export interface ProgramRound {
  name: string;
  state: RoundState;
  order: number;
  questions: ProgramRoundQuestion[];
  asked: number;
  answered: number;
  /** The changes its answers became (the token keeps "n changes"). */
  became: number;
  /** The question that waits for his answer. */
  waiting: string | null;
}

/** `POST …/rounds/{name}/next`: one question, or the round done by the engine's word. */
export interface RoundAsked {
  round: string;
  state: RoundState;
  done: boolean;
  question: ProgramRoundQuestion | null;
  engine: string | null;
  seconds: number;
  program: Program;
}

/** `POST …/rounds/{name}/answer`: the shaped rows (source `round:<name>`). */
export interface RoundAnswer extends ShapeAnswer {
  source: string;
  round: string;
  round_question: ProgramRoundQuestion;
  program: Program;
}

/** `POST …/rounds`, `…/decide` and Skip question: the Program after the press. */
export interface RoundPressed {
  round?: string;
  state?: RoundState;
  program: Program;
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


/* ── PG-LANG (PROGRAM-LANGUAGE-2026-10-31 §3.6, §3.8): the Program text ── */

/** `GET /api/programs/{id}/text`: the text with its lamps. */
export interface ProgramText {
  program_id: string;
  text: string;
  revision: number;
  version: number;
}

/** One change row of a text preview or apply (§3.8). */
export interface TextChange {
  id: string;
  op: "add" | "change" | "remove" | "move" | "amend";
  /** `program`, `step 3`, `R6`. */
  where: string;
  field: string;
  before: string;
  after: string;
  say: string;
  verdict: "allowed" | "refused" | "conflict" | "lowers";
  lowers_bar: boolean;
  reason: string | null;
  code: string | null;
  /** The line of the proposed text (1-based). */
  line: number | null;
  /** LANG6: where the row came from (`plan` for a planning draft). */
  source?: string;
  /** LANG6: an added step's size (`7k of 32k`; `step_too_big`). */
  size?: PlanSize | null;
}

/** PG-LANG §5.4: one step's size; the words name the working share. */
export interface PlanSize {
  tokens: number;
  budget: number | null;
  share: number | null;
  /** `null`: no budget applies (Claude Code or Codex with none named). */
  fits: boolean | null;
  /** `7k of 32k`, or `Too big for qwen · 41k of 32k`. */
  words: string;
  engine: string | null;
  code: "step_too_big" | null;
  place?: number;
  title?: string;
  owns?: string[];
}

/** PG-LANG LANG6: `POST /api/programs/{id}/plan/draft`, a goal drafted
 *  into change rows (the text_apply answer, plus the engine's words). */
export interface PlanAnswer extends TextApplyAnswer {
  source: "plan";
  say: string;
  words: string;
  counts: { steps: number; requirements: number; too_big: number };
  engine: string;
  latency_ms: number;
  seconds: number;
  sizes: PlanSize[];
  budget: number | null;
  share: number | null;
  split: { place: number; title: string; words: string; owns: string[] }[];
  proposed_text: string;
  base: string;
}

/** `POST /api/programs/{id}/text`: the rows, and on a real apply the Program. */
export interface TextApplyAnswer {
  program_id: string;
  changes: TextChange[];
  patch: string;
  /** The proposed text with each refused hunk put back as it was. */
  allowed_text: string;
  applied: boolean;
  /** The current text (after an apply: the new one). */
  text: string;
  revision: number;
  version: number;
  refused: number;
  /** The ids of the rows that lower the bar. */
  lowers: string[];
  program?: Program;
}

/** PG-LANG LANG3: the engine that shapes (`engine: null`: none is set). */
export interface ShapeEngine {
  program_id: string;
  engine: string | null;
  capability: string | null;
  profile: string | null;
}

/** PG-LANG LANG3: a sentence shaped into change rows (the text_apply
 *  answer, plus the engine's words). At YOLO with apply, `applied` is true,
 *  `applied_rows` are the rows that landed, `decision` is the Decided for
 *  you row (Overturn), and `changes` are the rows that still wait for his
 *  press, against the text as it is now (`base`). */
export interface ShapeAnswer extends TextApplyAnswer {
  sentence: string;
  say: string;
  question: string | null;
  engine: string;
  latency_ms: number;
  seconds: number;
  proposed_text: string;
  base: string;
  applied_rows: TextChange[];
  decision: { id: number | string; rule: string; kind: string; choice: string; at: string } | null;
  held?: string;
}
