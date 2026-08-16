import "./inline-editor.css";
import { useState } from "react";
import { FirstWords } from "./FirstWords";
import { DeskStartActions } from "./DeskStartActions";
import { useDesk } from "../store";
import { egressBadge } from "../setup";
import { SYSTEM } from "../systemSprites";
import { useDeskWriteReceipt } from "../hooks/useWriteReceipt";

// HS-100-10 — the arrival (thesis §2): the two modes as start verbs and
// ONE trust line. No headline prose, no checklist wall (Article VII).
export function EmptyDesk({
  arrivalRequired = false,
}: {
  arrivalRequired?: boolean;
}) {
  const [continued, setContinued] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const setup = useDesk((s) => s.setup);
  const badge = egressBadge(setup);
  // HS-132-06 — the empty floor's own receipt line: a refused New Note or
  // Seed names itself here, in flow under the start verbs.
  const { receipt: writeReceipt } = useDeskWriteReceipt();
  return (
    <div
      className={`desk-empty${arrivalRequired && !continued ? " is-first-value" : ""}`}
    >
      <img
        className="desk-empty-mark desk-chrome-sprite"
        src={SYSTEM.menuMark}
        alt=""
        width={32}
        height={32}
        draggable={false}
        aria-hidden="true"
      />
      <DeskStartActions />
      <button
        type="button"
        className="desk-chip desk-start-action is-primary"
        onClick={() => void useDesk.getState().createPrimitive("note")}
      >
        <span aria-hidden="true">＋</span> New Note
      </button>
      <p className="desk-empty-line">or right-click for more options</p>
      {/* HS-112-03 — the empty floor's start verb: the architect's desk
          in one press (additive seed; the drawers materialize). */}
      <button
        type="button"
        className="desk-chip desk-start-action"
        disabled={seeding}
        onClick={() => {
          setSeeding(true);
          void useDesk
            .getState()
            .seedDesk()
            .finally(() => setSeeding(false));
        }}
      >
        <span aria-hidden="true">▤</span>{" "}
        {seeding ? "Seeding…" : "Seed the desk"}
      </button>
      {writeReceipt ? (
        <div className="write-receipt-row">{writeReceipt}</div>
      ) : null}
      <p className={`desk-empty-trust is-${badge.scope}`} title={badge.title}>
        <span className="desk-empty-trust-dot" aria-hidden="true" />
        {badge.scope === "local"
          ? "Everything runs on this device"
          : badge.text}
      </p>
      {arrivalRequired && !continued ? (
        <FirstWords embedded onDismiss={() => setContinued(true)} />
      ) : null}
    </div>
  );
}
