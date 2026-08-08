// HS-117-05 — shared core types: CoreProps, response interfaces, and
// promoted locals. Every core imports from here instead of ad-hoc
// JsonRecord bags. The endpoint contracts are compile-time structure.

import type { ReactNode } from "react";

/* ── CoreProps: the host contract every core accepts ── */

export interface CoreProps {
  /** Optional chrome the host renders around the core's own verbs. */
  hero?: (actions: ReactNode) => ReactNode;
  /** The subject this window is scoped to (a qualified ref). */
  scope?: string;
  /** The subject's product label (hosts resolve it; never a raw ref). */
  scopeLabel?: string;
}

/* ── promoted core-local interfaces ── */

/** ConstitutionalContextCore */
export interface ContextState {
  content: string;
  revision: number;
  content_hash: string;
  char_limit?: number;
}

export interface HistoryEntry {
  content: string;
  revision: number;
  content_hash: string;
  created_at: string;
}

/** WorkbenchesHomeCore */
export interface WbSummary {
  id: string;
  name: string;
  recipe_id: string | null;
  profile_id: string | null;
  schedule: string | null;
  schedule_enabled: boolean;
  item_count: number;
  pending_count: number;
  last_run: {
    started_at: string;
    completed_at: string | null;
    items_completed: number;
    items_attempted: number;
    items_failed: number;
    egress_boundary: string;
    model: string;
    status: string;
  } | null;
}

export interface RunSummary {
  id: string;
  workbench_id: string;
  workbench_name: string;
  started_at: string;
  completed_at: string | null;
  items_completed: number;
  items_attempted: number;
  items_failed: number;
  egress_boundary: string;
  model: string;
  status: string;
}

/** SetupCore */
export type SetupStatus = {
  overall?: string;
  first_run?: boolean;
  sections?: Array<Record<string, unknown>>;
  trust?: Record<string, unknown>;
  presence?: Record<string, unknown>;
};

/** CommandsCore */
export type Macro = {
  keyword: string;
  action: { kind: string; payload: string };
};

/** SettingsCore */
export type SecretState = { configured?: boolean; destination?: string };

/* ── endpoint response types ── */

/** ActivityCore endpoints */
export interface ActivityStatusResponse {
  settings?: { enabled?: boolean; [key: string]: unknown };
  [key: string]: unknown;
}

export interface ActivityRecordsResponse {
  records?: Record<string, unknown>[];
  items?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface ActivityRulesResponse {
  rules?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface ActivityCandidatesResponse {
  candidates?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface ActivityConnectorsResponse {
  connectors?: Record<string, unknown>[];
  [key: string]: unknown;
}

/** CadenceCore endpoints */
export interface CadenceStatusResponse {
  enabled?: boolean;
  pressure?: string | number;
  [key: string]: unknown;
}

export interface CadenceLoopsResponse {
  loops?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface CadenceHistoryResponse {
  nudges?: Record<string, unknown>[];
  [key: string]: unknown;
}

/** CommandsCore / SettingsCore — the settings blob */
export interface SettingsResponse {
  config_version?: number;
  control_mode?: string;
  _secrets?: Record<string, SecretState>;
  dictation?: DictationSettings;
  hotkey?: Record<string, unknown>;
  ui?: Record<string, unknown>;
  model?: Record<string, unknown>;
  meeting?: Record<string, unknown>;
  wake_word?: Record<string, unknown>;
  cadence?: Record<string, unknown>;
  cadence_telegram?: Record<string, unknown>;
  presence?: Record<string, unknown>;
  mesh?: Record<string, unknown>;
  device?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface DictationSettings {
  macros?: { enabled?: boolean; items?: Macro[] };
  pipeline?: Record<string, unknown>;
  runtime?: Record<string, unknown>;
  spoken_symbols?: Array<{ spoken?: string; symbol?: string; attach?: string }>;
  preview_before_type?: boolean;
  [key: string]: unknown;
}

export interface CommandTestResponse {
  ok?: boolean;
  tested?: boolean;
  note?: string;
  error?: string;
  [key: string]: unknown;
}

/** AuthorityCore — used by SettingsCore and HistoryCore */
export interface AuthorityPolicyResponse {
  control_mode?: string;
  precedence?: string[];
  [key: string]: unknown;
}

/** CompanionCore endpoints */
export interface RecipesResponse {
  recipes?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface CodersStatusResponse {
  agent?: { sessions?: Record<string, unknown>[]; [key: string]: unknown };
  [key: string]: unknown;
}

/** LiveCore endpoints */
export interface MeetingStateResponse {
  active?: boolean;
  meeting_active?: boolean;
  status?: string;
  title?: string;
  tags?: string[];
  segments?: Record<string, unknown>[];
  formatted_duration?: string;
  duration?: { formatted?: string } | string;
  id?: string;
  meeting_id?: string;
  intel_status?: { state?: string } | string;
  [key: string]: unknown;
}

export interface RuntimeStatusResponse {
  intel_egress?: { label?: string; [key: string]: unknown } | string;
  [key: string]: unknown;
}

export interface IntentControlResponse {
  profile?: string;
  [key: string]: unknown;
}

export interface PluginJobsSummaryResponse {
  [key: string]: unknown;
}

export interface DevicesHealthResponse {
  devices?: Record<string, unknown>[];
  items?: Record<string, unknown>[];
  [key: string]: unknown;
}

/** ConstitutionalContextCore endpoints */
export interface ConstitutionalContextResponse {
  context: ContextState;
  error?: string;
  [key: string]: unknown;
}

export interface ConstitutionalContextHistoryResponse {
  revisions: HistoryEntry[];
  [key: string]: unknown;
}

export interface ConstitutionalContextSaveResponse {
  context?: ContextState;
  error?: string;
  [key: string]: unknown;
}

/** WorkbenchesHomeCore endpoints */
export interface WorkbenchesListResponse {
  workbenches: WbSummary[];
  [key: string]: unknown;
}

export interface WorkbenchRunsResponse {
  runs: RunSummary[];
  [key: string]: unknown;
}

/** DictationCore endpoints */
export interface DictationReadinessResponse {
  config?: Record<string, unknown>;
  target?: Record<string, unknown>;
  depth?: Record<string, unknown>;
  warnings?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface DictationBlocksResponse {
  document?: { blocks?: unknown[] };
  [key: string]: unknown;
}

export interface DictationCorrectionsResponse {
  items?: Record<string, unknown>[];
  corrections?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface DictationLearningDigestResponse {
  totals?: { corrections_made?: number; dictations_corrected?: number; similar_nudged?: number };
  by_block?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface DictationProjectKbResponse {
  kb?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface DictationProjectHsResponse {
  files?: Record<string, Record<string, unknown>>;
  [key: string]: unknown;
}

export interface DictationJournalResponse {
  items?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface DictationJournalReplayResponse {
  after?: { final_text?: string; [key: string]: unknown };
  [key: string]: unknown;
}

export interface DictationAgentHooksResponse {
  destinations?: Record<string, unknown>;
  agents?: Record<string, { latest_session?: unknown; [key: string]: unknown }>;
  [key: string]: unknown;
}

export interface ActivityNudgesResponse {
  nudges?: Record<string, unknown>[];
  items?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface DictationDryRunResponse {
  delivered?: boolean;
  [key: string]: unknown;
}

/** HistoryCore endpoints */
export interface MeetingsListResponse {
  meetings?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface MeetingsFacetsResponse {
  [key: string]: unknown;
}

export interface AllActionItemsResponse {
  items?: Record<string, unknown>[];
  actions?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface SpeakersResponse {
  speakers?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface ProjectsListResponse {
  projects?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface IntelJobsResponse {
  jobs?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface PluginJobsResponse {
  jobs?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface MeetingDetailResponse {
  id?: string;
  title?: string;
  segments?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface MeetingArtifactsResponse {
  artifacts?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface MeetingAftercareResponse {
  [key: string]: unknown;
}

export interface MeetingTimelineResponse {
  [key: string]: unknown;
}

export interface MeetingProposalsResponse {
  proposals?: Record<string, unknown>[];
  [key: string]: unknown;
}

/** ProjectMemoryCore endpoints */
export interface ProjectResponse {
  id?: string;
  name?: string;
  [key: string]: unknown;
}

export interface ProjectMeetingsResponse {
  meetings?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface ProjectDecisionsResponse {
  decisions?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface ProjectArtifactsResponse {
  artifacts?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface SinceLastMeetingResponse {
  current_meeting?: unknown;
  since_last_meeting?: {
    previous_meeting?: Record<string, unknown>;
    new_decisions?: unknown[];
    new_actions?: unknown[];
    closed_actions?: unknown[];
    [key: string]: unknown;
  } | null;
  [key: string]: unknown;
}

export interface DecisionMomentResponse {
  moment?: {
    meeting_id?: string;
    segment_index?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface DecisionTransitionResponse {
  decision?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface DecisionPromoteResponse {
  artifact?: { id?: string; [key: string]: unknown };
  [key: string]: unknown;
}

export interface MemorySearchResponse {
  hits?: Record<string, unknown>[];
  [key: string]: unknown;
}

/** settingsModels.tsx endpoints */
export interface InferenceTargetsResponse {
  targets?: Record<string, unknown>[];
  [key: string]: unknown;
}

export interface ProfilesResponse {
  profiles?: Record<string, unknown>[];
  [key: string]: unknown;
}
