import { useState } from "react";
import { FirstWords } from "./FirstWords";
import { DeskStartActions } from "./DeskStartActions";

// The fresh Desk leads with its three daily actions. The optional first-value
// dictation exercise stays below those actions instead of replacing the front
// door with an onboarding lesson.
export function EmptyDesk({
  arrivalRequired = false,
}: {
  arrivalRequired?: boolean;
}) {
  const [continued, setContinued] = useState(false);
  return (
    <div
      className={`desk-empty${arrivalRequired && !continued ? " is-first-value" : ""}`}
    >
      <div className="desk-empty-mark" aria-hidden="true">
        ◍
      </div>
      <h1 className="desk-empty-word">Start on your Desk</h1>
      <p className="desk-empty-line">
        Dictate text, record a meeting, or create a Desk item.
      </p>
      <DeskStartActions />
      {arrivalRequired && !continued ? (
        <FirstWords embedded onDismiss={() => setContinued(true)} />
      ) : null}
    </div>
  );
}
