// HS-117-09 — extracted from MeetingDetail (lines 718-738).
import { rowId } from "../../pageSupport";
import { presentValue } from "../../../desk/surface/format";
import { countLabel } from "../../../desk/surface";

export function SettledList({
  settledActions,
}: {
  settledActions: Record<string, unknown>[];
}) {
  if (!settledActions.length) return null;
  return (
    <div className="surface-outcome-sec">
      <span className="surface-eyebrow">
        {countLabel("SETTLED", settledActions.length)}
      </span>
      <ul className="surface-settled">
        {settledActions.map((row, index) => (
          <li key={rowId(row, index)}>
            <span aria-hidden="true">✓</span>
            <span>
              {String(row.text ?? row.title ?? "Action item")}
              {presentValue(row.owner)
                ? ` · ${presentValue(row.owner)}`
                : ""}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
