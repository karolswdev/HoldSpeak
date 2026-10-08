/** PHILO-14 B1 — ConfirmLine: the YOLO hand in one line (board A-3).
 *
 *  The item's sprite → the agent's sprite, the item's title (primary
 *  step), the fact line (`CLAUDE CODE · YOLO · hs/write-the-cutover-comms`,
 *  mono), and the three verbs: **Brief ▸** (the brief one press away),
 *  **Cancel**, **Hand** (primary). A sunken well: it sits in the drawer, at
 *  the top, while the drop waits for the press.
 */
import type { ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { listSprite } from "../../sprites";
import { objectSprite } from "./kinds";
import "./objects.css";

export interface ConfirmEnd {
  kind: string;
  id: string;
  sprite?: string;
}

export interface ConfirmLineProps {
  from: ConfirmEnd;
  to: ConfirmEnd;
  title: string;
  /** The facts of the hand: agent · mode · branch. */
  fact: string;
  /** PHILO-15 16 (B39): the agent as a token the owner can flip (a library
   *  Button), drawn first on the fact line; `fact` then holds mode · branch. */
  agentToken?: ReactNode;
  onBrief?(): void;
  /** True while the brief is open (the Brief verb reads pressed). */
  briefOpen?: boolean;
  onCancel(): void;
  onHand(): void;
  /** The primary verb's word; default `Hand`. */
  handLabel?: string;
  busy?: boolean;
  /** PHILO-14 C3: Hand cannot be pressed (the preview refused, or is out). */
  disabled?: boolean;
  /** The egress chip of the hand, on the Hand side (where the brief goes). */
  egress?: ReactNode;
  /** A token line under the fact: a refusal, the tracker read, the receipt. */
  status?: ReactNode;
  /** The verbs after the press (Close, Send again): they replace the three. */
  verbs?: ReactNode;
}

export function ConfirmLine({
  from,
  to,
  title,
  fact,
  agentToken,
  onBrief,
  briefOpen,
  onCancel,
  onHand,
  handLabel = "Hand",
  busy,
  disabled,
  egress,
  status,
  verbs,
}: ConfirmLineProps) {
  return (
    <div className="confirm-line" role="group" aria-label={`Hand: ${title}`}>
      <span className="confirm-line-ends" aria-hidden="true">
        <img src={listSprite(from.sprite ?? objectSprite(from.kind, from.id))} alt="" draggable={false} />
        <span className="confirm-line-arrow">→</span>
        <img src={listSprite(to.sprite ?? objectSprite(to.kind, to.id))} alt="" draggable={false} />
      </span>
      <span className="confirm-line-what">
        <span className="confirm-line-title">{title}</span>
        <span className="confirm-line-fact">
          {agentToken ? (
            <>
              <span className="confirm-line-agent">{agentToken}</span>
              {fact ? <span aria-hidden="true">{" · "}</span> : null}
            </>
          ) : null}
          {fact}
        </span>
        {status ? <span className="confirm-line-status">{status}</span> : null}
      </span>
      {egress ? <span className="confirm-line-egress">{egress}</span> : null}
      <span className="object-verbs confirm-line-verbs">
        {verbs ?? (
          <>
            {onBrief ? (
              <Button dense variant="ghost" aria-expanded={briefOpen ? "true" : "false"} onClick={onBrief}>
                Brief ▸
              </Button>
            ) : null}
            <Button dense variant="ghost" onClick={onCancel} disabled={busy}>
              Cancel
            </Button>
            <Button dense variant="primary" onClick={onHand} loading={busy} disabled={disabled || busy}>
              {handLabel}
            </Button>
          </>
        )}
      </span>
    </div>
  );
}
