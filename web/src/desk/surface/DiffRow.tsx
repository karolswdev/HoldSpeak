/* DiffRow (PG-LANG §3.8, §9.2, §11): one proposed change, one row.
 *
 * The op glyph (`+` add or amend, `~` change, `−` remove, `↕` move), the
 * where (`step 3 · merge`), before → after (values in mono), and the
 * verdict as a DotWord: Allowed, Lowers the bar, Refused, Changed since you
 * read it. A refused or conflicting row says its reason and its line under
 * the row (and shakes once as it lands). A row that lowers the bar has its
 * own verb, Apply this: his press per row, never a bulk one. 32 px; two
 * lines at the phone width. Rows fade in one after the other (`index`). */
import type { CSSProperties } from "react";
import { Button } from "../../components/signal/Signal";
import { DotWord } from "./kit";
import type { ObjectTone } from "./objects/kinds";
import "./change-well.css";

export type DiffOp = "add" | "change" | "remove" | "move" | "amend";
export type DiffVerdict = "allowed" | "refused" | "conflict" | "lowers";

const GLYPH: Record<DiffOp, string> = { add: "+", amend: "+", change: "~", remove: "−", move: "↕" };
const OP_WORDS: Record<DiffOp, string> = { add: "Add", amend: "Add a line", change: "Change", remove: "Remove", move: "Move" };

export function verdictWords(verdict: DiffVerdict, allowedByYou = false): { word: string; tone: ObjectTone } {
  if (verdict === "lowers") return allowedByYou ? { word: "Allowed by you", tone: "ok" } : { word: "Lowers the bar", tone: "warn" };
  if (verdict === "refused") return { word: "Refused", tone: "fail" };
  if (verdict === "conflict") return { word: "Changed since you read it", tone: "fail" };
  return { word: "Allowed", tone: "ok" };
}

export function DiffRow({
  op,
  where,
  field,
  before,
  after,
  verdict,
  reason,
  line,
  pressed = false,
  onPress,
  index = 0,
  disabled,
  "data-testid": testId,
  "data-row": rowId,
}: {
  op: DiffOp;
  /** `step 3`, `program`, `R6`. */
  where: string;
  /** The statement the row changes (`merge`, `agent`), when it is one field. */
  field?: string;
  before?: string;
  after?: string;
  verdict: DiffVerdict;
  /** A refusal's or a conflict's words (`Step 2 · brief: The agent has read it.`). */
  reason?: string | null;
  /** The line of the text the row is about (1-based). */
  line?: number | null;
  /** A row that lowers the bar: he pressed Apply this. */
  pressed?: boolean;
  /** Apply this (and its undo) on a row that lowers the bar. */
  onPress?(next: boolean): void;
  /** The row's place in the well (the landing order). */
  index?: number;
  disabled?: boolean;
  "data-testid"?: string;
  "data-row"?: string;
}) {
  const { word, tone } = verdictWords(verdict, pressed);
  const blocked = verdict === "refused" || verdict === "conflict";
  const values = before && after ? "both" : after ? "after" : before ? "before" : "";
  return (
    <li className="kit-diffrow" data-op={op} data-verdict={verdict} data-pressed={pressed ? "" : undefined}
      style={{ "--i": index } as CSSProperties} data-testid={testId} data-row={rowId}>
      <span className="kit-diffrow-glyph" title={OP_WORDS[op]} aria-label={OP_WORDS[op]}>{GLYPH[op]}</span>
      <span className="kit-diffrow-where">{field ? `${where} · ${field}` : where}</span>
      <span className="kit-diffrow-values" data-values={values || undefined}>
        {before ? <code className="kit-diffrow-value" data-side="before" title={before}>{before}</code> : null}
        {before && after ? <span className="kit-diffrow-to" aria-label="to">→</span> : null}
        {after ? <code className="kit-diffrow-value" data-side="after" title={after}>{after}</code> : null}
      </span>
      <DotWord tone={tone} className="kit-diffrow-verdict" data-testid="kit-diffrow-verdict">{word}</DotWord>
      <span className="kit-diffrow-verb">
        {verdict === "lowers" && onPress ? (
          <Button dense variant={pressed ? "ghost" : "secondary"} aria-pressed={pressed} disabled={disabled}
            onClick={() => onPress(!pressed)} data-testid="kit-diffrow-apply-this">
            {pressed ? "Undo" : "Apply this"}
          </Button>
        ) : null}
      </span>
      {blocked && reason ? (
        <span className="kit-diffrow-reason" data-testid="kit-diffrow-reason">
          {line ? <span className="kit-diffrow-line">Line {line}</span> : null}
          {reason}
        </span>
      ) : null}
    </li>
  );
}
