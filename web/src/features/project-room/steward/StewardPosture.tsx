import { useState } from "react";
import {
  CheckGadget,
  CycleGadget,
  InspectorForm,
  LivePane,
  PaneInspector,
  PadGadget,
  StringGadget,
  type ListVerb,
} from "../../../desk/surface";
import { openRef } from "../../../desk/openObject";
import { RoomList } from "../RoomList";
import type { StewardController } from "./useStewardController";
import {
  EFFECT_KINDS,
  STEWARD_PRESETS,
  assembleGrantText,
  phaseLabel,
  presetOf,
  receiptRefs,
  runCoverage,
  runRowSubstance,
  runStateLabel,
  circuitStateLabel,
  runCounts,
} from "./model";

export function StewardPosture({
  ctrl,
  onOpenReview,
  onOpenUpdate,
}: {
  ctrl: StewardController;
  onOpenReview(id: string): void;
  onOpenUpdate(id: string): Promise<void>;
}) {
  const [seat, setSeat] = useState("runs"),
    [picked, setPicked] = useState<string | null>(null);
  const step = ctrl.currentSteps.find((row) => row.id === picked);
  const run = ctrl.currentRun;
  const counts = run ? runCounts(ctrl.currentSteps, run) : null;
  const updateId = ctrl.currentSteps
    .map((row) => String(row.observed.update_id || ""))
    .find(Boolean);
  const verbs: ListVerb[] = [
    {
      id: "run",
      label: "Run once",
      enabled: () => ctrl.canRun && !ctrl.runBusy,
      title: ctrl.runDisabledReason || undefined,
      run: () => {
        void ctrl.runOnce();
        setSeat("steps");
      },
    },
    {
      id: "stop",
      label: "Stop",
      enabled: () => ctrl.canStop && !ctrl.stopBusy,
      run: () => {
        void ctrl.stopRun();
      },
    },
    {
      id: "policy",
      label: "Watch settings",
      run: () => {
        void ctrl.enterPolicy();
        setSeat("policy");
      },
    },
    {
      id: "review",
      label: "Open review",
      enabled: () => Boolean(counts?.reviewId),
      run: () => {
        if (counts?.reviewId) onOpenReview(counts.reviewId);
      },
    },
    {
      id: "update",
      label: "Open update",
      enabled: () => Boolean(updateId),
      run: () => {
        if (updateId) void onOpenUpdate(updateId);
      },
    },
  ];
  const rows =
    seat === "steps"
      ? ctrl.currentSteps.map((row) => ({
          id: row.id,
          name: phaseLabel(row.phase),
          kind: "action",
          kindWord: row.effectKind.replaceAll("_", " "),
          cells: { state: row.state },
          facts: [
            { label: "Error", value: row.error?.message },
            { label: "Expected", value: JSON.stringify(row.expected) },
            { label: "Observed", value: JSON.stringify(row.observed) },
            { label: "Receipt", value: JSON.stringify(row.receipt) },
          ],
          open: receiptRefs(row)[0]
            ? () => openRef(receiptRefs(row)[0])
            : undefined,
        }))
      : seat === "watches"
        ? ctrl.watches.map((row) => ({
            id: row.id,
            name: row.name,
            kind: "source",
            kindWord: row.connectorId,
            cells: {
              state:
                row.circuitState === "closed"
                  ? ""
                  : circuitStateLabel(row.circuitState),
            },
            facts: [
              {
                label: "Every",
                value: `${row.evaluationCadenceMinutes} minutes`,
              },
              { label: "Failures", value: row.circuitFailureStreak || "" },
              { label: "Opened", value: row.circuitOpenedAt },
            ],
          }))
        : ctrl.runs.map((row) => ({
            id: row.id,
            name: runRowSubstance(row) || runStateLabel(row.state),
            kind: "action",
            kindWord: "Run",
            when: row.createdAt || "",
            cells: { state: runStateLabel(row.state) },
            facts: [
              { label: "State", value: runStateLabel(row.state) },
              { label: "Phase", value: phaseLabel(row.phase) },
            ],
            open: () => {
              void ctrl.openRun(row);
              setSeat("steps");
            },
          }));
  const draft = ctrl.policyDraft;
  return (
    <RoomList
      label="Steward"
      rows={rows}
      selectedId={picked}
      onSelect={(id) => {
        setPicked(id);
        if (seat === "runs") {
          void ctrl.openRun(ctrl.runs.find((row) => row.id === id)!);
        }
      }}
      verbs={verbs}
      field={
        <CycleGadget
          label="Steward records"
          value={seat}
          onChange={(next) => {
            setSeat(next);
            if (next === "policy") void ctrl.enterPolicy();
          }}
          options={[
            { value: "runs", label: "Runs" },
            { value: "steps", label: "Steps" },
            { value: "policy", label: "Settings" },
            { value: "watches", label: "Watches" },
          ]}
        />
      }
      loading={ctrl.loading}
      error={ctrl.error || ctrl.policyError}
      retry={() => {
        void ctrl.enterSteward();
      }}
      empty="No runs"
    >
      {seat === "policy" && draft ? (
        <PaneInspector label="Watch settings">
          <InspectorForm
            rows={[
              {
                label: "Preset",
                control: (
                  <CycleGadget
                    label="Preset"
                    value={presetOf(draft)}
                    options={[...STEWARD_PRESETS]}
                    onChange={(value) =>
                      ctrl.applyPreset(
                        value as Parameters<typeof ctrl.applyPreset>[0],
                      )
                    }
                  />
                ),
              },
              {
                label: "Enabled",
                control: (
                  <CheckGadget
                    label="Enabled"
                    checked={draft.enabled}
                    onChange={(value) =>
                      ctrl.updatePolicyDraft("enabled", value)
                    }
                  />
                ),
              },
              {
                label: "Unattended",
                control: (
                  <CheckGadget
                    label="Unattended"
                    checked={draft.unattended_enabled}
                    onChange={(value) =>
                      ctrl.updatePolicyDraft("unattended_enabled", value)
                    }
                  />
                ),
              },
              ...EFFECT_KINDS.map((kind) => ({
                label: kind.replaceAll("_", " "),
                control: (
                  <CheckGadget
                    label={kind.replaceAll("_", " ")}
                    checked={draft.eligible_effect_kinds.includes(kind)}
                    onChange={() => ctrl.toggleEffectKind(kind)}
                  />
                ),
              })),
              {
                label: "Every (minutes)",
                control: (
                  <StringGadget
                    label="Every (minutes)"
                    type="number"
                    value={String(draft.evaluation_cadence_minutes ?? 60)}
                    onChange={(value) =>
                      ctrl.updatePolicyDraft(
                        "evaluation_cadence_minutes",
                        Number(value),
                      )
                    }
                  />
                ),
              },
              {
                label: "Actions per run",
                control: (
                  <StringGadget
                    label="Actions per run"
                    type="number"
                    value={String(draft.max_actions_per_run)}
                    onChange={(value) =>
                      ctrl.updatePolicyDraft(
                        "max_actions_per_run",
                        Number(value),
                      )
                    }
                  />
                ),
              },
              {
                label: "Retries",
                control: (
                  <StringGadget
                    label="Retries"
                    type="number"
                    value={String(draft.max_retries)}
                    onChange={(value) =>
                      ctrl.updatePolicyDraft("max_retries", Number(value))
                    }
                  />
                ),
              },
              {
                label: "Cooldown (seconds)",
                control: (
                  <StringGadget
                    label="Cooldown (seconds)"
                    type="number"
                    value={String(draft.cooldown_seconds)}
                    onChange={(value) =>
                      ctrl.updatePolicyDraft("cooldown_seconds", Number(value))
                    }
                  />
                ),
              },
              {
                label: "Nudge text",
                control: (
                  <PadGadget
                    label="Nudge text"
                    value={draft.nudge_template || ""}
                    onChange={(value) =>
                      ctrl.updatePolicyDraft("nudge_template", value)
                    }
                  />
                ),
              },
              {
                label: "Approval",
                control: draft.eligible_effect_kinds.includes("github_comment")
                  ? "Each nudge needs your approval"
                  : "",
              },
              {
                label: "Grant",
                control: ctrl.policy
                  ? assembleGrantText(ctrl.policy, ctrl.watches)
                  : "",
              },
            ]}
            completion={{
              cancel: () => {
                void ctrl.backToList();
                setSeat("runs");
              },
              primary: {
                label: "Save",
                busy: ctrl.policyBusy,
                run: () => {
                  void ctrl.savePolicy();
                },
              },
            }}
          />
        </PaneInspector>
      ) : (seat === "runs" || (seat === "steps" && !step)) && run ? (
        <LivePane
          label="Run"
          facts={[
            { label: "State", value: runStateLabel(run.state) },
            { label: "Outcome", value: runRowSubstance(run) },
            { label: "Sources read", value: counts?.sources },
            { label: "Proposals", value: counts?.proposals },
            { label: "Effects", value: counts?.effects },
            {
              label: "Source states",
              value: runCoverage(run)
                .map((row) => `${row.source}: ${row.state}`)
                .join(" · "),
            },
          ]}
        />
      ) : undefined}
    </RoomList>
  );
}
