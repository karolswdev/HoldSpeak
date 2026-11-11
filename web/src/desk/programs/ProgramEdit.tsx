import { useEffect, useState } from "react";
import {
  CheckGadget,
  CycleGadget,
  InspectorForm,
  PadGadget,
  PaneInspector,
  SegmentedTabs,
  StringGadget,
  type InspectorRow,
} from "../surface";
import { Button } from "../../components/signal/Signal";
import {
  readProjectChoices,
  type ProjectChoice,
  updateProgram,
  type UpdateBody,
} from "./api";
import { programFailure } from "./liveModel";
import { RunsOnPicker, type RunsOnChoice } from "./RunsOn";
import { PersonPicker, type PersonChoice } from "./PersonPicker";
import type { Program } from "./types";

/** Language fields share the hub's update operation and one completion row.
 * Only fields touched in this form are sent; a fresh unrelated field is kept. */
export function ProgramEdit({
  program,
  onCancel,
  onApplied,
}: {
  program: Program;
  onCancel(): void;
  onApplied(next: Program | null): void;
}) {
  const [part, setPart] = useState("program"),
    [patch, setPatch] = useState<UpdateBody>({}),
    [busy, setBusy] = useState(false),
    [failed, setFailed] = useState("");
  const [projects, setProjects] = useState<ProjectChoice[]>([]),
    [projectFailed, setProjectFailed] = useState(false);
  const loadProjects = async () => {
    try {
      setProjects(await readProjectChoices());
      setProjectFailed(false);
    } catch {
      setProjectFailed(true);
    }
  };
  useEffect(() => {
    void loadProjects();
  }, []);
  const put = <K extends keyof UpdateBody>(key: K, value: UpdateBody[K]) =>
    setPatch((now) => ({ ...now, [key]: value }));
  const value = <K extends keyof UpdateBody>(key: K, initial: UpdateBody[K]) =>
    key in patch ? patch[key] : initial;
  const text = (
    key: keyof UpdateBody,
    label: string,
    initial: string,
    pad = false,
  ): InspectorRow => ({
    label,
    control: pad ? (
      <PadGadget
        label={label}
        value={String(value(key, initial) ?? "")}
        onChange={(v) => put(key, v)}
      />
    ) : (
      <StringGadget
        label={label}
        value={String(value(key, initial) ?? "")}
        onChange={(v) => put(key, v)}
      />
    ),
  });
  const tick = (
    key: keyof UpdateBody,
    label: string,
    initial: boolean,
  ): InspectorRow => ({
    label,
    control: (
      <CheckGadget
        label={label}
        checked={Boolean(value(key, initial))}
        onChange={(v) => put(key, v)}
      />
    ),
  });
  const agent: RunsOnChoice = {
    profile: value(
      "default_profile",
      program.default.profile ?? "claude-default",
    )!,
    engine: value("default_engine", program.default.engine?.id ?? null) ?? null,
  };
  const reviewer: RunsOnChoice = {
    profile: value("reviewer_profile", program.reviewer.profile ?? "none")!,
    engine:
      value("reviewer_engine", program.reviewer.engine?.id ?? null) ?? null,
  };
  const [person, setPerson] = useState<PersonChoice | null>(
    program.place.person ?? null,
  );
  const rows: InspectorRow[] =
    part === "program"
      ? [
          text("title", "Name", program.title),
          text("goal", "Goal", program.goal, true),
          {
            label: "Project",
            control: (
              <CycleGadget
                label="Program project"
                value={value("project_id", program.project_id) || ""}
                options={[
                  { value: "", label: "No project", disabled: true },
                  ...projects.map((row) => ({
                    value: row.id,
                    label: row.name,
                  })),
                ]}
                onChange={(v) => put("project_id", v)}
              />
            ),
          },
          {
            label: "Control",
            control: (
              <CycleGadget
                label="Program control"
                value={value("control", program.control)!}
                options={[
                  { value: "secure", label: "Asks at every step" },
                  { value: "normal", label: "Asks before it merges or sends" },
                  { value: "yolo", label: "Runs by itself" },
                ]}
                onChange={(v) => put("control", v as Program["control"])}
              />
            ),
          },
          {
            label: "For",
            control: (
              <PersonPicker
                value={person}
                onPick={(v) => {
                  setPerson(v);
                  put("for_person_id", v?.id ?? null);
                }}
              />
            ),
          },
        ]
      : part === "agents"
        ? [
            {
              label: "Agent",
              control: (
                <RunsOnPicker
                  label="Default agent"
                  value={agent}
                  onPick={(v) =>
                    setPatch((now) => ({
                      ...now,
                      default_profile: v.profile,
                      default_engine: v.engine,
                    }))
                  }
                  then={(
                    value("runs_on", program.default.runs_on ?? []) ?? []
                  ).slice(1)}
                  onThen={(v) => put("runs_on", [agent, ...v])}
                />
              ),
            },
            {
              label: "Reviewer",
              control: (
                <RunsOnPicker
                  label="Program reviewer"
                  value={reviewer}
                  onPick={(v) =>
                    setPatch((now) => ({
                      ...now,
                      reviewer_profile: v.profile,
                      reviewer_engine: v.engine,
                    }))
                  }
                />
              ),
            },
            {
              label: "Allowed agents",
              control: (
                <StringGadget
                  label="Allowed agent profiles"
                  value={(
                    value("allowed_profiles", program.allowed_profiles ?? []) ??
                    []
                  ).join(", ")}
                  onChange={(v) =>
                    put("allowed_profiles", v.split(/[,\s]+/).filter(Boolean))
                  }
                />
              ),
            },
            tick("prefer_idle", "When idle", program.prefer_idle),
            tick(
              "may_handoff",
              "May hand off on its own",
              Boolean(program.may_handoff),
            ),
          ]
        : part === "checks"
          ? [
              text(
                "check_command",
                "Check command",
                program.check_command ?? "",
              ),
              {
                label: "Review depth",
                control: (
                  <CycleGadget
                    label="Review depth"
                    value={
                      value("review_depth", program.review_depth ?? "") ?? ""
                    }
                    options={[
                      { value: "", label: "Program rule" },
                      { value: "glance", label: "Glance" },
                      { value: "delta", label: "Delta" },
                      { value: "standard", label: "Standard" },
                    ]}
                    onChange={(v) => put("review_depth", v || null)}
                  />
                ),
              },
              text(
                "planner_engine",
                "Planning engine",
                program.planner?.engine ?? "",
              ),
              {
                label: "Token budget",
                control: (
                  <StringGadget
                    label="Token budget"
                    value={String(
                      value("budget_tokens", program.budget_tokens ?? null) ??
                        "",
                    )}
                    onChange={(v) => put("budget_tokens", v ? Number(v) : null)}
                  />
                ),
              },
              tick(
                "rounds_before_start",
                "Rounds before start",
                Boolean(program.rounds_before_start),
              ),
            ]
          : part === "limits"
            ? [
                {
                  label: "Spending note, USD",
                  control: (
                    <StringGadget
                      label="Spending note in USD"
                      value={String(
                        value(
                          "spend_limit_usd",
                          program.spend_limit_usd ?? null,
                        ) ?? "",
                      )}
                      onChange={(v) =>
                        put("spend_limit_usd", v ? Number(v) : null)
                      }
                    />
                  ),
                },
                {
                  label: "Usage warning share",
                  control: (
                    <StringGadget
                      label="Usage warning share"
                      value={String(
                        value(
                          "usage_warning_share",
                          program.usage_warning_share ?? null,
                        ) ?? "",
                      )}
                      onChange={(v) =>
                        put("usage_warning_share", v ? Number(v) : null)
                      }
                    />
                  ),
                },
                tick("may_call", "May call you", Boolean(program.may_call)),
                text("within", "Within", (program.within ?? []).join(", ")),
              ]
            : [
                text("night", "Night window", program.night?.line ?? ""),
                text(
                  "delivery",
                  "Delivery",
                  program.delivery ? `dw:${program.delivery.ref}` : "",
                ),
              ];
  const save = async () => {
    if (busy) return;
    setBusy(true);
    try {
      onApplied(await updateProgram(program.id, patch));
    } catch (e) {
      setFailed(programFailure(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <PaneInspector label="Edit program">
      <SegmentedTabs
        label="Program fields"
        value={part}
        onChange={setPart}
        tabs={[
          { id: "program", label: "Program" },
          { id: "agents", label: "Agents" },
          { id: "checks", label: "Checks" },
          { id: "limits", label: "Limits" },
          { id: "night", label: "Night" },
        ]}
      >
        <InspectorForm
          rows={rows}
          notice={
            failed ||
            (projectFailed ? (
              <Button variant="ghost" onClick={() => void loadProjects()}>
                Retry projects
              </Button>
            ) : undefined)
          }
          completion={{
            cancel: onCancel,
            primary: {
              label: "Save program",
              busy,
              disabled: !Object.keys(patch).length,
              run: () => void save(),
            },
          }}
        />
      </SegmentedTabs>
    </PaneInspector>
  );
}
