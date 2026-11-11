import { useEffect, useReducer, useRef } from "react";
import {
  EgressChip,
  InspectorFacts,
  InspectorForm,
  PaneInspector,
  PadGadget,
} from "../../desk/surface";
import {
  SendWells,
  pickDestination,
  type DocRef,
} from "../../desk/surface/send";
import type {
  RoomHealthPerson,
  RoomNeedsYouItem,
  RoomNudgeDestination,
  NudgeLocal,
} from "./model";
import { nudgeCardReducer, initialNudgeCard } from "./model";
import * as api from "./api";
export function NudgeCard({
  person,
  needsYouItem,
  nudgeItem,
  onReload,
  onSent,
  persistedState,
  local,
  onLocal,
}: {
  person: RoomHealthPerson | undefined;
  needsYouItem: RoomNeedsYouItem;
  nudgeItem: api.NudgeItem | undefined;
  onReload(): void;
  onSent?(): void;
  persistedState?: string | null;
  local?: NudgeLocal;
  onLocal?(value: NudgeLocal): void;
}) {
  const displayName = person?.displayName || needsYouItem.title;
  const prNumber =
    nudgeItem?.pr_number ??
    person?.nudge?.prNumber ??
    person?.prs?.[0]?.number ??
    0;
  const prUrl = nudgeItem?.pr_url ?? person?.prs?.[0]?.url ?? "";
  const stepId = nudgeItem?.step_id ?? person?.nudge?.stepId ?? "";
  const defaultText =
    nudgeItem?.comment_text ||
    person?.nudge?.text ||
    `This PR has been waiting for review for ${Math.round(person?.medianDays || needsYouItem.medianDays || 1)} days. Flagged by HoldSpeak.`;
  const [card, dispatch] = useReducer(
    nudgeCardReducer,
    initialNudgeCard(
      local?.state ?? persistedState ?? nudgeItem?.state,
      defaultText,
      prNumber,
      {
        displayName,
        sentAt: local?.sentAt,
        reason: local?.reason,
        text: local?.text,
      },
    ),
  );
  const pending = useRef(false);
  const send = async () => {
    if (
      pending.current ||
      !stepId ||
      (card.phase !== "open" && card.phase !== "failed")
    )
      return;
    pending.current = true;
    const text = card.text;
    dispatch({ type: "sending" });
    onLocal?.({ state: "pending", text });
    try {
      const result = await api.sendNudge(stepId, text);
      if (result.success) {
        const sentAt =
          typeof result.sent_at === "string"
            ? result.sent_at
            : new Date().toISOString();
        dispatch({ type: "sent", displayName, prNumber, sentAt });
        onLocal?.({ state: "sent", sentAt });
        onSent?.();
      } else if (result.outcome === "unknown") {
        dispatch({ type: "unknown", prNumber });
        onLocal?.({ state: "unknown" });
      } else {
        const reason = String(result.message || "Send failed");
        dispatch({ type: "failed", reason });
        onLocal?.({ state: "failed", reason, text });
      }
    } catch {
      // A lost reply cannot prove that the external comment was not posted.
      dispatch({ type: "unknown", prNumber });
      onLocal?.({ state: "unknown" });
    } finally {
      pending.current = false;
    }
  };
  if (card.phase === "closed") return null;
  if (card.phase === "sent" || card.phase === "unknown")
    return (
      <PaneInspector label="Nudge">
        <InspectorForm
          rows={[
            {
              label: "State",
              control: card.phase === "sent" ? "Sent" : "Result unknown",
            },
            { label: "To", control: displayName },
            { label: "Pull request", control: prNumber ? `#${prNumber}` : "" },
          ]}
          completion={{
            cancel: onReload,
            primary: {
              label: "Open PR",
              run: () => {
                if (prUrl) window.open(prUrl, "_blank", "noopener");
              },
              disabled: !prUrl,
            },
          }}
        />
      </PaneInspector>
    );
  return (
    <PaneInspector label="Nudge">
      <InspectorForm
        rows={[
          {
            label: "Text",
            control: (
              <PadGadget
                label="Comment"
                value={card.text}
                onChange={(text) => dispatch({ type: "setText", text })}
              />
            ),
          },
          { label: "To", control: prUrl },
          {
            label: "State",
            control: card.phase === "failed" ? card.reason : "",
          },
        ]}
        completion={{
          cancel: () => {
            void (stepId ? api.dismissNudge(stepId) : Promise.resolve()).then(
              () => {
                dispatch({ type: "dismiss" });
                onReload();
              },
            );
          },
          leading: <EgressChip scope="cloud" label="github.com" />,
          primary: {
            label: "Send",
            disabled: !card.text.trim() || !stepId,
            busy: card.phase === "open" && card.busy,
            run: () => {
              void send();
            },
          },
        }}
      />
    </PaneInspector>
  );
}
export function GenericNudgeCard({ nudge }: { nudge: RoomNudgeDestination }) {
  const doc: DocRef = {
    ref: nudge.documentRef,
    title: nudge.title,
    label: "NUDGE",
  };
  useEffect(() => {
    pickDestination(nudge.documentRef, nudge.destinationId);
  }, [nudge.documentRef, nudge.destinationId]);
  return <SendWells doc={doc} destinationIds={[nudge.destinationId]} />;
}
