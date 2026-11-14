import { useState } from "react";
import { roomEditRows } from "../RoomEditFields";
import {
  InspectorForm,
  InspectorQuestion,
  InspectorFacts,
  SurfaceState,
  PaneInspector,
  StringGadget,
  type ListVerb,
} from "../../../desk/surface";
import { refOpener } from "../../../desk/openObject";
import { RoomList, roomFacts, roomObject } from "../RoomList";
import { kindLabel, humanFields, renderValue, type Proposal } from "./model";
import type { ReviewController } from "./useReviewController";

export function ReviewPosture({
  ctrl,
  onClose,
  projectName = "Project",
}: {
  ctrl: ReviewController;
  onClose?(): void;
  projectName?: string;
}) {
  const [mode, setMode] = useState(""),
    [armed, setArmed] = useState<string | null>(null);
  const proposal = ctrl.selectedProposal;
  const target = proposal
    ? `${ctrl.window?.reviewId}:${proposal.id}:${proposal.binding?.revision}:${JSON.stringify(proposal.patchJson)}`
    : "";
  const refusal = ctrl.error ? (
    <SurfaceState
      error={ctrl.error}
      retryLabel="Read again"
      onRetry={() => {
        setMode("");
        setArmed(null);
        void ctrl.enterReview(ctrl.window?.reviewId);
      }}
    />
  ) : undefined;
  const verbs: ListVerb[] = [
    {
      id: "accept",
      label: "Accept",
      enabled: () => Boolean(proposal) && !ctrl.decidingId,
      run: () => {
        if (proposal) void ctrl.acceptProposal(proposal.id);
      },
    },
    {
      id: "edit",
      label: "Edit and accept",
      enabled: () => Boolean(proposal),
      run: () => {
        if (proposal) {
          ctrl.startEdit();
          setMode("edit");
        }
      },
    },
    {
      id: "defer",
      label: "Defer",
      enabled: () => Boolean(proposal),
      run: () => setMode("defer"),
    },
    {
      id: "dismiss",
      label: "Dismiss",
      enabled: () => Boolean(proposal),
      run: () => setArmed(target),
    },
    {
      id: "undo",
      label: "Undo dismissal",
      enabled: () => ctrl.undoStack.length > 0,
      run: () => {
        void ctrl.undoLastDismiss();
      },
    },
    {
      id: "finish",
      label: "Finish review",
      enabled: () =>
        !ctrl.checkpointed && Boolean(ctrl.window) && !ctrl.decidingId,
      run: () => {
        void ctrl.finishReview();
      },
    },
    {
      enabled: () => true,
      id: "close",
      label: "Close review",
      run: () => {
        ctrl.exitReview();
        onClose?.();
      },
    },
  ];
  return (
    <RoomList
      label="Review"
      rows={ctrl.openProposals.map((row) => ({
        id: row.id,
        name: reviewName(row),
        kind: "decision",
        kindWord: kindLabel(row.proposalKind),
        cells: { state: row.lifecycle },
        facts: [
          {
            label: "From",
            value:
              row.targetRef === `project:${ctrl.window?.projectId}`
                ? projectName
                : undefined,
          },
          { label: "What it says", value: row.rationale },
          ...humanFields(row.patchJson).map((field) => ({
            label: field.label,
            value: renderValue(field.value),
          })),
        ],
        open: row.targetRef === `project:${ctrl.window?.projectId}` ? undefined : (refOpener(row.targetRef) ?? undefined),
      }))}
      selectedId={proposal?.id ?? null}
      onSelect={(id) => {
        const index = ctrl.openProposals.findIndex((row) => row.id === id);
        ctrl.selectByIndex(index);
        setMode("");
        setArmed(null);
      }}
      verbs={verbs}
      loading={ctrl.loading}
      retryLabel="Read again"
      retry={() => {
        void ctrl.enterReview(ctrl.window?.reviewId);
      }}
      empty={ctrl.checkpointed ? "Review saved" : "No proposals to review"}
    >
      {armed && armed === target && proposal ? (
        <InspectorQuestion
          actionId="remove"
          targetId={target}
          question={`Dismiss ${reviewName(proposal)}?`}
          notice={refusal}
          keeps={["Project records"]}
          cancel={() => setArmed(null)}
          onDisarm={() => setArmed(null)}
          verb={{
            label: "Dismiss",
            busy: Boolean(ctrl.decidingId),
            run: () => {
              void ctrl.dismissProposal(proposal.id).then(saved => {if(saved)setArmed(null);});
            },
          }}
        />
      ) : mode && proposal ? (
        <PaneInspector
          label={mode === "edit" ? "Edit proposal" : "Defer proposal"}
        >
          <InspectorForm
            notice={refusal}
            rows={
              mode === "defer"
                ? [
                    {
                      label: "Until",
                      control: (
                        <StringGadget
                          label="Until"
                          value={ctrl.deferDate}
                          onChange={ctrl.setDeferDate}
                        />
                      ),
                    },
                  ]
                : roomEditRows(proposal.editableFields ?? [], ctrl.editingPatch ?? {}, ctrl.updateEditField)
            }
            completion={{
              cancel: () => {
                setMode("");
                ctrl.cancelEdit();
              },
              primary: {
                label: mode === "edit" ? "Save and accept" : "Defer",
                busy: Boolean(ctrl.decidingId),
                run: () => {
                  const work =
                    mode === "edit"
                      ? ctrl.editAcceptProposal(
                          proposal.id,
                          ctrl.editingPatch ?? {},
                        )
                      : ctrl.deferProposal(
                          proposal.id,
                          ctrl.deferDate || undefined,
                        );
                  void work.then(saved => {if(saved)setMode("");});
                },
              },
            }}
          />
        </PaneInspector>
      ) : ctrl.error ? (
        <InspectorFacts object={roomObject({kind:"decision",id:proposal?.id ?? "review"})}
          name={proposal ? reviewName(proposal) : "Review"}
          rows={
            proposal
              ? roomFacts([
                  {
                    label: "From",
                    value: proposal.targetRef === `project:${ctrl.window?.projectId}`
                      ? projectName
                      : undefined,
                  },
                  { label: "What it says", value: proposal.rationale },
                ])
              : []
          }
          notice={refusal}
          data-feedback-redact="true"
        />
      ) : undefined}
    </RoomList>
  );
}

function reviewName(row: Proposal): string {
  return String(row.patchJson.text || row.patchJson.title || row.patchJson.owner ||
    (row.title.startsWith(`${row.proposalKind}:`) ? kindLabel(row.proposalKind) : row.title));
}
