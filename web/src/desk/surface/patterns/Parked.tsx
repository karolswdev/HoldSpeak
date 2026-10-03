/** PHILO-13-02 (A1-F) — Park, never delete: the one receipt and the one
 *  Parked strip that Meetings and the Workbench window share (C1 artboard
 *  "Parked and Restore", boards C1-5a–j).
 *
 *  Every outcome is a compact receipt in the footer's receipt slot:
 *    PARKED hh:mm + Restore · PARKED n · hh:mm + Restore (bulk)
 *    RESTORED hh:mm · NOT RESTORED · <why> + Retry · NOT PARKED · <why>
 *  The strip is a `PARKED n` token (absent at zero) that, when on, lists
 *  the parked rows with their own Restore. */
import { Button } from "../../../components/signal/Signal";
import { CheckGadget } from "../gadgets";
import { SurfaceLedger, SurfaceLedgerRow } from "../Surface";
import "./parked.css";

export type ParkOutcome = {
  kind: "parked" | "restored" | "restore-failed" | "refused";
  text: string;
  /** The ids the receipt's Restore (or Retry) acts on. */
  ids: string[];
  tone?: "danger";
};

export type ParkedRow = { id: string; title: string; at: string };

/** hh:mm, the receipt clock. */
export function parkClock(at: Date = new Date()): string {
  return `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
}

/** The PARKED token: none at zero (UX-CANON A.8). */
export function parkedToken(n: number): string | null {
  return n > 0 ? `PARKED ${n}` : null;
}

export function parkedOutcome(ids: string[], at = parkClock()): ParkOutcome {
  const n = ids.length;
  return { kind: "parked", text: n > 1 ? `PARKED ${n} · ${at}` : `PARKED ${at}`, ids };
}

export function restoredOutcome(ids: string[], at = parkClock()): ParkOutcome {
  return { kind: "restored", text: `RESTORED ${at}`, ids };
}

export const RESTORE_REFUSED = "NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE";

export function restoreFailedOutcome(ids: string[]): ParkOutcome {
  return { kind: "restore-failed", text: RESTORE_REFUSED, ids, tone: "danger" };
}

export function notParkedOutcome(why: string): ParkOutcome {
  return { kind: "refused", text: `NOT PARKED · ${why}`, ids: [], tone: "danger" };
}

export function ParkReceipt({
  outcome,
  onRestore,
  "data-testid": testId,
}: {
  outcome: ParkOutcome;
  /** Restore (after a park) and Retry (after a refused restore). */
  onRestore: (ids: string[]) => void;
  "data-testid"?: string;
}) {
  return (
    <span className="park-receipt" data-testid={testId} data-outcome={outcome.kind}>
      <span className="surface-footer-receipt-line" role="status" data-tone={outcome.tone}>
        {outcome.text}
      </span>
      {outcome.kind === "parked" ? (
        <Button dense variant="ghost" onClick={() => onRestore(outcome.ids)}>
          Restore
        </Button>
      ) : null}
      {outcome.kind === "restore-failed" ? (
        <Button dense variant="ghost" onClick={() => onRestore(outcome.ids)}>
          Retry
        </Button>
      ) : null}
    </span>
  );
}

export function ParkedStrip({
  rows,
  on,
  onToggle,
  onRestore,
  "data-testid": testId,
}: {
  rows: ParkedRow[];
  on: boolean;
  onToggle: (next: boolean) => void;
  onRestore: (ids: string[]) => void;
  "data-testid"?: string;
}) {
  // No counter of zero (UX-CANON A.8): no token until something is parked.
  if (!rows.length) return null;
  return (
    <div className="parked-strip" data-testid={testId}>
      <div className="parked-strip-facet">
        <CheckGadget
          label={parkedToken(rows.length) ?? ""}
          variant="token"
          checked={on}
          onChange={onToggle}
        />
      </div>
      {on ? (
        <SurfaceLedger count={null} cols="room">
          {rows.map((row) => (
            <SurfaceLedgerRow
              key={row.id}
              time={row.at}
              primary={row.title}
              lineLabel={row.title}
              cells={<span className="desk-chip parked-strip-chip">PARKED</span>}
              trailing={
                <Button dense variant="ghost" onClick={() => onRestore([row.id])}>
                  Restore
                </Button>
              }
              expands={false}
              data-testid="parked-row"
            />
          ))}
        </SurfaceLedger>
      ) : null}
    </div>
  );
}
