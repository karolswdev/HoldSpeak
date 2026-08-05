// HS-117-09 — extracted from MeetingDetail (lines 552-574).
import { stateToken } from "./helpers";
import {
  GadgetGroup,
  GadgetRow,
} from "../../../desk/surface/gadgets";

export function CaptureSlab({
  detail,
  meeting,
}: {
  detail: Record<string, unknown> | null;
  meeting: Record<string, unknown>;
}) {
  const captureBad =
    Boolean(detail?.capture_status) && detail?.capture_status !== "finalized";
  if (!captureBad) return null;
  return (
    <GadgetGroup label="Capture">
      <GadgetRow
        label={
          <span
            className="surface-token"
            data-tone={stateToken(detail ?? meeting).tone ?? "warn"}
          >
            {String(detail?.capture_status ?? "").replace(/_/g, " ").toUpperCase()}
          </span>
        }
        fact={
          detail?.capture_failure
            ? String(detail.capture_failure)
            : undefined
        }
      >
        <span className="gadget-fact">
          TRANSCRIPT RETAINED · LAST DURABLE CHECKPOINT
        </span>
      </GadgetRow>
    </GadgetGroup>
  );
}
