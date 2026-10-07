/** PHILO-14 B1 — ConfirmLine: the YOLO hand in one line (board A-3).
 *
 *  The item's sprite → the agent's sprite, the item's title (primary
 *  step), the fact line (`CLAUDE CODE · YOLO · hs/write-the-cutover-comms`,
 *  mono), and the three verbs: **Brief ▸** (the brief one press away),
 *  **Cancel**, **Hand** (primary). A sunken well: it sits in the drawer, at
 *  the top, while the drop waits for the press.
 */
import { Button } from "../../../components/signal/Signal";
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
  onBrief?(): void;
  /** True while the brief is open (the Brief verb reads pressed). */
  briefOpen?: boolean;
  onCancel(): void;
  onHand(): void;
  /** The primary verb's word; default `Hand`. */
  handLabel?: string;
  busy?: boolean;
}

export function ConfirmLine({
  from,
  to,
  title,
  fact,
  onBrief,
  briefOpen,
  onCancel,
  onHand,
  handLabel = "Hand",
  busy,
}: ConfirmLineProps) {
  return (
    <div className="confirm-line" role="group" aria-label={`Hand: ${title}`}>
      <span className="confirm-line-ends" aria-hidden="true">
        <img src={from.sprite ?? objectSprite(from.kind, from.id)} alt="" draggable={false} />
        <span className="confirm-line-arrow">→</span>
        <img src={to.sprite ?? objectSprite(to.kind, to.id)} alt="" draggable={false} />
      </span>
      <span className="confirm-line-what">
        <span className="confirm-line-title">{title}</span>
        <span className="confirm-line-fact">{fact}</span>
      </span>
      <span className="object-verbs confirm-line-verbs">
        {onBrief ? (
          <Button dense variant="ghost" aria-expanded={briefOpen ? "true" : "false"} onClick={onBrief}>
            Brief ▸
          </Button>
        ) : null}
        <Button dense variant="ghost" onClick={onCancel} disabled={busy}>
          Cancel
        </Button>
        <Button dense variant="primary" onClick={onHand} loading={busy}>
          {handLabel}
        </Button>
      </span>
    </div>
  );
}
