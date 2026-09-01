// HS-162-05 -- the Update posture types: decode the wire shapes from
// tests/integration/test_update_routes.py (the fixture truth).
// claims_json carries the claim array; each claim resolves to openable
// source refs (paying 160's S-4 debt).

/* ── Wire update shape (from project_updates table rows) ── */

export type UpdateLifecycle = "draft" | "published" | "superseded";

export type UpdateClaim = {
  spanId: string;
  text: string;
  refs: string[];
  section: string;
  verified: boolean;
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
  fallbackReason: string | null;
  createdAt: string;
  updatedAt: string;
  publishedAt: string | null;
};

export function decodeClaim(raw: Record<string, unknown>): UpdateClaim {
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
  };
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

/** Build a human chip label for a claim ref. The raw id is NEVER shown
 *  on glass -- only the kind in plain words. When the claim's own text
 *  is available (it always is), "Open <kind>" is sufficient because the
 *  claim text already names the thing. */
export function refChipLabel(ref: string): string {
  const colon = ref.indexOf(":");
  if (colon < 0) return "Open";
  const prefix = ref.slice(0, colon);
  const kindWord = REF_PREFIX_LABELS[prefix];
  if (kindWord) return `Open ${kindWord.toLowerCase()}`;
  return "Open";
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
