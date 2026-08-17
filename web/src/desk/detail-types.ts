/** Detail types for window-level data (HS-117-13).
 *
 * These were inline in WorkbenchWindow.tsx; now they are first-class citizens
 * in the type layer so any window or hook can import them without pulling in
 * the full component tree. All fields use wireGuard-safe types (no `any`,
 * no `as` casts). */

/* ── Workbench detail types ───────────────────────────────────────────── */

export interface WorkbenchDetail {
  id: string;
  name: string;
  recipe_id: string | null;
  profile_id: string | null;
  resolver_profile_id: string | null;
  schedule: string | null;
  schedule_enabled: boolean;
  items: WorkbenchItem[];
  item_count: number;
  pending_count: number;
  last_run: WorkbenchRun | null;
}

export interface WorkbenchItem {
  id: string;
  title: string;
  body: string;
  priority: number;
  status: string;
  grounding: Record<string, unknown>;
  result: string | null;
  /** The backend's structured reason when a workbench run fails. */
  error?: string | null;
  error_reason?: string | null;
  result_egress: { boundary?: string } | null;
  result_artifact_id: string | null;
  artifact_status?: string | null;
  mint_attempted: boolean;
  tokens_consumed: number;
  created_at: string;
  completed_at: string | null;
}

export interface WorkbenchRun {
  id: string;
  started_at: string;
  completed_at: string | null;
  items_attempted: number;
  items_completed: number;
  items_failed: number;
  mint_failures: number;
  total_tokens: number;
  egress_boundary: string;
  model: string;
  status: string;
}

export interface Skill {
  id: string;
  title: string;
  body: string;
  source: string;
  status: string;
  recipe_ids: string[];
  created_by: string;
}

export interface MemoryEntry {
  run_id: string;
  timestamp: string;
  kind: string;
  content: string;
  item_title: string;
  provenance: { egress?: string; model?: string };
}

/* ── Workbench automations / Reactions ──────────────────────────────── */

/** A durable, Workbench-native event trigger. V1 always adds grounded work;
 * it does not run the entire pending Workbench from an unrelated event. */
export interface WorkbenchAutomation {
  id: string;
  name: string;
  provider: "github" | "jira" | "custom";
  event_kind: string;
  enabled: boolean;
  status: "active" | "paused" | "attention" | "unavailable";
  adapter_status?: "ready" | "unavailable" | "not_configured";
  last_error?: string | null;
  last_good_at?: string | null;
  created_at?: string;
}

/** One event delivery (or refusal) carrying the durable receipt from V1. */
export interface AutomationHistoryEntry {
  id: string;
  occurred_at: string;
  outcome: "added" | "skipped" | "refused" | "failed";
  event_kind: string;
  subject: string;
  receipt_id?: string | null;
  detail?: string | null;
}

/** Non-mutating evidence from an event-trigger test. */
export interface AutomationTestResult {
  entity_count: number;
  changes: number;
  would_add: number;
}

/** Intrinsic negative-space automation; no connector or polling source needed. */
export interface ResourcefulPolicy {
  workbench_id: string;
  enabled: boolean;
  idle_after_minutes: number;
  cooldown_hours: number;
  nightly_target: number;
  night_only: boolean;
  night_start_hour: number;
  night_end_hour: number;
  routines: Array<"loose_ideas" | "failed_work">;
  idle_since?: string | null;
  last_checked_at?: string | null;
  last_fired_at?: string | null;
  nightly_count: number;
  last_outcome?: string;
  last_error?: string | null;
}

export interface ResourcefulDispatch {
  workbench_id: string;
  candidate_key: string;
  routine: string;
  source_ref: string;
  event_id: string;
  item_id: string;
  operation_id?: string | null;
  receipt_id?: string | null;
  outcome: string;
  created_at: string;
  completed_at?: string | null;
}
