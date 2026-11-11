import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { openRef } from "../openObject";
import {
  InspectorFacts,
  InspectorBody,
  InspectorFigures,
  Lamp,
  ListPane,
  ListView,
  PaneActions,
  PaneInspector,
  streamTime,
} from "../surface";
import { programVerb } from "./api";
import { stepResult, programFailure } from "./liveModel";
import type { Program } from "./types";

export function ProgramOutcome({
  program,
  onApplied,
  onError,
}: {
  program: Program;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const [picked, setPicked] = useState<string | null>(null),
    [busy, setBusy] = useState(false);
  const done = program.state === "done",
    parked = ["parked", "failed"].includes(program.state);
  const displaySteps = program.steps
    .filter((step) => !step.race_of)
    .map((step) => ({ ...stepResult(step), id: step.id, title: step.title }));
  const row = displaySteps.find((step) => step.id === picked);
  const park = program.checkpoints.find((cp) => /park/i.test(cp.line));
  const when = (stamp?: string | null) =>
    stamp ? streamTime(new Date(stamp)) : undefined;
  const resume = async () => {
    if (busy) return;
    setBusy(true);
    try {
      onApplied(await programVerb(program.id, "resume"));
    } catch (e) {
      onError(programFailure(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PaneInspector
        label={
          done
            ? "Program recap"
            : parked
              ? "Parked program"
              : `Starts tonight at ${program.night?.start}`
        }
        trailing={
          <Lamp
            state={done ? "done" : parked ? "off" : "tonight"}
            label={
              done
                ? "Done"
                : parked
                  ? "Parked"
                  : `Starts tonight at ${program.night?.start}`
            }
          />
        }
      >
        <InspectorBody>
          {done ? (
            <InspectorFigures
              label="Program recap"
              figures={[
                { value: program.done, label: "steps done" },
                {
                  value: program.checkpoints.filter((cp) =>
                    cp.line.startsWith("A core question for you:"),
                  ).length,
                  label: "questions to you",
                },
                { value: program.done_in || "—", label: "from start to end" },
              ]}
            />
          ) : null}
          <InspectorFacts
            name={
              done
                ? "Program recap"
                : parked
                  ? "Parked program"
                  : `Starts tonight at ${program.night?.start}`
            }
            rows={
              parked
                ? [
                    {
                      label: "Why",
                      value:
                        (park?.line === "Parked the program; the worktrees stay"
                          ? "No reason was added"
                          : park?.line) ||
                        program.steps.find((s) => s.parked_reason)
                          ?.parked_reason ||
                        program.last_checkpoint?.line,
                    },
                    {
                      label: "When",
                      value: when(park?.at || program.updated_at),
                    },
                    {
                      label: "By",
                      value:
                        (park?.by ||
                          program.steps.find((s) => s.parked_by)?.parked_by) ===
                        "owner"
                          ? "You"
                          : "HoldSpeak",
                    },
                  ]
                : done
                  ? [{ label: "Result", value: program.goal }]
                  : [
                      { label: "Window", value: program.night?.line },
                      {
                        label: "Before in the night list",
                        value:
                          program.night_order?.before?.title ||
                          "First in the list",
                      },
                      {
                        label: "After in the night list",
                        value:
                          program.night_order?.after?.title ||
                          "Last in the list",
                      },
                    ]
            }
          />
          {parked ? (
            <PaneActions>
              <Button
                variant="primary"
                loading={busy}
                onClick={() => void resume()}
              >
                Resume
              </Button>
            </PaneActions>
          ) : null}
        </InspectorBody>
      </PaneInspector>
      <ListPane
        label="Selected program step"
        list={
          <ListView
            label={
              done
                ? "Finished steps"
                : parked
                  ? "Parked steps"
                  : "Tonight's steps"
            }
            headerless
            ordered
            rows={displaySteps.map((s) => ({
              id: s.id,
              kind: "program",
              name: s.title,
              detail: [
                s.state_word,
                s.history?.pr_number
                  ? `PR #${s.history.pr_number}`
                  : s.pr?.url
                    ? `PR ${s.pr.url.split("/").at(-1)}`
                    : null,
                when(s.history?.merged_at || s.ended_at),
              ]
                .filter(Boolean)
                .join(" · "),
            }))}
            columns={[{key:"name",word:"Step"}]}
            selectedId={picked}
            onSelect={setPicked}
            verbs={[
              {
                id: "pr",
                label: "Open PR",
                enabled: () => Boolean(row?.history?.pr_url || row?.pr?.url),
                run: () => {
                  const url = row?.history?.pr_url || row?.pr?.url;
                  if (url) window.open(url, "_blank", "noopener,noreferrer");
                },
              },
              {
                id: "recap",
                label: "Open recap",
                enabled: () => Boolean(program.note_id),
                run: () => {
                  if (program.note_id) openRef(`note:${program.note_id}`);
                },
              },
            ]}
            toolbar={{}}
          />
        }
      >
        {row ? (
          <InspectorFacts
            name="Step result"
            rows={[
              {
                label: "Result",
                value: row.report_text || row.last_checkpoint?.line,
              },
              {
                label: "Finished",
                value: when(row.history?.merged_at || row.ended_at),
              },
            ]}
          />
        ) : null}
      </ListPane>
    </>
  );
}
