/** LedgerRemainder (HS-200-15, species S4 of the daily-workflow design) —
 *  the cap and the remainder, as one grammar: the true total lives in the
 *  head, the cap in the section caption (`NEEDS YOU 5 OF 17`), and the
 *  remainder is THIS row — a real count and a real verb:
 *
 *      12 MORE · Show all
 *
 *  Pressing it reveals the rest IN PLACE (never a modal, A.4) and the verb
 *  turns into `Show fewer`, which leads back. `Escape` inside the revealed
 *  rows is the caller's to wire back to this verb (`ref`).
 *
 *  Rules the species enforces:
 *
 *  - **Nothing at zero.** `remaining <= 0` renders nothing (A.8); the
 *    caller never has to guard it.
 *  - **The count is `countToken`** — the one way a face says "N things".
 *  - **Every verb is the library Button** (A.1).
 */
import { forwardRef } from "react";
import { Button } from "../../../components/signal/Signal";
import { countToken } from "../count";
import "./ledger-remainder.css";

export interface LedgerRemainderProps {
  /** How many rows are NOT shown while collapsed. */
  remaining: number;
  expanded: boolean;
  onToggle: () => void;
  /** The noun for the count (`MORE` by default). */
  noun?: string;
  /** The verb's accessible name subject (`the remaining 12`). */
  subject?: string;
  "data-testid"?: string;
}

export const LedgerRemainder = forwardRef<HTMLButtonElement, LedgerRemainderProps>(
  function LedgerRemainder(
    {
      remaining,
      expanded,
      onToggle,
      noun = "MORE",
      subject,
      "data-testid": dataTestId = "ledger-remainder",
    },
    ref,
  ) {
    if (remaining <= 0) return null;
    const token = countToken(remaining, noun, noun);
    const what = subject ?? `the remaining ${remaining}`;
    return (
      <div className="surface-ledger-remainder" data-testid={dataTestId}>
        {!expanded && token ? (
          <span className="surface-ledger-remainder-count" data-testid={`${dataTestId}-count`}>
            {token}
          </span>
        ) : null}
        <Button
          ref={ref}
          variant="ghost"
          dense
          aria-expanded={expanded}
          aria-label={expanded ? `Show fewer — hide ${what}` : `Show all — ${what}`}
          onClick={onToggle}
          data-testid={`${dataTestId}-verb`}
        >
          {expanded ? "Show fewer" : "Show all"}
        </Button>
      </div>
    );
  },
);
