/**
 * HS-92-01 — strict product-language adapter.
 *
 * Keep this small runtime snapshot in lock-step with
 * `docs/product-language.json`; productLanguage.test.ts enforces the source of
 * truth. Legacy values are accepted only at API boundaries and always resolve
 * to a canonical product term before reaching UI copy.
 */

export const PRODUCT_LANGUAGE_VERSION = 1 as const;

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
  persona: ["Persona", "Personas"],
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

export const MEETING_PROJECTIONS = [
  "summary",
  "action_items",
  "transcript",
  "topics",
] as const;

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

export function requireCanonicalValue<T extends string>(
  value: string,
  allowed: readonly T[],
  family: string,
): T {
  if ((allowed as readonly string[]).includes(value)) return value as T;
  throw new TypeError(`Unknown HoldSpeak ${family}: ${value}`);
}
