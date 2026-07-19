/**
 * HS-92-01 — strict product-language adapter.
 *
 * Keep this small runtime snapshot in lock-step with
 * `docs/product-language.json`; productLanguage.test.ts enforces the source of
 * truth. Legacy values are accepted only at API boundaries and always resolve
 * to a canonical product term before reaching UI copy.
 */

export const PRODUCT_LANGUAGE_VERSION = 2 as const;

export const PRODUCT_TERMS = {
  desk: ["Desk", "Desks"],
  meeting: ["Meeting", "Meetings"],
  transcript: ["Transcript", "Transcripts"],
  action_item: ["Action item", "Action items"],
  result: ["Result", "Results"],
  artifact: ["Artifact", "Artifacts"],
  note: ["Note", "Notes"],
  zone: ["Zone", "Zones"],
  knowledge: ["Knowledge", "Knowledge collections"],
  project: ["Project", "Projects"],
  persona: ["Agent", "Agents"],
  coder_session: ["Coder session", "Coder sessions"],
  workflow: ["Workflow", "Workflows"],
  sequence: ["Sequence", "Sequences"],
  integration: ["Integration", "Integrations"],
  runs_on: ["Runs on", "Runs on"],
  proposed_action: ["Proposed action", "Proposed actions"],
  review: ["Review", "Reviews"],
  approval: ["Approval", "Approvals"],
  grant: ["Grant", "Grants"],
  receipt: ["Receipt", "Receipts"],
} as const;

export type CanonicalProductTerm = keyof typeof PRODUCT_TERMS;

export const LEGACY_PRODUCT_ALIASES = {
  agent: "persona",
  recipe: "persona",
  coder: "coder_session",
  directory: "zone",
  folder: "zone",
  kb: "knowledge",
  knowledge_base: "knowledge",
  chain: "sequence",
  connector: "integration",
  plugin: "integration",
  profile: "runs_on",
} as const satisfies Record<string, CanonicalProductTerm>;

export const DESTINATION_CLASSES = [
  "this_device",
  "paired_device",
  "private_endpoint",
  "external_service",
] as const;
export type DestinationClass = (typeof DESTINATION_CLASSES)[number];

export const DECISION_KINDS = ["review", "approval", "grant"] as const;
export type DecisionKind = (typeof DECISION_KINDS)[number];

export const CONTROL_MODES = ["safe", "neutral", "yolo"] as const;
export type ControlMode = (typeof CONTROL_MODES)[number];

export const CONTROL_MODE_LABELS = {
  safe: "Secure",
  neutral: "Normal",
  yolo: "YOLO",
} as const satisfies Record<ControlMode, string>;

export const CONTROL_MODE_DESCRIPTIONS = {
  safe: "Reviews consequential work before it runs.",
  neutral: "Runs routine configured work and asks at consequential boundaries.",
  yolo: "Runs eligible configured work without HoldSpeak approval prompts.",
} as const satisfies Record<ControlMode, string>;

export const DESTINATION_CLASS_LABELS = {
  this_device: "This device",
  paired_device: "Paired device",
  private_endpoint: "Private endpoint",
  external_service: "External service",
} as const satisfies Record<DestinationClass, string>;

export const LIFECYCLE_AXES = {
  readiness: ["unconfigured", "configured", "ready", "unavailable"],
  availability: ["offline", "connecting", "available", "degraded"],
  sync: ["local_only", "pending_sync", "synced", "sync_error"],
  work: ["queued", "running", "succeeded", "failed", "cancelled"],
  review: ["unreviewed", "accepted", "dismissed"],
  authority: [
    "not_requested",
    "proposed",
    "approved",
    "rejected",
    "expired",
    "revoked",
  ],
  attention: ["unseen", "needs_attention", "acknowledged", "resolved"],
} as const;

export const LIFECYCLE_LABELS = {
  readiness: {
    unconfigured: "Not set up",
    configured: "Configured",
    ready: "Ready",
    unavailable: "Unavailable",
  },
  availability: {
    offline: "Offline",
    connecting: "Connecting",
    available: "Available",
    degraded: "Degraded",
  },
  sync: {
    local_only: "This device only",
    pending_sync: "Pending sync",
    synced: "Synced",
    sync_error: "Sync failed",
  },
  work: {
    queued: "Queued",
    running: "Running",
    succeeded: "Succeeded",
    failed: "Failed",
    cancelled: "Cancelled",
  },
  review: {
    unreviewed: "Needs review",
    accepted: "Accepted",
    dismissed: "Dismissed",
  },
  authority: {
    not_requested: "No authority requested",
    proposed: "Needs approval",
    approved: "Approved",
    rejected: "Rejected",
    expired: "Expired",
    revoked: "Revoked",
  },
  attention: {
    unseen: "New",
    needs_attention: "Needs attention",
    acknowledged: "Acknowledged",
    resolved: "Resolved",
  },
} as const;

export const MEETING_PROJECTIONS = [
  "summary",
  "action_items",
  "transcript",
  "topics",
] as const;

/**
 * Proposal wire vocabulary (HS-93): effect classes are `target/action`
 * compounds, authority bases come from `operation_policy.resolve_policy`, and
 * proposal statuses from `VALID_ACTUATOR_PROPOSAL_STATUSES`. Unknown values
 * humanize rather than rendering raw snake_case.
 */
export const EFFECT_CLASS_LABELS: Record<string, string> = {
  "slack/post_message": "Slack message",
  "webhook/post_message": "Webhook message",
  "github/create_issue": "GitHub issue",
  "desktop/type_text": "Typed text",
  "terminal/type_text_and_keys": "Terminal input",
};

export const AUTHORITY_BASIS_LABELS: Record<string, string> = {
  none: "No authority",
  per_action_required: "Per-action approval required",
  per_action_decision: "Per-action approval",
  scoped_grant: "Scoped grant",
  control_posture: "Control posture",
  configured_cadence: "Configured cadence",
  configured_preview: "Configured preview",
  direct_gesture: "Direct gesture",
  explicit_run: "Explicit run",
  explicit_dictation: "Explicit dictation",
};

export const PROPOSAL_STATUS_LABELS: Record<string, string> = {
  proposed: "Needs approval",
  approved: "Approved",
  executed: "Executed",
  rejected: "Rejected",
  failed: "Failed",
};

const WIRE_NAME_OVERRIDES: Record<string, string> = {
  github: "GitHub",
  slack: "Slack",
  webhook: "Webhook",
};

export function canonicalProductTerm(value: string): CanonicalProductTerm {
  const normalized = value.trim().toLowerCase().replace(/[ -]/g, "_");
  if (Object.prototype.hasOwnProperty.call(PRODUCT_TERMS, normalized)) {
    return normalized as CanonicalProductTerm;
  }
  if (
    Object.prototype.hasOwnProperty.call(LEGACY_PRODUCT_ALIASES, normalized)
  ) {
    return LEGACY_PRODUCT_ALIASES[
      normalized as keyof typeof LEGACY_PRODUCT_ALIASES
    ];
  }
  throw new TypeError(`Unknown HoldSpeak product term: ${value}`);
}

export function productLabel(value: string, plural = false): string {
  return PRODUCT_TERMS[canonicalProductTerm(value)][plural ? 1 : 0];
}

export function controlModeWire(value: string): ControlMode {
  const normalized = value.trim().toLowerCase();
  const byLabel = Object.entries(CONTROL_MODE_LABELS).find(
    ([, label]) => label.toLowerCase() === normalized,
  )?.[0];
  return requireCanonicalValue(
    byLabel ?? normalized,
    CONTROL_MODES,
    "control mode",
  );
}

export function controlModeLabel(value: string): string {
  return CONTROL_MODE_LABELS[controlModeWire(value)];
}

export function controlModeDescription(value: string): string {
  return CONTROL_MODE_DESCRIPTIONS[controlModeWire(value)];
}

export function destinationClassLabel(value: string): string {
  return DESTINATION_CLASS_LABELS[
    requireCanonicalValue(value, DESTINATION_CLASSES, "destination class")
  ];
}

export function humanizeWireValue(value: string): string {
  const clean = value.trim();
  const known = WIRE_NAME_OVERRIDES[clean.toLowerCase()];
  if (known) return known;
  const spaced = clean.replace(/[_/]+/g, " ").replace(/\s+/g, " ").trim();
  if (!spaced) return "";
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export function effectClassLabel(value: string): string {
  return (
    EFFECT_CLASS_LABELS[value.trim().toLowerCase()] ?? humanizeWireValue(value)
  );
}

export function authorityBasisLabel(value: string): string {
  return (
    AUTHORITY_BASIS_LABELS[value.trim().toLowerCase()] ??
    humanizeWireValue(value)
  );
}

export function proposalStatusLabel(value: string): string {
  return (
    PROPOSAL_STATUS_LABELS[value.trim().toLowerCase()] ??
    humanizeWireValue(value)
  );
}

export function lifecycleLabel<Axis extends keyof typeof LIFECYCLE_AXES>(
  axis: Axis,
  value: string,
): string {
  const canonical = requireCanonicalValue(
    value,
    LIFECYCLE_AXES[axis],
    `${axis} lifecycle value`,
  );
  return (LIFECYCLE_LABELS[axis] as Record<string, string>)[canonical];
}

export function requireCanonicalValue<T extends string>(
  value: string,
  allowed: readonly T[],
  family: string,
): T {
  if ((allowed as readonly string[]).includes(value)) return value as T;
  throw new TypeError(`Unknown HoldSpeak ${family}: ${value}`);
}
