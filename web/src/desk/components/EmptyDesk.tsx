import { useState } from "react";
import { FirstWords } from "./FirstWords";
import { DeskStartActions } from "./DeskStartActions";
import { useDesk } from "../store";
import { egressBadge } from "../setup";

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
  return (
    <div
      className={`desk-empty${arrivalRequired && !continued ? " is-first-value" : ""}`}
    >
      <div className="desk-empty-mark" aria-hidden="true">
        ◍
      </div>
      <DeskStartActions />
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
        <span aria-hidden="true">▤</span> {seeding ? "Seeding…" : "Seed the desk"}
      </button>
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
