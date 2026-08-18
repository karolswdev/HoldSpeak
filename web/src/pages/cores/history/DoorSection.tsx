// HS-117-09 — extracted from HistoryCore (lines 1100-1205).
import { openSurfaceOr } from "../../../desk/shell";
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
} from "../../../desk/surface/Surface";
import {
  CycleGadget,
  GadgetGroup,
  GadgetRow,
  LampGadget,
} from "../../../desk/surface/gadgets";
import { humanTime, presentValue } from "../../../desk/surface/format";
import { asRows, rowId } from "../../pageSupport";
import { DOOR_SECTIONS, displayState } from "./helpers";
import { apiFetch } from "../../../lib/api";
import { MeetingsConfig } from "./MeetingsConfig";

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
  const doorRows = (section: (typeof DOOR_SECTIONS)[number]) =>
    section === "actions"
      ? asRows(actions.data, ["items", "action_items"])
      : section === "speakers"
        ? asRows(speakers.data, ["speakers"])
        : section === "projects"
          ? asRows(projects.data, ["projects"])
          : [...asRows(intel.data, ["jobs"]), ...asRows(plugin.data, ["jobs"])];
  return (
    <div className="surface-door">
      {DOOR_SECTIONS.map((section) => (
        <SurfaceSection
          key={section}
          label={section[0].toUpperCase() + section.slice(1)}
        >
          {section === "queues" ? (
            <GadgetGroup>
              <GadgetRow label="STATUS">
                <CycleGadget
                  label="Queue status"
                  value={queueStatus}
                  onChange={(next) => {
                    setQueueStatus(next);
                    window.setTimeout(() => {
                      void intel.reload();
                      void plugin.reload();
                    });
                  }}
                  options={[
                    { value: "pending", label: "Queued" },
                    { value: "running", label: "Running" },
                    { value: "failed", label: "Failed" },
                    { value: "complete", label: "Succeeded" },
                  ]}
                />
              </GadgetRow>
            </GadgetGroup>
          ) : null}
          {doorRows(section).length ? (
            <SurfaceRows>
              {doorRows(section).map((row, index) => (
                <SurfaceRow
                  key={rowId(row, index)}
                  title={String(
                    row.title ?? row.name ?? row.text ?? row.kind ?? section,
                  )}
                  detail={
                    humanTime(row.started_at ?? row.created_at) ||
                    presentValue(row.owner ?? row.status ?? row.summary) ||
                    undefined
                  }
                  meta={
                    row.status === "failed" ? (
                      <LampGadget
                        on
                        tone="fail"
                        label={displayState(row.status ?? row.kind ?? section)}
                      />
                    ) : (
                      <span className="gadget-chip">
                        {displayState(row.status ?? row.kind ?? section)}
                      </span>
                    )
                  }
                  onOpen={
                    section === "projects"
                      ? () =>
                          openSurfaceOr(
                            "open-project-memory",
                            "/history",
                            `project:${String(row.id)}`,
                          )
                      : undefined
                  }
                  verbs={
                    section === "queues" && row.status === "failed" ? (
                      <Button
                        dense
                        onClick={() =>
                          void apiFetch(
                            `/api/${row.meeting_id ? "intel/retry" : "plugin-jobs"}/${encodeURIComponent(String(row.meeting_id ?? row.id))}${row.meeting_id ? "" : "/retry-now"}`,
                            { method: "POST" },
                          ).then(() => {
                            void intel.reload();
                            void plugin.reload();
                          })
                        }
                      >
                        {row.meeting_id
                          ? "Retry intelligence"
                          : "Retry background work"}
                      </Button>
                    ) : undefined
                  }
                />
              ))}
            </SurfaceRows>
          ) : (
            <SurfaceState empty emptyLabel="Nothing here" emptyGlyph="·" />
          )}
        </SurfaceSection>
      ))}
      {/* HS-139-03: capture + export config lives on its object. */}
      <MeetingsConfig />
    </div>
  );
}
