/* Hand to agent on a Door or Room row (the Conductor canvas K2d/K2e): the
 * row's item opens the launch sheet. A row whose item `agent.hand` cannot
 * take has no verb (UX-CANON A.11). */
import { Button } from "../../components/signal/Signal";
import { handOriginOfRow, openHand, type HandRowItem } from "../agentHand";

export function HandRowVerb({ item }: { item: HandRowItem }) {
  const origin = handOriginOfRow(item);
  if (!origin) return null;
  return (
    <Button
      dense
      variant="ghost"
      aria-label={`Hand to agent: ${origin.title}`}
      data-testid="hand-row-verb"
      onClick={() => openHand(origin)}
    >
      Hand to agent
    </Button>
  );
}
