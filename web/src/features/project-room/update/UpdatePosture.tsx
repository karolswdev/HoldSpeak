import { useCallback, useEffect, useState, type ReactNode } from "react";
import {
  InspectorForm,
  PaneViews,
  ObjectReader,
  ReadingDocument,
  PadGadget,
  PaneInspector,
  PreferencePane,
  StatusBar,
  RunLine,
  StringGadget,
  type ListVerb,
  wireDayClock,
} from "../../../desk/surface";
import { openRef, refOpener } from "../../../desk/openObject";
import { openSurfaceOr } from "../../../desk/shell";
import { useEngine } from "../../../desk/hooks/useEngine";
import { refusedWord } from "../../channels/channels";
import { updateDoc } from "../../channels/SendWell";
import { SendWells } from "../../../desk/surface/send";
import { PaneViewContext } from "../../../desk/surface/patterns/PaneViews";
import { RoomList, roomReadingText, roomClaimWords, roomWord, type RoomEntry } from "../RoomList";
import type { UpdateController } from "./useUpdateController";
import {
  generatorLabel,
  lifecycleLabel,
  claimSends,
  claimSourceKind,
  refChipLabel,
  refIdentityLabel,
  type ProjectUpdate,
} from "./model";

export function generatorChipBoundary(update: {
  generator: string;
  generatorModel?: string | null;
  generatorHost?: string | null;
}): string | undefined {
  return update.generator.startsWith("model:")
    ? update.generatorModel?.trim() || undefined
    : undefined;
}
export function draftWords(engine: { state: string; model: string }): string {
  return `${engine.state === "set" && engine.model ? engine.model : "HoldSpeak"} drafts from the sources · you send`;
}
export function updateName(row: ProjectUpdate): string {
  return [wireDayClock(row.publishedAt || row.updatedAt || row.createdAt), row.audience || row.deliveries.map(delivery => delivery.deliveredTo).filter(Boolean).join(", ") || "Audience not named"].filter(Boolean).join(" · ") || "Project update";
}
export function UpdatePosture({
  ctrl,
  projectActions = [],
  sourceItems = [],
  field,
  sendUpdateId,
  linkFailure,
  onSendState,
  projectViews = [],
  onProjectView,
}: {
  projectViews?: readonly {id: string; label: string}[];
  onProjectView?(id: string): void;
  ctrl: UpdateController;
  projectActions?: ListVerb[];
  sourceItems?: readonly Pick<RoomEntry, "id" | "kind">[];
  field?: ReactNode;
  sendUpdateId?: string | null;
  linkFailure?: { retry(): void };
  onSendState?(open: boolean): void;
}) {
  const [seat, setSeat] = useState("updates"),
    [picked, setPicked] = useState<string | null>(null);
  const current = linkFailure ? null : ctrl.current;
  useEffect(() => { onSendState?.(Boolean(current && (seat === "send" || seat === "delivery"))); return () => onSendState?.(false); }, [Boolean(current), seat, onSendState]);
  useEffect(() => {
    if (sendUpdateId) setSeat("send");
  }, [sendUpdateId]);
  const afterSend = useCallback(() => {
    void ctrl.reloadDeliveries();
  }, [ctrl.reloadDeliveries]);
  const engine = useEngine("project.update_draft");
  const claim = seat === "claims" ? current?.claims.find((row) => row.spanId === picked) : undefined;
  const rows: RoomEntry[] =
    seat === "claims" && current
      ? current.claims.map((row) => ({
          id: row.spanId,
          ...roomClaimWords(row.text),
          kind: row.kind,
          kindWord: row.kind.replaceAll("_", " "),
          cells: {
            state:
              row.acceptance === "unreviewed"
                ? claimSends(row)
                  ? "Source linked"
                  : "Needs review"
                : row.acceptance,
          },
          facts: [
            { label: "What it says", value: row.text },
            { label: "Kind", value: row.kind.replaceAll("_", " ") },
            { label: "Support", value: row.support.replaceAll("_", " ") },
            { label: "Acceptance", value: row.acceptance },
            { label: "Send", value: claimSends(row) ? "Included" : "Omitted" },
            { label: "Sources", value: row.refs.map(refIdentityLabel).join(" · ") },
            ...row.unknowns.map((unknown, i) => ({
              key: String(i),
              label: "Not known",
              value: `${unknown.type.replaceAll("_", " ")}: ${unknown.value}`,
            })),
          ],
          open: row.refs[0] ? (refOpener(row.refs[0]) ?? undefined) : undefined,
        }))
      : seat === "sources" && current
        ? [...new Set(current.claims.flatMap((row) => row.refs))].map(
            (ref) => {
              const claims = current.claims.filter((claim) => claim.refs.includes(ref));
              const item = sourceItems.find(item => ref === `item:${item.id}`);
              const kind = item ? roomWord(item.kind) : claimSourceKind(ref, claims[0]?.text || "");
              const checkedAt = claims.find((claim) => claim.supportRecord?.checkedAt)?.supportRecord?.checkedAt;
              const revision = claims[0]?.supportRecord?.sourceVersion.match(/@r?(\d+)$/)?.[1];
              return {
                id: ref,
                ...roomClaimWords(claims[0]?.text || refChipLabel(ref)),
                kind: "artifact",
                kindWord: kind,
                facts: [
                  { label: "Kind", value: kind },
                  { label: "From", value: ref.startsWith("item:") ? "Project plan" : refIdentityLabel(ref) },
                  { label: "Revision", value: revision },
                  { label: "Checked", value: checkedAt },
                ],
                open: refOpener(ref) ?? undefined,
              };
            },
          )
        : ctrl.updates.map((row) => ({
            id: row.id,
            name: updateName(row),
            kind: "artifact",
            facts: [
              { label: "State", value: lifecycleLabel(row.lifecycle) },
              {
                label: "From",
                value: generatorLabel(row.generator, row.generatorModel).replace(/^From /, ""),
              },
            ],
            open: () => ctrl.openUpdate(row),
          }));
  const draft = () => {
    void ctrl.write(engine.state === "set");
    setSeat("updates");
  };
  const verbs: ListVerb[] = [
    ...(projectActions.length
      ? projectActions
      : [
          {
            id: "draft",
            label: "Draft update",
            run: draft,
            enabled: () => !ctrl.draftBusy && engine.state !== "unread",
          },
        ]),
    {
      id: "edit",
      label: "Edit",
      enabled: () => Boolean(current) && ctrl.isDraft,
      run: () => setSeat("edit"),
    },
    {
      id: "save",
      label: "Save",
      testId: "update-verb-save",
      enabled: () =>
        Boolean(current) && ctrl.isDraft && ctrl.dirty && !ctrl.saveBusy,
      run: () => {
        void ctrl.save();
      },
    },
    {
      id: "publish",
      label: "Publish",
      testId: "update-verb-publish",
      enabled: () => Boolean(current) && ctrl.isDraft && !ctrl.publishBusy,
      run: () => {
        void ctrl.publish();
      },
    },
    {
      id: "copy",
      label: ctrl.copyState === "copied" ? "Copied" : "Copy",
      enabled: () => Boolean(current) && !ctrl.copyBusy,
      run: () => {
        void ctrl.copyMarkdown();
      },
    },
    {
      id: "regenerate",
      label: "Regenerate",
      enabled: () => Boolean(current) && !ctrl.regenerateBusy,
      run: () => {
        void ctrl.regenerate("deterministic");
      },
    },
    {
      id: "send",
      label: "Send",
      enabled: () => Boolean(current) && ctrl.isPublished,
      run: () => setSeat("send"),
    },
    {
      id: "delivered",
      label: "Mark delivered",
      enabled: () => Boolean(current) && ctrl.isPublished,
      run: () => setSeat("delivery"),
    },
    {
      id: "accept",
      label: "Accept claim",
      enabled: () => ctrl.isDraft && Boolean(claim) && !ctrl.reviewBusy,
      run: () => {
        if (claim) void ctrl.reviewClaim(claim.spanId, "accepted");
      },
    },
    {
      id: "reject",
      label: "Reject claim",
      enabled: () => ctrl.isDraft && Boolean(claim) && !ctrl.reviewBusy,
      run: () => {
        if (claim) void ctrl.reviewClaim(claim.spanId, "rejected");
      },
    },
    {
      id: "stop",
      label: "Stop engine",
      enabled: () => ctrl.enginePass.phase === "running",
      run: () => {
        void ctrl.stopEnginePass();
      },
    },
    {
      id: "undo",
      label: "Undo engine draft",
      enabled: () => ctrl.enginePass.phase === "written",
      run: () => {
        void ctrl.undoEngineDraft();
      },
    },
    {
      id: "better",
      label: "Use better draft",
      enabled: () => ctrl.enginePass.phase === "ready",
      run: () => {
        void ctrl.takeBetterDraft();
      },
    },
    {
      id: "retry-engine",
      label: "Retry engine",
      enabled: () => ctrl.enginePass.phase === "failure",
      run: () => {
        void ctrl.retryEnginePass();
      },
    },
    {
      enabled: () => true,
      id: "engine",
      label: "Set up model",
      run: () => openSurfaceOr("configure-runs-on", "/settings", "models"),
    },
  ];
  let inspector: ReactNode;
  if (current && seat === "delivery")
    inspector = (
      <PreferencePane label="Delivery">
      <PaneInspector label="Delivery">
        <InspectorForm
          rows={[
            {
              label: "To",
              control: ctrl.deliverLocked ? (
                <span data-feedback-redact="true">
                  {ctrl.deliverTo || "No recipient"}
                </span>
              ) : (
                <StringGadget
                  label="Delivered to"
                  placeholder="No recipient"
                  value={ctrl.deliverTo}
                  onChange={ctrl.setDeliverTo}
                />
              ),
            },
            ...current.deliveries.map(delivery => ({
              key: delivery.id,
              label: "Delivered to",
              control: <span data-feedback-redact="true">
                {delivery.deliveredTo || "No recipient"} · {delivery.outcome === "unknown" && ctrl.deliverOutcome.kind !== "uncertain" ? "Result unknown · " : ""}
                {wireDayClock(delivery.deliveredAt)} · {delivery.channel === "manual" ? "Manual" : delivery.channel}
                {delivery.proof ? ` · ${JSON.stringify(delivery.proof)}` : ""}
              </span>,
            })),
          ]}
          completion={{
            state: ctrl.deliverOutcome.kind === "refused"
              ? `Delivery refused · ${refusedWord(ctrl.deliverOutcome.code)}`
              : undefined,
            cancel: () => setSeat("updates"),
            primary: {
              label:
                ctrl.deliverOutcome.kind === "uncertain"
                  ? "Try again"
                  : "Mark delivered",
              busy: ctrl.deliverBusy,
              run: () => {
                void ctrl.markDelivered();
              },
            },
          }}
        />
      </PaneInspector>
      <StatusBar data-testid="delivery-status" parts={[{text:ctrl.deliverOutcome.kind === "uncertain" ? "Result unknown" : ctrl.deliverOutcome.kind === "refused" ? "Failed" : current.deliveries.length ? "Marked delivered" : "New",lamp:ctrl.deliverOutcome.kind === "uncertain" ? "ask" : ctrl.deliverOutcome.kind === "refused" ? "fail" : undefined}]} />
      </PreferencePane>
    );
  else if (current && seat === "send")
    inspector = (
      <PaneViewContext.Provider value={null}>
        <SendWells
          doc={updateDoc(current)}
          onSettled={afterSend}
          onBack={() => setSeat("updates")}
        />
      </PaneViewContext.Provider>
    );
  else if (current && (seat === "updates" || seat === "edit"))
    inspector =
      ctrl.isDraft && seat === "edit" ? (
        <PaneInspector label="Update">
          <InspectorForm
            rows={[
              {
                label: "Text",
                control: (
                  <div className="surface-inspector-control" data-feedback-redact="true"><PadGadget
                    label="Update body"
                    value={ctrl.editBody}
                    onChange={ctrl.handleEditBody}
                    rows={6}
                  /></div>
                ),
              },
              {
                label: "From",
                control: generatorLabel(
                  current.generator,
                  current.generatorModel,
                ).replace(/^From /, ""),
              },
            ]}
            completion={{
              cancel: () => {
                setSeat("updates");
              },
              state: ctrl.dirty ? "Not saved" : undefined,
              primary: {
                label: "Save",
                disabled: !ctrl.dirty,
                busy: ctrl.saveBusy,
                run: () => {
                  void ctrl.save();
                },
              },
            }}
          />
        </PaneInspector>
      ) : (
          <ObjectReader
            key={current.id}
            label="Update"
            facts={[
              { label: "State", value: ctrl.dirty ? "Not saved" : lifecycleLabel(current.lifecycle) },
              {
                label: "From",
                value: generatorLabel(
                  current.generator,
                  current.generatorModel,
                ).replace(/^From /, ""),
              },
              {
                label: "To",
                value:
                  current.audience ||
                  current.deliveries
                    .map((row) => row.deliveredTo)
                    .filter(Boolean)
                    .join(" · "),
              },
            ]}
          >
            <ReadingDocument>{roomReadingText(ctrl.isDraft && ctrl.dirty ? ctrl.editBody : current.bodyMd)}</ReadingDocument>
          </ObjectReader>
      );
  return (
    <PaneViews label="Update view" value={seat === "edit" ? "updates" : seat}
      tabs={[{id:"updates",label:"Text"},{id:"claims",label:"Claims"},{id:"sources",label:"Sources"},{id:"send",label:"Send"},{id:"delivery",label:"Delivery"},
        ...projectViews.map(view => ({id:`project:${view.id}`,label:view.label}))]}
      onChange={id => id.startsWith("project:") ? onProjectView?.(id.slice(8)) : setSeat(id)}>
    <RoomList
      label="Updates"
      rows={rows}
      columns={
        seat === "claims" || seat === "sources"
          ? undefined
          : [
              { key: "name", word: "Update", priority: 10, minWidth: 220 },
            ]
      }
      selectedId={
        seat === "claims" || seat === "sources" ? picked : current?.id
      }
      onSelect={(id) => {
        if (seat === "claims" || seat === "sources") setPicked(id);
        else {
          const row = ctrl.updates.find((row) => row.id === id);
          if (row) {
            ctrl.openUpdate(row);
            setSeat("updates");
          }
        }
      }}
      verbs={verbs}
      field={field}
      loading={ctrl.loading || ctrl.draftBusy}
      error={
        linkFailure
          ? "Could not read the latest update · Nothing changed · Try again"
          : ctrl.error
      }
      retry={
        linkFailure?.retry ??
        ctrl.retryFailed ??
        (() => {
          void ctrl.enterUpdates();
        })
      }
      empty="No updates"
    >
      {inspector ??
        (ctrl.draftRun.phase === "failure" ? (
          <RunLine
            phase="failure"
            reason={ctrl.draftRun.reason}
            onRetry={() => {
              void ctrl.draft("deterministic");
            }}
          />
        ) : undefined)}
    </RoomList>
    </PaneViews>
  );
}
