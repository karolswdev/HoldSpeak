import { useCallback, useEffect, useState, type ReactNode } from "react";
import {
  CycleGadget,
  PaneActions,
  InspectorForm,
  LivePane,
  ReadingDocument,
  PadGadget,
  PaneInspector,
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
import { RoomList, type RoomEntry } from "../RoomList";
import type { UpdateController } from "./useUpdateController";
import {
  generatorLabel,
  lifecycleLabel,
  claimSends,
  refChipLabel,
  plainLine,
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
export function UpdatePosture({
  ctrl,
  projectActions = [],
  field,
  sendUpdateId,
  linkFailure,
}: {
  ctrl: UpdateController;
  projectActions?: ListVerb[];
  field?: ReactNode;
  sendUpdateId?: string | null;
  linkFailure?: { retry(): void };
}) {
  const [seat, setSeat] = useState("updates"),
    [picked, setPicked] = useState<string | null>(null);
  const current = linkFailure ? null : ctrl.current;
  useEffect(() => {
    if (sendUpdateId) setSeat("send");
  }, [sendUpdateId]);
  const afterSend = useCallback(() => {
    void ctrl.reloadDeliveries();
  }, [ctrl.reloadDeliveries]);
  const engine = useEngine("project.update_draft");
  const claim = current?.claims.find((row) => row.spanId === picked);
  const rows: RoomEntry[] =
    seat === "claims" && current
      ? current.claims.map((row) => ({
          id: row.spanId,
          name: row.text,
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
            { label: "Sources", value: row.refs.join(" · ") },
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
            (ref) => ({
              id: ref,
              name:
                current.claims.find((claim) => claim.refs.includes(ref))
                  ?.text || refChipLabel(ref),
              kind: "artifact",
              kindWord: ref.split(":")[0],
              open: refOpener(ref) ?? undefined,
            }),
          )
        : ctrl.updates.map((row) => ({
              id: row.id,
              name:
                row.bodyMd
                  .split("\n")
                  .filter((line) => !/^\s*#/.test(line))
                  .map((line) => plainLine(line).trim())
                  .find(Boolean) || "Update",
              kind: "artifact",
              when: wireDayClock(row.publishedAt || row.updatedAt),
              cells: {
                to: row.deliveries
                  .map((delivery) => delivery.deliveredTo)
                  .filter(Boolean)
                  .join(" · "),
              },
              facts: [
                { label: "State", value: lifecycleLabel(row.lifecycle) },
                {
                  label: "From",
                  value: generatorLabel(row.generator, row.generatorModel),
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
      id: "save",
      label: "Save",
      testId: "update-verb-save",
      enabled: () => Boolean(current) && ctrl.isDraft && ctrl.dirty && !ctrl.saveBusy,
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
      id: "engine",
      label: "Set up model",
      run: () => openSurfaceOr("configure-runs-on", "/settings", "models"),
    },
  ];
  let inspector: ReactNode;
  if (current && seat === "delivery")
    inspector = (
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
                  value={ctrl.deliverTo}
                  onChange={ctrl.setDeliverTo}
                />
              ),
            },
            ...current.deliveries.map(delivery => ({
              key: delivery.id,
              label: delivery.deliveredTo || "Delivery",
              control: <span data-feedback-redact="true">
                {delivery.outcome === "unknown" && ctrl.deliverOutcome.kind !== "uncertain" ? "Result unknown · " : ""}
                {wireDayClock(delivery.deliveredAt)} · {delivery.channel}
                {delivery.proof ? ` · ${JSON.stringify(delivery.proof)}` : ""}
              </span>,
            })),
          ]}
          completion={{
            state:
              ctrl.deliverOutcome.kind === "uncertain"
                ? "Result unknown · Try again"
                : ctrl.deliverOutcome.kind === "refused"
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
  else if (current && seat === "updates")
    inspector = ctrl.isDraft ? (
      <PaneInspector label="Update">
        <InspectorForm
          rows={[
            {
              label: "Text",
              control: (
                <PadGadget
                  label="Update body"
                  value={ctrl.editBody}
                  onChange={ctrl.handleEditBody}
                  rows={6}
                />
              ),
            },
            {
              label: "From",
              control: generatorLabel(
                current.generator,
                current.generatorModel,
              ),
            },
          ]}
          completion={{
            cancel: () => {
              void ctrl.backToList();
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
      <LivePane
        label="Update"
        well={
          <div className="surface-preference-pane" data-feedback-redact="true">
            <ReadingDocument>{current.bodyMd}</ReadingDocument>
          </div>
        }
        facts={[
          { label: "State", value: lifecycleLabel(current.lifecycle) },
          {
            label: "From",
            value: generatorLabel(current.generator, current.generatorModel),
          },
        ]}
      />
    );
  return (
    <RoomList
      label="Updates"
      rows={rows}
      columns={
        seat === "claims" || seat === "sources"
          ? undefined
          : [
              { key: "when", word: "Sent", priority: 8 },
              { key: "name", word: "Update", priority: 10, minWidth: 220 },
              { key: "to", word: "To", priority: 4 },
            ]
      }
      selectedId={
        seat === "claims" || seat === "sources"
          ? picked
          : current?.id
      }
      onSelect={(id) => {
        if (seat === "claims" || seat === "sources")
          setPicked(id);
        else {
          const row = ctrl.updates.find((row) => row.id === id);
          if (row) ctrl.openUpdate(row);
        }
      }}
      verbs={verbs}
      field={
        <PaneActions>
          {field}
          <CycleGadget
            label="Update records"
            value={seat}
            onChange={setSeat}
            options={[
              { value: "updates", label: "Text" },
              { value: "claims", label: "Claims" },
              { value: "sources", label: "Sources" },
              { value: "send", label: "Send" },
              { value: "delivery", label: "Delivery" },
            ]}
          />
        </PaneActions>
      }
      loading={ctrl.loading || ctrl.draftBusy}
      error={linkFailure ? "Could not read the latest update · Nothing changed · Try again" : ctrl.error}
      retry={
        linkFailure?.retry ?? ctrl.retryFailed ??
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
  );
}
