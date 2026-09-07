// HS-162-05 -- the Update posture types: decode the wire shapes from
// tests/integration/test_update_routes.py (the fixture truth).
// claims_json carries the claim array; each claim resolves to openable
// source refs (paying 160's S-4 debt).

/* ── Wire update shape (from project_updates table rows) ── */

import type { ChipState } from "../../../desk/surface";

export type UpdateLifecycle = "draft" | "published" | "superseded";

/* ── HS-200-06 (C2): kind, support and acceptance are three
      INDEPENDENT axes. A citation buys source linkage only. ── */

export type ClaimKind =
  | "observation"
  | "inference"
  | "proposal"
  | "decision"
  | "execution_result"
  | "outcome_measure";

export type ClaimSupport =
  | "unknown"
  | "source_linked"
  | "supported"
  | "disputed";

export type ClaimAcceptance =
  | "unreviewed"
  | "accepted"
  | "rejected"
  | "superseded";

export type ClaimSupportRecord = {
  method: string;
  sourceVersion: string;
  sourceRefs: string[];
  fields: string[];
  reviewerRef: string | null;
  checkedAt: string | null;
  invalidatedAt: string | null;
  invalidationReason: string | null;
};

export type ClaimUnknown = { type: string; value: string };

export type UpdateClaim = {
  spanId: string;
  text: string;
  refs: string[];
  section: string;
  verified: boolean;
  /** True when the record carries the C2 axes (everything the service
   *  serves does; a bare fixture may not). */
  hasAxes: boolean;
  kind: ClaimKind;
  support: ClaimSupport;
  acceptance: ClaimAcceptance;
  /** Set when the record was mapped from a citation-only `verified`
   *  row written before HS-200-06. */
  supportMappingVersion: string | null;
  supportRecord: ClaimSupportRecord | null;
  unknowns: ClaimUnknown[];
};

export type ProjectUpdate = {
  id: string;
  projectId: string;
  projectRevision: number;
  reviewId: string | null;
  lifecycle: UpdateLifecycle;
  draftRevision: number;
  bodyMd: string;
  claims: UpdateClaim[];
  sourceManifestJson: string;
  generator: string;
  generatorHost: string | null;
  generatorModel: string | null;
  fallbackReason: string | null;
  createdAt: string;
  updatedAt: string;
  publishedAt: string | null;
};

function decodeSupportRecord(raw: unknown): ClaimSupportRecord | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;
  return {
    method: String(r.method ?? ""),
    sourceVersion: String(r.source_version ?? ""),
    sourceRefs: Array.isArray(r.source_refs)
      ? (r.source_refs as unknown[]).map(String)
      : [],
    fields: Array.isArray(r.fields) ? (r.fields as unknown[]).map(String) : [],
    reviewerRef: r.reviewer_ref != null ? String(r.reviewer_ref) : null,
    checkedAt: r.checked_at != null ? String(r.checked_at) : null,
    invalidatedAt: r.invalidated_at != null ? String(r.invalidated_at) : null,
    invalidationReason:
      r.invalidation_reason != null ? String(r.invalidation_reason) : null,
  };
}

function decodeUnknowns(raw: unknown): ClaimUnknown[] {
  if (!Array.isArray(raw)) return [];
  return (raw as unknown[])
    .filter((u): u is Record<string, unknown> => !!u && typeof u === "object")
    .map((u) => ({ type: String(u.type ?? ""), value: String(u.value ?? "") }));
}

export function decodeClaim(raw: Record<string, unknown>): UpdateClaim {
  const hasAxes = typeof raw.support === "string";
  return {
    spanId: String(raw.span_id ?? ""),
    text: String(raw.text ?? ""),
    refs: Array.isArray(raw.refs)
      ? (raw.refs as unknown[]).map(String)
      : [],
    section: String(raw.section ?? ""),
    // Deterministic claims omit verified (defaulting to true);
    // only model MARKED claims set verified:false explicitly.
    verified: raw.verified !== false,
    hasAxes,
    kind: (typeof raw.kind === "string"
      ? raw.kind
      : "observation") as ClaimKind,
    support: (hasAxes ? raw.support : "unknown") as ClaimSupport,
    acceptance: (typeof raw.acceptance === "string"
      ? raw.acceptance
      : "unreviewed") as ClaimAcceptance,
    supportMappingVersion:
      raw.support_mapping_version != null
        ? String(raw.support_mapping_version)
        : null,
    supportRecord: decodeSupportRecord(raw.support_record),
    unknowns: decodeUnknowns(raw.unknowns),
  };
}

/* ── Claim axis tokens (HS-200-06) ── */

const KIND_TOKENS: Record<string, string> = {
  observation: "OBSERVATION",
  inference: "INFERENCE",
  proposal: "PROPOSAL",
  decision: "DECISION",
  execution_result: "EXECUTION RESULT",
  outcome_measure: "OUTCOME MEASURE",
};

/** The lead emblem: what the sentence asserts. */
export function claimKindToken(kind: string): string {
  return KIND_TOKENS[kind] ?? kind.replace(/_/g, " ").toUpperCase();
}

export type ClaimToken = { label: string; state: ChipState };

/** What the evidence establishes -- with the honest history suffix:
 *  MIGRATED for a record mapped from a citation-only row, EDITED when
 *  the sentence changed after it was supported. */
export function claimSupportToken(claim: UpdateClaim): ClaimToken {
  if (claim.support === "supported") {
    return { label: "SUPPORTED", state: "success" };
  }
  if (claim.support === "disputed") {
    return { label: "DISPUTED", state: "failure" };
  }
  if (claim.support === "source_linked") {
    if (claim.supportRecord?.invalidatedAt) {
      return { label: "LINKED · EDITED", state: "warning" };
    }
    if (claim.supportMappingVersion) {
      return { label: "LINKED · MIGRATED", state: "idle" };
    }
    return { label: "LINKED", state: "idle" };
  }
  return { label: "UNSUPPORTED", state: "warning" };
}

/** Applicable domain or reviewer judgment. Never inferred from a score. */
export function claimAcceptanceToken(claim: UpdateClaim): ClaimToken {
  if (claim.acceptance === "accepted") {
    return { label: "ACCEPTED", state: "success" };
  }
  if (claim.acceptance === "rejected") {
    return { label: "REJECTED", state: "failure" };
  }
  if (claim.acceptance === "superseded") {
    return { label: "SUPERSEDED", state: "warning" };
  }
  return { label: "UNREVIEWED", state: "idle" };
}

/** A typed unknown the cited source cannot carry: "NAME · Priya". */
export function claimUnknownToken(unknown: ClaimUnknown): string {
  return `${unknown.type.toUpperCase()} · ${unknown.value}`;
}

export function decodeUpdate(raw: Record<string, unknown>): ProjectUpdate {
  // claims_json arrives as a JSON string on the wire
  let claims: UpdateClaim[] = [];
  const rawClaims = raw.claims_json;
  if (typeof rawClaims === "string" && rawClaims) {
    try {
      const parsed = JSON.parse(rawClaims) as unknown;
      if (Array.isArray(parsed)) {
        claims = parsed.map((c: unknown) =>
          decodeClaim(c as Record<string, unknown>),
        );
      }
    } catch {
      claims = [];
    }
  } else if (Array.isArray(rawClaims)) {
    claims = rawClaims.map((c: unknown) =>
      decodeClaim(c as Record<string, unknown>),
    );
  }

  return {
    id: String(raw.id ?? ""),
    projectId: String(raw.project_id ?? ""),
    projectRevision: Number(raw.project_revision ?? 0),
    reviewId: raw.review_id != null ? String(raw.review_id) : null,
    lifecycle: String(raw.lifecycle ?? "draft") as UpdateLifecycle,
    draftRevision: Number(raw.draft_revision ?? 1),
    bodyMd: String(raw.body_md ?? ""),
    claims,
    sourceManifestJson: String(raw.source_manifest_json ?? "{}"),
    generator: String(raw.generator ?? "deterministic"),
    generatorHost: raw.generatorHost != null ? String(raw.generatorHost) : null,
    generatorModel: raw.generatorModel != null ? String(raw.generatorModel) : null,
    fallbackReason: raw.fallback_reason != null
      ? String(raw.fallback_reason)
      : null,
    createdAt: String(raw.created_at ?? ""),
    updatedAt: String(raw.updated_at ?? ""),
    publishedAt: raw.published_at != null ? String(raw.published_at) : null,
  };
}

/* ── Generator provenance label ── */

/** Human label for the generator provenance: "deterministic" stays as
 *  "Deterministic"; "model:<assignment>" shows "Model (<assignment>)";
 *  unknown generators show verbatim. */
export function generatorLabel(generator: string): string {
  if (generator === "deterministic") return "Deterministic";
  if (generator.startsWith("model:")) {
    const assignment = generator.slice("model:".length);
    return `Model (${assignment})`;
  }
  return generator;
}

/** Plain-words provenance for the list row — no assignment id (it goes
 *  to title/aria and the editor band where there's room). */
export function provenancePhrase(generator: string): string {
  if (generator === "deterministic") return "Deterministic draft";
  if (generator.startsWith("model:")) return "Model draft";
  return `${generator} draft`;
}

/* ── Section labels (UPD-001 canonical order) ── */

const SECTION_LABELS: Record<string, string> = {
  progress: "Progress",
  decisions: "Decisions",
  risks_blockers: "Risks & blockers",
  dependencies: "Dependencies",
  next_actions: "Next actions",
  source_coverage: "Source coverage",
};

export function sectionLabel(key: string): string {
  return SECTION_LABELS[key] ?? key.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

/* ── Lifecycle label ── */

export function lifecycleLabel(lifecycle: UpdateLifecycle): string {
  if (lifecycle === "draft") return "Draft";
  if (lifecycle === "published") return "Published";
  if (lifecycle === "superseded") return "Superseded";
  return lifecycle;
}

export function lifecycleTone(lifecycle: UpdateLifecycle): string | undefined {
  if (lifecycle === "published") return "ok";
  if (lifecycle === "superseded") return "danger";
  return undefined;
}

/* ── Ref kind extraction ── */

export type RefKind = "item" | "decision" | "meeting" | "artifact" | "observation" | "unknown";

const REF_PREFIX_TO_KIND: Record<string, RefKind> = {
  item: "item",
  action_item: "item",
  risk: "item",
  dependency: "item",
  workstream: "item",
  milestone: "item",
  signal: "item",
  decision: "decision",
  meeting: "meeting",
  artifact: "artifact",
  observation: "observation",
};

export function refKind(ref: string): RefKind {
  const colon = ref.indexOf(":");
  if (colon < 0) return "unknown";
  const prefix = ref.slice(0, colon);
  return REF_PREFIX_TO_KIND[prefix] ?? "unknown";
}

/* ── Human ref labels for claim chips (no raw hashes on glass) ── */

/** Plain-words label for a ref prefix. */
const REF_PREFIX_LABELS: Record<string, string> = {
  item: "Item",
  action_item: "Action item",
  risk: "Risk",
  dependency: "Dependency",
  workstream: "Workstream",
  milestone: "Milestone",
  signal: "Signal",
  decision: "Decision",
  meeting: "Meeting",
  artifact: "Artifact",
  observation: "Observation",
};

/** Fallback chip label when no claim text is available. */
export function refChipLabel(ref: string): string {
  const colon = ref.indexOf(":");
  if (colon < 0) return "Open";
  const prefix = ref.slice(0, colon);
  const kindWord = REF_PREFIX_LABELS[prefix];
  if (kindWord) return `Open ${kindWord.toLowerCase()}`;
  return "Open";
}

// HS-173-02: Jira-key pattern (ABC-123) and PR pattern (pr-123).
const JIRA_KEY_RE = /^[a-zA-Z]+-\d+$/;
const PR_REF_RE = /^pr-(\d+)$/i;
const MEETING_DATE_RE = /^(\d{4})-?(\d{2})-?(\d{2})/;
// An opaque record id: a prefix, an underscore, then a long hash.
const OPAQUE_ID_RE = /^[a-zA-Z]+_[0-9a-fA-F]{8,}$|^[0-9a-fA-F]{12,}$/;

/** Short identity label for a ref, matching the board grammar:
 *  `PR #612`, `KAN-7`, `MTG 09-05`. One chip per ref. */
export function refIdentityLabel(ref: string): string {
  const colon = ref.indexOf(":");
  if (colon < 0) return ref;
  const prefix = ref.slice(0, colon);
  const id = ref.slice(colon + 1);

  // Meeting refs: MTG MM-DD (from the meeting id or a date-like id)
  if (prefix === "meeting") {
    const dateMatch = id.match(MEETING_DATE_RE);
    if (dateMatch) {
      return `MTG ${dateMatch[2]}-${dateMatch[3]}`;
    }
    return `MTG ${id}`.toUpperCase();
  }

  // PR refs: PR #<number>
  const prMatch = id.match(PR_REF_RE);
  if (prMatch) return `PR #${prMatch[1]}`;

  // Jira-key refs: uppercase (KAN-7)
  if (JIRA_KEY_RE.test(id)) return id.toUpperCase();

  // HS-200-06: a record id is not an identity. An opaque id (the
  // hashed ids real Projects carry) shows its kind word, never the
  // raw hash -- 162's no-raw-ids law.
  if (OPAQUE_ID_RE.test(id)) {
    const kindWord = REF_PREFIX_LABELS[prefix];
    return (kindWord ?? prefix).toUpperCase();
  }

  // Fallback: uppercase the id
  return id.toUpperCase();
}

/** Strip a "Kind [severity]:" prefix from a claim text to get the
 *  core title. Patterns: "Risk [critical]: ...", "Dependency: ...",
 *  "Action item [high]: ...", bare "Something...". */
const CLAIM_PREFIX_RE = /^[A-Z][a-z]+(?:\s+[a-z]+)?(?:\s*\[[^\]]+\])?\s*:\s*/;

/** Derive a short human identity from a claim's text for a source chip.
 *  Strips the kind/severity prefix, truncates to ~32 chars with ellipsis.
 *  Returns null when the text is empty/unusable (caller falls back to
 *  refChipLabel). */
export function claimChipTitle(claimText: string | undefined, maxLen = 32): string | null {
  if (!claimText || !claimText.trim()) return null;
  const stripped = claimText.replace(CLAIM_PREFIX_RE, "").trim();
  if (!stripped) return null;
  if (stripped.length <= maxLen) return stripped;
  // Find the last space before maxLen to avoid mid-word cut
  const cut = stripped.lastIndexOf(" ", maxLen);
  const end = cut > maxLen * 0.5 ? cut : maxLen;
  return stripped.slice(0, end) + "…";
}

/* ── Fallback reason humanization (closed table) ── */

const FALLBACK_REASON_LABELS: Record<string, string> = {
  model_unavailable: "Model unavailable",
  no_output: "Model produced no output",
  unparseable_output: "Model output unusable",
};

/** Human-words label for a fallback reason code. Unknown codes show
 *  with generic phrasing, never raw machine text. */
export function humanFallbackReason(code: string | null): string | null {
  if (!code) return null;
  const label = FALLBACK_REASON_LABELS[code];
  if (label) return `${label} -- drafted deterministically`;
  // Unknown code: generic phrasing
  return `Fallback: ${code.replace(/_/g, " ")} -- drafted deterministically`;
}
