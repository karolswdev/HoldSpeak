// HS-117-09 — extracted from MeetingDetail (lines 749-776).
import { Button } from "../../../components/signal/Signal";
import {
  GadgetGroup,
  GadgetRow,
} from "../../../desk/surface/gadgets";
import { controlModeLabel } from "../../../lib/productLanguage";

export function AftercareGadgets({
  aftercare,
  authority,
  busy,
  proposeSlack,
}: {
  aftercare: Record<string, unknown>;
  authority: Record<string, unknown>;
  busy: boolean;
  proposeSlack: (what: "digest" | "followup") => Promise<void>;
}) {
  if (!aftercare.slack_configured) return null;
  return (
    <GadgetGroup label="Aftercare">
      <GadgetRow label="DIGEST → SLACK">
        <Button
          dense
          loading={busy}
          onClick={() => void proposeSlack("digest")}
        >
          Send
        </Button>
      </GadgetRow>
      <GadgetRow label="FOLLOW-UP → SLACK">
        <Button
          dense
          loading={busy}
          onClick={() => void proposeSlack("followup")}
        >
          Send
        </Button>
      </GadgetRow>
      <GadgetRow label="BASIS">
        <span className="surface-token">
          {controlModeLabel(String(authority.control_mode ?? "neutral"))}
        </span>
      </GadgetRow>
    </GadgetGroup>
  );
}
