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
  result_egress: { boundary?: string } | null;
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
