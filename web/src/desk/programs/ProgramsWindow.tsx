import { useCallback, useEffect, useRef, useState } from "react";
import type { CoreProps } from "../../pages/cores/core-types";
import { programFailure as readableError } from "./liveModel";
import { keepPlace } from "../deskMemory";
import { openAgentLane } from "../shell";
import { useDesk } from "../store";
import { ListApp, useListApp, useWindowTitle, type ListVerb } from "../surface";
import {
  applyProgram,
  programVerb,
  readPrograms,
  useProgram,
  useProgramFrames,
} from "./api";
import { ProgramDetail } from "./ProgramWindow";
import { ProgramEdit } from "./ProgramEdit";
import { ProgramForm } from "./ProgramForm";
import {
  answerBinding,
  currentStep,
  latestRuns,
  programRow,
} from "./liveModel";
import { NEW_PROGRAM_PLACE, type NewProgramPrefill } from "./newProgram";
import type { Program } from "./types";
import { addToTonight } from "./api";

export { openProgram } from "./open";
export const PROGRAM_PICKED = "programs/picked";
const read = async () => {
  const list = await readPrograms();
  return { ...list, rows: latestRuns(list.programs) };
};

/** One master-detail window, including links to a single program. */
export function ProgramsCore({
  scope,
  initialProgramId,
}: CoreProps & { initialProgramId?: string }) {
  const keptPlace = useDesk((s) => s.places[PROGRAM_PICKED]);
  const kept =
    initialProgramId ||
    (scope?.startsWith("program:") ? scope.slice(8) : null) ||
    keptPlace ||
    null;
  const app = useListApp({
    read,
    keyOf: (row) => row.id,
    initialPicked: kept,
    search: (row, query) =>
      `${row.title} ${row.line ?? ""} ${row.search_words ?? ""}`
        .toLocaleLowerCase()
        .includes(query),
  });
  const chosen = useProgram(app.picked ?? "");
  const [form, setForm] = useState<"new" | "amend" | "edit" | null>(null);
  const [detailTab, setDetailTab] = useState("now");
  const [formBusy, setFormBusy] = useState(false);
  const seenHeld = useRef("");
  useEffect(() => {
    const held = chosen.program?.held_shape;
    const key = held ? `${chosen.program?.id}:${held.at}` : "";
    if (key && key !== seenHeld.current && !form) {
      seenHeld.current = key;
      setForm("amend");
    }
  }, [chosen.program?.held_shape, form]);
  const [prefill, setPrefill] = useState<NewProgramPrefill>();
  const [busy, setBusy] = useState(false),
    [failed, setFailed] = useState("");
  useWindowTitle("Programs", []);
  useEffect(() => {
    if (!app.picked && !app.loading && app.visible.length && !app.query)
      app.setPicked(app.visible[0].id);
  }, [app.loading, app.visible, app.picked, app.query]);
  useEffect(() => {
    if (kept && kept !== app.picked) {
      app.setQuery("");
      app.setPicked(kept);
      setForm(null);
      setDetailTab("now");
    }
  }, [kept]);
  useProgramFrames(() => {
    void app.reload();
  });
  const asked = useDesk((s) => s.places[NEW_PROGRAM_PLACE]);
  useEffect(() => {
    if (!asked) return;
    keepPlace(NEW_PROGRAM_PLACE, "");
    try {
      setPrefill(JSON.parse(asked));
      setForm("new");
    } catch {
      setFailed("The new program details could not be read.");
    }
  }, [asked]);
  const applied = useCallback(
    (next: Program | null) => {
      if (next) {
        applyProgram(next);
        app.apply(next);
      } else void chosen.reload();
      void app.reload();
    },
    [app.apply, app.reload, chosen.reload],
  );
  const run = async (work: () => Promise<Program | null>) => {
    if (busy) return;
    setBusy(true);
    setFailed("");
    try {
      applied(await work());
    } catch (cause) {
      setFailed(readableError(cause));
    } finally {
      setBusy(false);
    }
  };
  const program = chosen.program;
  const step = program ? currentStep(program) : null;
  const mutable = () =>
    Boolean(program && !busy && !formBusy && program.state !== "done");
  const verbs: ListVerb[] = [
    {
      id: "new",
      label: "New program",
      testId: "programs-new",
      enabled: () => !formBusy,
      run: () => {
        setPrefill(undefined);
        setForm("new");
      },
    },
    {
      id: "open",
      label: "Open",
      title: "Open the agent session",
      enabled: () => Boolean(step?.launch_id),
      run: () => {
        if (step?.launch_id) openAgentLane(step.launch_id);
      },
    },
    {
      id: "park",
      label:
        program?.state === "parked" || program?.state === "failed"
          ? "Resume"
          : "Park",
      enabled: mutable,
      run: () => {
        if (program)
          void run(() =>
            programVerb(
              program.id,
              program.state === "parked" || program.state === "failed"
                ? "resume"
                : "park",
              answerBinding(program, step?.id),
            ),
          );
      },
    },
    {
      id: "tonight",
      label: "Add to tonight",
      enabled: () => Boolean(step && !busy),
      run: () => {
        if (step)
          void run(async () => {
            await addToTonight({ kind: "program_step", item_id: step.id });
            return program;
          });
      },
    },
    {
      id: "amend",
      label: "Amend",
      testId: "program-amend",
      enabled: mutable,
      run: () => {
        setDetailTab("now");
        setForm("amend");
      },
    },
    {
      id: "edit",
      label: "Edit program",
      enabled: () => Boolean(program && !busy),
      run: () => setForm("edit"),
    },
  ];
  const runningCount = app.rows.filter(
    (row) => programRow(row, app.page?.night?.program_id).group === 1,
  ).length;
  const waitingCount = app.rows.filter(
    (row) => programRow(row, app.page?.night?.program_id).group === 0,
  ).length;
  return (
    <ListApp
      app={app}
      onPaneBack={() => setForm(null)}
      paneOpen={Boolean(form)}
      layout="deck"
      label="Programs"
      ids={{
        windowTestId: "programs-window",
        listTestId: "programs-list",
        paneTestId: "programs-pane",
        toolbarTestId: "programs-toolbar",
        statusTestId: "programs-status",
      }}
      words={{
        find: "Find a program",
        empty: "No programs yet",
        noMatch: "No programs match",
        select: "Select a program",
      }}
      list={{
        headerless: true,
        columns: [{ key: "name", word: "Program" }],
        verbs,
        groups: [
          { id: 0, label: "Waits on you" },
          { id: 1, label: "Running" },
          {
            id: 2,
            label: `Tonight, from ${app.page?.night?.start ?? "23:00"}`,
          },
          { id: 3, label: "Earlier" },
        ],
        onOpen: () => setForm(null),
      }}
      row={(row) => programRow(row, app.page?.night?.program_id)}
      onSelect={() => {
        setDetailTab("now");
        setForm(null);
        setFailed("");
      }}
      pane={() =>
        form === "edit" && program ? (
          <ProgramEdit
            program={program}
            onCancel={() => setForm(null)}
            onApplied={(next) => {
              applied(next);
              setForm(null);
            }}
          />
        ) : form && form !== "edit" ? (
          <ProgramForm
            key={`${form}:${form === "amend" ? program?.id : "new"}`}
            onBusyChange={setFormBusy}
            onOpenText={() => {
              setForm(null);
              setDetailTab("text");
            }}
            kind={form}
            program={program}
            prefill={prefill}
            scopeProjectId={
              scope?.startsWith("project:") ? scope.slice(8) : undefined
            }
            onCancel={() => setForm(null)}
            onApplied={(next) => {
              applied(next);
              if (next) {
                app.setPicked(next.id);
                keepPlace(PROGRAM_PICKED, next.id);
              }
              setForm(null);
            }}
          />
        ) : (
          <ProgramDetail
            view={detailTab}
            program={program}
            loading={chosen.loading}
            error={chosen.error}
            reload={chosen.reload}
            onApplied={applied}
            onError={setFailed}
          />
        )
      }
      status={[
        app.rows.length
          ? {
              key: "count",
              text: `${app.rows.length} ${app.rows.length === 1 ? "program" : "programs"}`,
              testId: "programs-status-total",
            }
          : null,
        waitingCount
          ? {
              key: "ask",
              lamp: "ask",
              text: `${waitingCount} waits on you`,
              testId: "programs-status-waiting",
            }
          : null,
        runningCount
          ? {
              key: "work",
              lamp: "info",
              text: `${runningCount} running`,
              testId: "programs-status-running",
            }
          : null,
        failed
          ? {
              key: "failed",
              lamp: "fail",
              text: failed,
              testId: "programs-failure",
            }
          : null,
      ]}
    />
  );
}
export default ProgramsCore;
