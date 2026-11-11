import { useState } from "react";
import {
  InspectorForm,
  InspectorQuestion,
  LivePane,
  Material,
  ReadingDocument,
  PaneInspector,
  PadGadget,
  CycleGadget,
  SurfaceState,
  type ListVerb,
} from "../../../desk/surface";
import { openSurfaceOr } from "../../../desk/shell";
import { refOpener } from "../../../desk/openObject";
import type { PrepareController } from "./usePrepareController";
import { RoomList, type RoomEntry } from "../RoomList";
import { refusalReceipt } from "./model";

export const RESULT_OPTIONS = [
  { value: "answer", label: "Answer" },
  { value: "brief", label: "Preparation brief" },
];
export function PreparePosture({
  ctrl,
  projectName: _projectName,
  onOpenRef,
  onResultChange,
  onClose,
}: {
  ctrl: PrepareController;
  onClose?(): void;
  projectName: string;
  onOpenRef(ref: string): void;
  onResultChange(purpose: string): void;
}) {
  const [seat, setSeat] = useState("sources"),
    [armed, setArmed] = useState<string | null>(null);
  const manifest = ctrl.brief?.manifest ?? ctrl.manifest;
  const brief = ctrl.brief;
  const [picked, setPicked] = useState<string | null>(null);
  const source = [
    ...(manifest?.sources ?? []),
    ...(manifest?.omitted ?? []),
  ].find((row) => row.sourceId === picked);
  const claims = brief?.claims ?? [];
  const claim = claims.find((row) => row.spanId === picked);
  const rows: RoomEntry[] =
    seat === "kept"
      ? ctrl.kept.map((row) => ({
          id: row.id,
          kind: "artifact",
          kindWord: "Brief",
          name: row.purpose,
          when: row.keptAt || row.createdAt,
          open: () => {
            void ctrl.openBrief(row);
            setSeat("brief");
          },
        }))
      : seat === "claims"
        ? claims.map((row) => ({
            id: row.spanId,
            kind: row.kind,
            name: row.text,
            kindWord: row.kind.replaceAll("_", " "),
            cells: {
              state: [row.support, row.acceptance]
                .join(" · ")
                .replaceAll("_", " "),
            },
            facts: [
              { label: "Source", value: row.refs.join(" · ") },
              {
                label: "State",
                value:
                  row.section === "superseded"
                    ? "Superseded"
                    : row.support.replaceAll("_", " "),
              },
              { label: "What it says", value: row.text },
              ...row.unknowns.map((unknown, index) => ({
                key: String(index),
                label: "Not known",
                value: `${unknown.type.replaceAll("_", " ")}: ${unknown.value}`,
              })),
            ],
            open: row.refs[0]
              ? (refOpener(row.refs[0]) ?? undefined)
              : undefined,
          }))
        : seat === "carried"
          ? [
              ...(manifest?.decisions ?? []).map((row) => ({
                id: row.ref,
                name: row.text,
                kind: row.kind,
                kindWord: row.kind === "action" ? "Commitment" : "Decision",
                cells: { state: row.lifecycle },
                facts: [
                  { label: "From", value: row.meetingTitle },
                  { label: "Successor", value: row.successorRef },
                ],
                open: () => onOpenRef(row.successorRef || row.ref),
              })),
              ...(manifest?.commitments ?? []).map((row) => ({
                id: row.ref,
                name: row.text,
                kind: row.kind,
                kindWord: row.kind === "decision" ? "Decision" : "Commitment",
                facts: [
                  { label: "Owner", value: row.owner },
                  { label: "Due", value: row.dueAt },
                ],
                open: () => onOpenRef(row.ref),
              })),
              ...(manifest?.notIncluded ?? []).map((row, i) => ({
                id: `omitted:${i}`,
                name: row.title,
                kind: "artifact",
                kindWord: "Not included",
                facts: [{ label: "Reason", value: row.why }],
                open: refOpener(row.ref) ?? undefined,
              })),
            ]
          : [...(manifest?.sources ?? []), ...(manifest?.omitted ?? [])].map(
              (row) => ({
                id: row.sourceId,
                name: row.label,
                kind: row.kind,
                kindWord: row.kind,
                when: row.observedAt || "Never read",
                cells: {
                  state:
                    row.state === "available"
                      ? ""
                      : row.repair?.verb || row.reason || "Not read",
                },
                facts: [
                  { label: "State", value: row.reason },
                  { label: "Last read", value: row.observedAt },
                  { label: "What it says", value: row.tokens.join(" · ") },
                ],
                open:
                  row.kind === "github"
                    ? () =>
                        window.open(
                          `https://github.com/${row.label}`,
                          "_blank",
                          "noopener",
                        )
                    : undefined,
              }),
            );
  const verbs: ListVerb[] = [
    {
      id: "prepare",
      label: "Prepare",
      enabled: () =>
        Boolean(ctrl.purpose.trim()) &&
        ctrl.posture !== "running" &&
        (!ctrl.route || ctrl.route.state === "ready"),
      run: () => {
        void ctrl.prepare();
        setSeat("brief");
      },
    },
    {
      id: "stop",
      label: "Stop",
      enabled: () => ctrl.posture === "running",
      run: () => {
        void ctrl.stop();
      },
    },
    {
      id: "keep",
      label: "Keep",
      enabled: () => brief?.lifecycle === "draft" && !ctrl.keepBusy,
      run: () => {
        void ctrl.keep();
      },
    },
    {
      id: "discard",
      label: "Discard",
      enabled: () => brief?.lifecycle === "draft",
      run: () => setArmed(`${brief!.id}:${brief!.manifestSha256}`),
    },
    {
      id: "copy",
      label: ctrl.copyState === "copied" ? "Copied" : "Copy",
      enabled: () => Boolean(brief),
      run: () => {
        void ctrl.copy();
      },
    },
    {
      id: "repair",
      label: source?.repair?.verb || "Read sources again",
      run: () => {
        if (source?.repair)
          void ctrl.repairSource(source.repair.verb, source.watchIds);
        else void ctrl.reloadCoverage();
      },
    },
    {
      id: "engine",
      label: "Set up model",
      run: () => openSurfaceOr("configure-runs-on", "/settings", "models"),
    },
    {
      id: "support",
      label: "Find support",
      enabled: () => Boolean(claim && !claim.refs.length),
      run: () => {
        if (claim) openSurfaceOr("open-project-memory", "/", `q:${claim.text}`);
      },
    },
    {
      id: "answer",
      label: "Answer instead",
      run: () => onResultChange(ctrl.purpose),
    },
  ];
  return (
    <RoomList
      label="Prepare"
      rows={rows}
      selectedId={picked}
      onSelect={setPicked}
      verbs={verbs}
      field={
        <CycleGadget
          label="Preparation records"
          value={seat}
          options={[
            { value: "sources", label: "Sources" },
            { value: "purpose", label: "Purpose" },
            { value: "brief", label: "Brief" },
            { value: "claims", label: "Claims" },
            { value: "carried", label: "Carried forward" },
            { value: "kept", label: "Kept briefs" },
          ]}
          onChange={(next) => {
            setSeat(next);
            if (next === "kept") void ctrl.loadKept();
          }}
        />
      }
      error={ctrl.error}
      retry={() => {
        void ctrl.reloadCoverage();
      }}
      empty="No preparation records"
    >
      {armed && brief && armed === `${brief.id}:${brief.manifestSha256}` ? (
        <InspectorQuestion
          actionId="remove"
          targetId={armed}
          question="Discard this brief?"
          keeps={["Project sources and decisions"]}
          cancel={() => setArmed(null)}
          onDisarm={() => setArmed(null)}
          verb={{
            label: "Discard",
            busy: ctrl.discardBusy,
            run: () => {
              void ctrl.discard().then(() => setArmed(null));
            },
          }}
        />
      ) : seat === "purpose" || !brief ? (
        <PaneInspector label="Prepare a brief">
          <InspectorForm
            rows={[
              {
                label: "Purpose",
                control: (
                  <PadGadget
                    label="Purpose"
                    value={ctrl.purpose}
                    onChange={ctrl.setPurpose}
                  />
                ),
              },
              { label: "Engine", control: ctrl.route?.model },
              {
                label: "State",
                control:
                  ctrl.posture === "running"
                    ? "Preparing"
                    : ctrl.refusal
                      ? refusalReceipt(ctrl.refusal.route).line
                      : ctrl.stopped
                        ? "Stopped"
                        : "",
              },
            ].filter((row) => row.control !== "" && row.control != null)}
            notice={
              ctrl.refusal ? (
                <SurfaceState
                  error={ctrl.refusal.error}
                  onRetry={() => {
                    void ctrl.reloadRoute();
                  }}
                />
              ) : undefined
            }
            completion={{
              cancel: () => {
                ctrl.exit();
                onClose?.();
              },
              primary: {
                label: "Prepare",
                run: () => {
                  void ctrl.prepare();
                  setSeat("brief");
                },
                disabled: !ctrl.purpose.trim() || ctrl.posture === "running",
                busy: ctrl.posture === "running",
              },
            }}
          />
        </PaneInspector>
      ) : seat === "brief" ? (
        <LivePane
          label="Brief"
          well={
            <div
              className="surface-preference-pane"
              data-feedback-redact="true"
            >
              <ReadingDocument>{brief.bodyMd}</ReadingDocument>
            </div>
          }
          facts={[
            { label: "Purpose", value: brief.purpose },
            { label: "State", value: brief.lifecycle },
            {
              label: "Coverage",
              value: `${brief.manifest.coverage.available} of ${brief.manifest.coverage.expected}`,
            },
            {
              label: "Integrity",
              value:
                brief.integrity === "mismatch"
                  ? "Does not match the saved sources"
                  : "",
            },
          ]}
        />
      ) : undefined}
    </RoomList>
  );
}
