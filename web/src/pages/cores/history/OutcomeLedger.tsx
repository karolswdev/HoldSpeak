/* The meeting's outcome rows (Phase 16, the interior kit): a Section over a
 * Ledger, one row per decision or commitment. Betterment Q9: its own module,
 * so a note's Find the tasks draws the same rows without the meeting
 * window's code. */
import type { ReactNode } from "react";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceSection } from "../../../desk/surface";

/** One row of the meeting's outcomes ledgers (Betterment Q9: a note's
 *  Find the tasks draws the same rows). */
export type OutcomeRow = {
  key: string;
  plate: "DEC" | "ACT";
  text: string;
  meta: string;
  tone?: "ask" | "ok";
  actionItemId?: string;
  proposalId?: string;
  /** A decision row: the record it has (`decision_record` id), else the
   *  decision the meeting recorded (`decisions` id). W2-LIVE-2: Decide… opens
   *  the record, else the decision's reader, else New decision. */
  recordId?: string | null;
  decisionId?: string | null;
  actionStatus?: string | null;
  owner?: string;
  due?: string;
  projectId?: string | null;
  personRelationshipId?: string | null;
  segmentIndex?: number | null;
  gap?: boolean;
  deferredUntil?: string | null;
  verbs?: ReactNode;
  children?: ReactNode;
};


export function OutcomeLedger({ label, rows, testId, controls }: { label: string; rows: OutcomeRow[]; testId: string; controls?: ReactNode }) {
  if (!rows.length) return null;
  return (
    <SurfaceSection label={label} count={rows.length || null} data-testid={testId} className="meeting-outcome-section">
      <SurfaceLedger label={label} cols="meeting-outcomes" controls={controls}>
        <ul className="surface-ledger-rows">
          {rows.map((row) => (
            <SurfaceLedgerRow
              key={row.key}
              data-testid={`${testId}-row`}
              primary={row.text}
              meta={row.meta}
              metaTone={row.tone}
              trailing={row.verbs}
              wrap
              open={Boolean(row.children)}
              expands={false}
            >{row.children}</SurfaceLedgerRow>
          ))}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

