// HS-117-09 — extracted from HistoryCore (lines 1100-1205).
// Window Program W1 (2026-10-27): the gear wing is on the window grammar:
// one list view per section, rows in real words (the task, the job's
// name), a state as a dot and a word, a quiet age; no mono caps tokens
// (`QUEUED`), no row that says only its section's name.
import { Button } from "../../../components/signal/Signal";
import { SurfaceState } from "../../../desk/surface/Surface";
import { CycleGadget } from "../../../desk/surface/gadgets";
import { deSnake, presentValue } from "../../../desk/surface/format";
import { ListDay, ListRow, ListView, ageWords, type ListRowState } from "../../../desk/surface/objects/ListView";
import { asRows, rowId } from "../../pageSupport";
import { DOOR_SECTIONS } from "./helpers";
import { apiFetch } from "../../../lib/api";
import { MeetingsConfig } from "./MeetingsConfig";
import { openProjectRoom } from "../../../desk/shell";

type Row = Record<string, unknown>;

const SECTION_WORDS: Record<(typeof DOOR_SECTIONS)[number], string> = {
  actions: "Actions",
  speakers: "Speakers",
  projects: "Projects",
  queues: "Background work",
};

/** A sentence-case word from a wire token (`cli_enrichment` → `Cli enrichment`). */
function sentence(value: unknown): string {
  const words = deSnake(value).toLowerCase();
  return words ? words[0].toUpperCase() + words.slice(1) : "";
}

/** A job's state in his words. */
export function jobState(status: unknown): ListRowState {
  switch (String(status ?? "").toLowerCase()) {
    case "pending":
    case "queued":
      return { word: "Waiting", tone: "idle" };
    case "running":
      return { word: "Running", tone: "info" };
    case "failed":
    case "error":
      return { word: "Failed", tone: "fail" };
    case "complete":
    case "completed":
    case "done":
    case "succeeded":
      return { word: "Done", tone: "ok" };
    default:
      return { word: sentence(status) || "Not known", tone: "idle" };
  }
}

/** An action item's state: open, done, dismissed. */
function actionState(status: unknown): ListRowState {
  const value = String(status ?? "").toLowerCase();
  if (value === "done") return { word: "Done", tone: "ok" };
  if (value === "dismissed") return { word: "Dismissed", tone: "idle" };
  return { word: "Open", tone: "info" };
}

/** A deferred plugin job by what it does. */
const PLUGIN_WORDS: Record<string, string> = {
  cli_enrichment: "Enrich with the CLI",
  candidate_inference: "Find meeting candidates",
  action_items: "Find actions",
  decisions: "Find decisions",
};
function jobName(row: Row): string {
  if (row.plugin_id) return PLUGIN_WORDS[String(row.plugin_id)] ?? sentence(row.plugin_id);
  if (row.title) return String(row.title);
  return "Summary";
}

/** The queue filter's statuses, the intel and plugin words for each. */
const QUEUE_MATCH: Record<string, string[]> = {
  pending: ["pending", "queued"],
  running: ["running"],
  failed: ["failed", "error"],
  complete: ["complete", "completed", "done", "succeeded"],
};

export function DoorSection({
  actions,
  speakers,
  projects,
  intel,
  plugin,
  queueStatus,
  setQueueStatus,
}: {
  actions: { data: Record<string, unknown> };
  speakers: { data: Record<string, unknown> };
  projects: { data: Record<string, unknown> };
  intel: { data: Record<string, unknown>; reload(): Promise<unknown> };
  plugin: { data: Record<string, unknown>; reload(): Promise<unknown> };
  queueStatus: string;
  setQueueStatus: (value: string) => void;
}) {
  const reloadQueues = () => {
    void intel.reload();
    void plugin.reload();
  };
  const queueRows = [...asRows(intel.data, ["jobs"]), ...asRows(plugin.data, ["jobs"])].filter((row) =>
    (QUEUE_MATCH[queueStatus] ?? [queueStatus]).includes(String(row.status ?? "").toLowerCase()),
  );
  const rows = (section: (typeof DOOR_SECTIONS)[number]): Row[] =>
    section === "actions"
      ? asRows(actions.data, ["items", "action_items"])
      : section === "speakers"
        ? asRows(speakers.data, ["speakers"])
        : section === "projects"
          ? asRows(projects.data, ["projects"])
          : queueRows;

  const row = (section: (typeof DOOR_SECTIONS)[number], item: Row, index: number) => {
    const key = rowId(item, index);
    if (section === "actions") {
      const meta = [presentValue(item.owner), presentValue(item.meeting_title)].filter(Boolean).join(" · ");
      return (
        <ListRow
          key={key}
          name={String(item.task ?? item.title ?? item.text ?? "Action")}
          meta={meta || undefined}
          state={actionState(item.status)}
          age={ageWords(item.created_at)}
        />
      );
    }
    if (section === "speakers") {
      return (
        <ListRow
          key={key}
          name={String(item.name ?? item.display_name ?? item.label ?? "Speaker")}
          meta={presentValue(item.person_name ?? item.email) || undefined}
          age={ageWords(item.last_seen ?? item.updated_at ?? item.created_at)}
        />
      );
    }
    if (section === "projects") {
      return (
        <ListRow
          key={key}
          name={String(item.name ?? item.title ?? "Project")}
          meta={presentValue(item.summary ?? item.description) || undefined}
          state={item.status ? { word: sentence(item.status), tone: "idle" } : undefined}
          age={ageWords(item.updated_at ?? item.created_at)}
          onOpen={() => openProjectRoom(String(item.id))} // PHILO-17 U30: the Room
          openLabel={`Open ${String(item.name ?? item.title ?? "project")}`}
        />
      );
    }
    const isSummary = Boolean(item.meeting_id) && !item.plugin_id;
    const failed = jobState(item.status).tone === "fail";
    return (
      <ListRow
        key={key}
        name={isSummary ? "Summary" : jobName(item)}
        meta={presentValue(item.meeting_title ?? item.title) || undefined}
        state={jobState(item.status)}
        age={ageWords(item.updated_at ?? item.requested_at ?? item.started_at ?? item.created_at)}
        verbs={
          failed ? (
            <Button
              dense
              onClick={() =>
                void apiFetch(
                  `/api/${isSummary ? "intel/retry" : "plugin-jobs"}/${encodeURIComponent(String(isSummary ? item.meeting_id : item.id))}${isSummary ? "" : "/retry-now"}`,
                  { method: "POST" },
                ).then(reloadQueues)
              }
            >
              {/* HS-202-04 (F07) — one job, one verb: a failed Summary is
                  `Retry` here as in the record; a deferred plugin job is a
                  different object, `Retry background work`. */}
              {isSummary ? "Retry" : "Retry background work"}
            </Button>
          ) : undefined
        }
      />
    );
  };

  return (
    <div className="surface-door meetings-door">
      <ListView label="Meeting plumbing">
        {DOOR_SECTIONS.map((section) => {
          const list = rows(section);
          return (
            <ListDay key={section} label={SECTION_WORDS[section]}>
              {section === "queues" ? (
                <li className="meetings-door-filter">
                  <CycleGadget
                    label="Show background work"
                    value={queueStatus}
                    onChange={(next) => {
                      setQueueStatus(next);
                      window.setTimeout(reloadQueues);
                    }}
                    options={[
                      { value: "pending", label: "Waiting" },
                      { value: "running", label: "Running" },
                      { value: "failed", label: "Failed" },
                      { value: "complete", label: "Done" },
                    ]}
                  />
                </li>
              ) : null}
              {list.length ? (
                list.map((item, index) => row(section, item, index))
              ) : (
                <li className="meetings-door-empty">
                  <SurfaceState empty emptyLabel={section === "queues" ? "Nothing here" : `No ${SECTION_WORDS[section].toLowerCase()} yet`} emptyGlyph="·" />
                </li>
              )}
            </ListDay>
          );
        })}
      </ListView>
      {/* HS-139-03: capture + export config lives on its object. */}
      <MeetingsConfig />
    </div>
  );
}
