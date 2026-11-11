import { useState } from "react";
import {
  CheckGadget,
  CycleGadget,
  EgressChip,
  InspectorForm,
  PaneInspector,
  PadGadget,
  PreferencePane,
  StringGadget,
  type InspectorRow,
  type ListVerb,
} from "../../../desk/surface";
import type { CoreProps } from "../../../pages/cores/core-types";
import { SignInWell } from "../../../pages/cores/connections/ConnectionsPane";
import { RoomList, type RoomEntry } from "../RoomList";
import { useDoorController, type DoorController } from "./useDoorController";

export function AddSourcesWell({
  projectId,
  onAdded,
  onCancel,
}: {
  projectId: string;
  onAdded(): void;
  onCancel(): void;
}) {
  const ctrl = useDoorController({ projectId, onAdded, onCancel });
  return <DoorSourceRows ctrl={ctrl} />;
}
export function DoorCore(_props: CoreProps) {
  const ctrl = useDoorController();
  return (
    <PreferencePane label="New project">
      <DoorSourceRows ctrl={ctrl} />
    </PreferencePane>
  );
}
const providerName = (name: string) =>
  name === "github"
    ? "GitHub"
    : name === "jira"
      ? "Jira"
      : name === "confluence"
        ? "Confluence"
        : name;
const watchLabel = (key: string) =>
  ({
    open_prs: "Open PRs",
    ci: "CI",
    overdue: "Overdue",
    due_7_days: "Due in 7 days",
    blocked: "Blocked",
    recent_blogs: "Recent blogs",
    pages_by_id: "Pages by ID",
  })[key] || key;
export function DoorSourceRows({ ctrl }: { ctrl: DoorController }) {
  const [picked, setPicked] = useState<string | null>(null),
    [seat, setSeat] = useState("project");
  const source = ctrl.sources.find((row) => row.provider === picked);
  const found = ctrl.preview?.found.find((row) => row.id === picked);
  const tool = ctrl.tools.find((row) => row.provider_id === source?.provider);
  const selectedSources = ctrl.sources.filter(
    (row) => row.connected && row.scope,
  );
  const canAdd =
    selectedSources.length > 0 ||
    Boolean(
      ctrl.preview?.sources.some((source) => source.state === "checked"),
    ) ||
    Boolean(ctrl.preview?.found.some((row) => row.selected));
  const destinations = [
    ...new Set(
      [
        ...selectedSources.map((row) => row.host),
        ...(ctrl.preview?.sources ?? [])
          .filter((source) => source.state === "checked")
          .map(
            (source) =>
              source.site || (source.provider === "github" ? "github.com" : ""),
          ),
      ].filter(Boolean),
    ),
  ];
  const rows: RoomEntry[] =
    seat === "found"
      ? [
          ...(ctrl.preview?.sources ?? []).map((source, i) => ({
            id: `source:${i}`,
            name: source.label,
            kind: "source",
            kindWord: providerName(source.provider),
            cells: {
              state:
                source.state === "checked"
                  ? ""
                  : source.reason || "Could not check",
            },
            facts: [{ label: "Reason", value: source.reason }],
          })),
          ...(ctrl.preview?.found ?? []).map((row) => ({
            id: row.id,
            name: row.title,
            kind: row.kind,
            kindWord: row.kind === "meeting" ? "Meeting" : "Note",
            cells: {
              state:
                row.linkState === "failed"
                  ? "Could not add"
                  : row.linkState === "linked"
                    ? "Added"
                    : row.selected
                      ? "Selected"
                      : "Removed",
            },
            facts: [
              { label: "What it says", value: row.detail },
              { label: "Reason", value: row.linkError },
            ],
          })),
        ]
      : ctrl.sources.map((row) => ({
          id: row.provider,
          name: row.scope || providerName(row.provider),
          kind: "source",
          kindWord: providerName(row.provider),
          cells: {
            state: !row.connected
              ? "Sign in again"
              : row.state === "cant_check"
                ? "Could not check"
                : "",
          },
          facts: [
            { label: "What it says", value: row.plain },
            { label: "Reason", value: row.reason },
          ],
          open: () => {
            setPicked(row.provider);
            setSeat("source");
            if (row.connected && !row.pickerItems.length)
              ctrl.openPicker(row.provider);
          },
        }));
  const verbs: ListVerb[] = [
    {
      id: "create",
      label: ctrl.projectId ? "Add" : "Create project",
      enabled: () =>
        !ctrl.creating &&
        (Boolean(ctrl.projectId) ? canAdd : Boolean(ctrl.outcome.trim())),
      run: ctrl.create,
    },
    { id: "cancel", label: "Cancel", run: ctrl.cancel },
    {
      id: "preview",
      label: "Check links",
      enabled: () => Boolean(ctrl.sourcePaste.trim()) && !ctrl.previewing,
      run: () => {
        ctrl.previewSources();
        setSeat("found");
      },
    },
    {
      id: "connect",
      label: "Connect",
      enabled: () => Boolean(source && !source.connected),
      run: () => {
        if (source) {
          ctrl.connect(source.provider);
          setSeat("source");
        }
      },
    },
    {
      id: "choose",
      label: "Choose source",
      enabled: () => Boolean(source?.connected),
      run: () => {
        if (source) {
          ctrl.openPicker(source.provider);
          setSeat("source");
        }
      },
    },
    {
      id: "more",
      label: "More sources",
      enabled: () => Boolean(source?.pickerCursor) && !source?.pickerLoading,
      run: () => {
        if (source) ctrl.loadMorePicker(source.provider);
      },
    },
    {
      id: "all",
      label: "Add all",
      enabled: () => Boolean(ctrl.preview?.found.length),
      run: ctrl.selectAllFound,
    },
    {
      id: "remove",
      label: "Remove from selection",
      enabled: () => Boolean(found?.selected && found.linkState !== "linked"),
      run: () => {
        if (found) ctrl.removeFound(found.id);
      },
    },
    {
      id: "retry",
      label: "Retry",
      enabled: () => found?.linkState === "failed",
      run: () => {
        if (found) ctrl.retryFound(found.id);
      },
    },
  ];
  const fields: InspectorRow[] =
    seat === "project"
      ? [
          ...(!ctrl.projectId
            ? [
                {
                  label: "Name",
                  control: (
                    <StringGadget
                      label="Project name"
                      value={ctrl.outcome}
                      onChange={ctrl.setOutcome}
                    />
                  ),
                },
              ]
            : []),
          {
            label: "Links",
            control: (
              <PadGadget
                label="Source links"
                value={ctrl.sourcePaste}
                onChange={ctrl.setSourcePaste}
              />
            ),
          },
          { label: "People", control: ctrl.preview?.people.join(" · ") },
        ]
      : source
        ? [
            ...(!source.connected && tool
              ? [
                  {
                    label: "Account",
                    control: (
                      <SignInWell
                        tool={tool}
                        busy={ctrl.busy === source.provider}
                        onRecheck={() => ctrl.recheck(source.provider)}
                        onAddAccount={(site, email) =>
                          ctrl.addAccount(source.provider, site, email)
                        }
                      />
                    ),
                  },
                ]
              : []),
            ...(source.connected
              ? [
                  {
                    label: "Find",
                    control: (
                      <StringGadget
                        label="Find source"
                        value={source.pickerQuery}
                        onChange={(query) =>
                          ctrl.searchPicker(source.provider, query)
                        }
                      />
                    ),
                  },
                  {
                    label: "Source",
                    control: (
                      <CycleGadget
                        roster
                        label="Source"
                        value={
                          source.scopeRaw && typeof source.scopeRaw === "string"
                            ? source.scopeRaw
                            : ""
                        }
                        options={[
                          { value: "", label: "Choose a source" },
                          ...source.pickerItems.map((item) => ({
                            value: item.value,
                            label:
                              item.label +
                              (item.detail ? ` · ${item.detail}` : ""),
                          })),
                        ]}
                        onChange={(value) => {
                          const item = source.pickerItems.find(
                            (item) => item.value === value,
                          );
                          if (item)
                            ctrl.pickScope(
                              source.provider,
                              item.value,
                              item.label,
                              item.value,
                            );
                        }}
                      />
                    ),
                  },
                  ...Object.entries(source.toggles).map(([key, on]) => ({
                    label: watchLabel(key),
                    control: (
                      <CheckGadget
                        label={watchLabel(key)}
                        checked={on}
                        onChange={() => ctrl.toggleWatch(source.provider, key)}
                      />
                    ),
                  })),
                  ...(source.provider === "github"
                    ? [
                        {
                          label: "Base branch",
                          control: (
                            <StringGadget
                              label="Base branch"
                              value={source.adjust.base || "main"}
                              onChange={(base) =>
                                ctrl.updateAdjust(source.provider, { base })
                              }
                            />
                          ),
                        },
                        {
                          label: "Labels",
                          control: (
                            <StringGadget
                              label="Labels"
                              value={source.adjust.labels || ""}
                              onChange={(labels) =>
                                ctrl.updateAdjust(source.provider, { labels })
                              }
                            />
                          ),
                        },
                        {
                          label: "Drafts",
                          control: (
                            <CheckGadget
                              label="Drafts"
                              checked={Boolean(source.adjust.drafts)}
                              onChange={(drafts) =>
                                ctrl.updateAdjust(source.provider, { drafts })
                              }
                            />
                          ),
                        },
                      ]
                    : source.provider === "confluence"
                      ? [
                          {
                            label: "Space key",
                            control: (
                              <StringGadget
                                label="Space key"
                                value={source.adjust.spaceKey || ""}
                                onChange={(spaceKey) =>
                                  ctrl.updateAdjust(source.provider, {
                                    spaceKey,
                                  })
                                }
                              />
                            ),
                          },
                        ]
                      : [
                          {
                            label: "Issue types",
                            control: (
                              <StringGadget
                                label="Issue types"
                                value={
                                  source.adjust.issueTypes?.join(", ") || ""
                                }
                                onChange={(value) =>
                                  ctrl.updateAdjust(source.provider, {
                                    issueTypes: value
                                      .split(",")
                                      .map((value) => value.trim())
                                      .filter(Boolean),
                                  })
                                }
                              />
                            ),
                          },
                          {
                            label: "JQL",
                            control: (
                              <StringGadget
                                label="JQL filter"
                                value={source.adjust.jql || ""}
                                onChange={(jql) =>
                                  ctrl.updateAdjust(source.provider, { jql })
                                }
                              />
                            ),
                          },
                        ]),
                ]
              : []),
          ]
        : [];
  return (
    <RoomList
      label={ctrl.projectId ? "Add sources" : "New project"}
      rows={rows}
      selectedId={picked}
      onSelect={(id) => {
        setPicked(id);
        if (seat !== "found") {
          setSeat("source");
          const row = ctrl.sources.find((row) => row.provider === id);
          if (row?.connected) ctrl.openPicker(id);
        }
      }}
      verbs={verbs}
      loading={!ctrl.loaded || ctrl.previewing}
      error={ctrl.error}
      empty="No sources found"
      field={
        <CycleGadget
          label="Source view"
          value={seat}
          options={[
            { value: "project", label: ctrl.projectId ? "Links" : "Project" },
            { value: "source", label: "Source" },
            { value: "found", label: "Found" },
          ]}
          onChange={setSeat}
        />
      }
    >
      {seat !== "found" ? (
        <PaneInspector
          label={
            seat === "project"
              ? ctrl.projectId
                ? "Add sources"
                : "New project"
              : providerName(source?.provider || "Source")
          }
        >
          <InspectorForm
            rows={fields}
            completion={{
              cancel: ctrl.cancel,
              leading: destinations.map((host) => (
                <EgressChip key={host} scope="cloud" label={host} />
              )),
              primary: {
                label: ctrl.projectId ? "Add" : "Create project",
                busy: ctrl.creating,
                disabled: ctrl.projectId ? !canAdd : !ctrl.outcome.trim(),
                run: ctrl.create,
              },
            }}
          />
        </PaneInspector>
      ) : undefined}
    </RoomList>
  );
}
