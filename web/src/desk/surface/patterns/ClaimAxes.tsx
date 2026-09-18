/** ClaimAxes — the three INDEPENDENT axes of one claim (HS-200-06, C2),
 *  promoted to the library by HS-200-11 (design D2.0, species S2).
 *
 *  Kind · support · acceptance are three chips, never one.  A valid reference
 *  buys LINKED, not SUPPORTED; a model score can never raise acceptance; a
 *  literal the cited source does not carry is printed AND typed unsupported
 *  (`DEADLINE 2026-12-31 · NO SOURCE`).  The tokens live here so the brief,
 *  the update posture, the meeting review and recall all say the same word
 *  for the same fact. */
import { StateChip, type ChipState } from "./StateChip";
import "./claim-axes.css";

export type ClaimAxisToken = { label: string; state: ChipState };
export type ClaimUnknownValue = { type: string; value: string };

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

/** What the evidence establishes — with the honest history suffix:
 *  MIGRATED for a record mapped from a citation-only row, EDITED when the
 *  sentence changed after it was supported. */
export function claimSupportToken(axis: {
  support: string;
  edited?: boolean;
  migrated?: boolean;
}): ClaimAxisToken {
  if (axis.support === "supported") return { label: "SUPPORTED", state: "success" };
  if (axis.support === "disputed") return { label: "DISPUTED", state: "failure" };
  if (axis.support === "source_linked") {
    if (axis.edited) return { label: "LINKED · EDITED", state: "warning" };
    if (axis.migrated) return { label: "LINKED · MIGRATED", state: "idle" };
    return { label: "LINKED", state: "idle" };
  }
  return { label: "UNSUPPORTED", state: "warning" };
}

/** Applicable domain or reviewer judgment. Never inferred from a score. */
export function claimAcceptanceToken(acceptance: string): ClaimAxisToken {
  if (acceptance === "accepted") return { label: "ACCEPTED", state: "success" };
  if (acceptance === "rejected") return { label: "REJECTED", state: "failure" };
  if (acceptance === "superseded") return { label: "SUPERSEDED", state: "warning" };
  return { label: "UNREVIEWED", state: "idle" };
}

/** A typed unknown the cited source cannot carry: `DEADLINE 2026-12-31 · NO SOURCE`. */
export function claimUnknownToken(unknown: ClaimUnknownValue): string {
  return `${unknown.type.toUpperCase()} ${unknown.value} · NO SOURCE`;
}

export interface ClaimAxesProps {
  kind: string;
  support: string;
  acceptance: string;
  supportEdited?: boolean;
  supportMigrated?: boolean;
  unknowns?: ClaimUnknownValue[];
  /** The data-testid stem: `<stem>-axes`, `<stem>-kind`, `<stem>-support`,
   *  `<stem>-acceptance`, `<stem>-unknown`. */
  testIdPrefix?: string;
  className?: string;
}

export function ClaimAxes({
  kind,
  support,
  acceptance,
  supportEdited,
  supportMigrated,
  unknowns = [],
  testIdPrefix = "claim",
  className,
}: ClaimAxesProps) {
  const supportToken = claimSupportToken({ support, edited: supportEdited, migrated: supportMigrated });
  const acceptanceToken = claimAcceptanceToken(acceptance);
  return (
    <span
      className={className ? `surface-claim-axes ${className}` : "surface-claim-axes"}
      data-testid={`${testIdPrefix}-axes`}
    >
      <span className="surface-token" data-chip data-testid={`${testIdPrefix}-kind`} data-kind={kind}>
        {claimKindToken(kind)}
      </span>
      <span data-testid={`${testIdPrefix}-support`} data-support={support}>
        <StateChip state={supportToken.state} label={supportToken.label} />
      </span>
      <span data-testid={`${testIdPrefix}-acceptance`} data-acceptance={acceptance}>
        <StateChip state={acceptanceToken.state} label={acceptanceToken.label} />
      </span>
      {unknowns.map((unknown) => (
        <span key={`${unknown.type}:${unknown.value}`} data-testid={`${testIdPrefix}-unknown`}>
          <StateChip state="warning" label={claimUnknownToken(unknown)} />
        </span>
      ))}
    </span>
  );
}
