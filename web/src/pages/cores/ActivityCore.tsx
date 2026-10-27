// HS-95-04 — the Activity surface's core: everything the flat page did,
// minus the flat chrome. Cores are host-agnostic (Constitution, Article I:
// features do not own surfaces): no page chrome, no router coupling — the
// guard in tests/unit/test_page_cores_guard.py keeps it that way. The
// `hero` slot lets a host wrap the core's own verbs in its chrome; the
// desk window passes nothing and gets the surface verb bar.
// HS-98-04 — re-crafted native on the surface kit; wire calls unchanged.
// HS-111-08 — conformance: gadget-kit controls (CheckGadget, StringGadget,
// LampGadget/chip tokens), errors in-flow, and the wings posture fix —
// Candidates/Connectors fold behind the gear door (they are
// configuration, not daily reads).
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  LampGadget,
  StringGadget,
} from "../../desk/surface/gadgets";
import { DotWord, Toolbar, ToolGlyph } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { apiFetch } from "../../lib/api";
import { asRows, rowId, useResource } from "../pageSupport";
import type {
  ActivityStatusResponse,
  ActivityRecordsResponse,
  ActivityRulesResponse,
  ActivityCandidatesResponse,
  ActivityConnectorsResponse,
  CoreProps,
} from "./core-types";
import {
  ConfirmVerb,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
} from "../../desk/surface/Surface";
import { deSnake, humanTime, presentValue } from "../../desk/surface/format";
import { ListDay, ListRow, ListView, ageWords, useWaitWord, type ListRowState } from "../../desk/surface/objects/ListView";
import { useAction, useCoreWings } from "./core-hooks";
import { CoreResourceGuard, renderHeroSlot } from "./core-layout";
import "./activity.css";
import { ActivityFinishedReceipts } from "./ActivityFinishedReceipts";

const WINGS = [
  { id: "records", label: "Records" },
  { id: "rules", label: "Rules" },
];

export function ActivityCore({ hero }: CoreProps) {
  const wings = useCoreWings(WINGS, "records", "Candidates and connectors");
  const [query, setQuery] = useState("");
  const action = useAction();
  const status = useResource<ActivityStatusResponse>("/api/activity/status", {});
  const records = useResource<ActivityRecordsResponse>(
    "/api/activity/records?limit=100",
    {},
  );
  const rules = useResource<ActivityRulesResponse>("/api/activity/project-rules", {});
  const candidates = useResource<ActivityCandidatesResponse>(
    "/api/activity/meeting-candidates",
    {},
  );
  const connectors = useResource<ActivityConnectorsResponse>(
    "/api/activity/enrichment/connectors",
    {},
  );
  const sources = {
    records: { resource: records, keys: ["records", "items"] },
    rules: { resource: rules, keys: ["rules"] },
    candidates: { resource: candidates, keys: ["candidates"] },
    connectors: { resource: connectors, keys: ["connectors"] },
  } as const;
  type Kind = keyof typeof sources;
  const invoke = (
    url: string,
    init: Parameters<typeof apiFetch>[1] = { method: "POST", json: {} },
  ) =>
    action.run(async () => {
      await apiFetch(url, init);
      await Promise.all(
        (wings.doorOpen ? ["candidates", "connectors"] : [wings.view]).map(
          (kind) => sources[kind as Kind].resource.reload(),
        ),
      );
      await status.reload();
    });
  const enabled = Boolean(
    status.data.settings?.enabled,
  );
  // Window grammar: the toolbar's verbs, icon + label; Watching is a quiet
  // toggle (pressed while the desk watches); Clear records sits behind its
  // confirm on the Records face.
  const recordsFace = !wings.doorOpen && wings.view === "records";
  useWindowInterior(recordsFace ? "list" : null);
  const verbs = (
    <>
      <Button
        dense
        variant="secondary"
        loading={action.busy}
        onClick={() => void invoke("/api/activity/refresh")}
      >
        <ToolGlyph kind="retry" />
        Refresh now
      </Button>
      <Button
        dense
        variant="secondary"
        aria-pressed={enabled}
        data-testid="activity-watching"
        onClick={() =>
          void invoke("/api/activity/settings", {
            method: "PUT",
            json: { enabled: !enabled },
          })
        }
      >
        <DotWord tone={enabled ? "ok" : "warn"}>{enabled ? "Watching" : "Paused"}</DotWord>
      </Button>
      {recordsFace ? (
        <ConfirmVerb
          label="Clear records"
          confirmLabel="Clear all?"
          busy={action.busy}
          onConfirm={() =>
            void invoke("/api/activity/records", { method: "DELETE" })
          }
        />
      ) : null}
    </>
  );

  const list = (kind: Kind) => {
    const { resource, keys } = sources[kind];
    const rows = asRows(resource.data, [...keys]).filter(
      (row) =>
        !query ||
        JSON.stringify(row).toLowerCase().includes(query.toLowerCase()),
    );
    return (
      <CoreResourceGuard
        resource={resource}
        empty={!rows.length}
        emptyLabel={kind === "rules" ? "No rules yet" : "No activity yet"}
        emptyGlyph="◍"
      >
        <SurfaceRows>
          {rows.map((row, index) => {
            const id = rowId(row, index);
            const off = row.enabled === false || row.status === "dismissed";
            const token = String(
              row.kind ??
                row.status ??
                (row.enabled === false ? "off" : "local"),
            );
            return (
              <SurfaceRow
                key={id}
                title={String(
                  row.title ??
                    row.name ??
                    row.domain ??
                    row.project ??
                    row.source ??
                    "Activity item",
                )}
                detail={
                  humanTime(row.occurred_at) ||
                  presentValue(
                    row.url ?? row.detail ?? row.pattern ?? row.status,
                  ) ||
                  undefined
                }
                meta={
                  off ? (
                    <LampGadget on tone="warn" label={token} />
                  ) : (
                    <span className="gadget-chip">{token}</span>
                  )
                }
                verbs={
                  <>
                    {kind === "connectors" ? (
                      <Button
                        dense
                        onClick={() =>
                          void invoke(
                            `/api/activity/enrichment/connectors/${encodeURIComponent(id)}/dry-run?limit=25`,
                            { method: "GET" },
                          )
                        }
                      >
                        Dry run
                      </Button>
                    ) : null}
                    {kind === "candidates" && row.status !== "started" ? (
                      <Button
                        dense
                        onClick={() =>
                          void invoke(
                            `/api/activity/meeting-candidates/${encodeURIComponent(id)}/start`,
                          )
                        }
                      >
                        Start meeting
                      </Button>
                    ) : null}
                    {kind === "rules" ? (
                      <ConfirmVerb
                        label="Delete"
                        confirmLabel="Delete?"
                        onConfirm={() =>
                          void invoke(
                            `/api/activity/project-rules/${encodeURIComponent(id)}`,
                            { method: "DELETE" },
                          )
                        }
                      />
                    ) : null}
                  </>
                }
              />
            );
          })}
        </SurfaceRows>
      </CoreResourceGuard>
    );
  };

  const search = (
    <span className="activity-search">
      <StringGadget
        label="Search activity"
        placeholder="Search activity"
        value={query}
        onChange={setQuery}
      />
    </span>
  );
  const recordRows = asRows(records.data, ["records", "items"]);

  return (
    <>
      {renderHeroSlot(hero, null)}
      <Toolbar label="Activity" data-testid="activity-toolbar" trailing={search}>
        {verbs}
      </Toolbar>
      {action.message ? <SurfaceState error={action.message} /> : null}
      {wings.doorOpen ? (
        <ActivityGear
          query={query}
          candidates={asRows(candidates.data, ["candidates"])}
          connectors={asRows(connectors.data, ["connectors"])}
          candidatesLoading={candidates.loading}
          connectorsLoading={connectors.loading}
          onDryRun={(id) =>
            void invoke(
              `/api/activity/enrichment/connectors/${encodeURIComponent(id)}/dry-run?limit=25`,
              { method: "GET" },
            )
          }
          onStart={(id) =>
            void invoke(`/api/activity/meeting-candidates/${encodeURIComponent(id)}/start`)
          }
        />
      ) : wings.view === "records" ? (
        // One list view: the finished receipts and the watched pages.
        <ActivityFinishedReceipts query={query} records={recordRows} />
      ) : (
        <SurfaceSection label="Project rules">
          {list("rules")}
        </SurfaceSection>
      )}
    </>
  );
}

/* Window Program W1 (2026-10-27): the gear wing on the window grammar.
   A connector reads by its own name and what it does ("Enrich with the
   CLI"), a dot-and-word state and a quiet age; never `first-party` or a
   `CLI_ENRICHMENT` token. A read that never answers says so. */
const CONNECTOR_KIND_WORDS: Record<string, string> = {
  cli_enrichment: "Enrich with the CLI",
  candidate_inference: "Find meeting candidates",
};

function kindWords(kind: unknown): string {
  const key = String(kind ?? "");
  if (CONNECTOR_KIND_WORDS[key]) return CONNECTOR_KIND_WORDS[key];
  const words = deSnake(key).toLowerCase();
  return words ? words[0].toUpperCase() + words.slice(1) : "";
}

function connectorState(row: Record<string, unknown>): ListRowState {
  if (row.last_error) return { word: "Failed", tone: "fail" };
  if (row.enabled === false) return { word: "Off", tone: "idle" };
  const cli = row.cli_status as Record<string, unknown> | undefined;
  if (row.requires_cli && cli && cli.available === false) return { word: "CLI not found", tone: "warn" };
  return { word: "On", tone: "ok" };
}

function ActivityGear({
  query,
  candidates,
  connectors,
  candidatesLoading,
  connectorsLoading,
  onDryRun,
  onStart,
}: {
  query: string;
  candidates: Record<string, unknown>[];
  connectors: Record<string, unknown>[];
  candidatesLoading: boolean;
  connectorsLoading: boolean;
  onDryRun(id: string): void;
  onStart(id: string): void;
}) {
  const match = (row: Record<string, unknown>) =>
    !query || JSON.stringify(row).toLowerCase().includes(query.toLowerCase());
  const candidateWait = useWaitWord(candidatesLoading && !candidates.length);
  const connectorWait = useWaitWord(connectorsLoading && !connectors.length);
  const shownCandidates = candidates.filter(match);
  const shownConnectors = connectors.filter(match);
  return (
    <ListView label="Candidates and connectors">
      <ListDay label="Meeting candidates">
        {candidateWait ? (
          <ListRow name="Meeting candidates" state={candidateWait} />
        ) : shownCandidates.length ? (
          shownCandidates.map((row, index) => {
            const id = rowId(row, index);
            return (
              <ListRow
                key={id}
                name={String(row.title ?? row.name ?? "Meeting candidate")}
                meta={presentValue(row.source_connector_id ? kindWords(row.source_connector_id) : row.source) || undefined}
                state={row.status ? { word: kindWords(row.status), tone: row.status === "started" ? "ok" : "idle" } : undefined}
                age={ageWords(row.starts_at ?? row.created_at)}
                verbs={row.status !== "started" ? (
                  <Button dense onClick={() => onStart(id)}>Start meeting</Button>
                ) : undefined}
              />
            );
          })
        ) : (
          <li><SurfaceState empty emptyLabel="No meeting candidates yet" emptyGlyph="·" /></li>
        )}
      </ListDay>
      <ListDay label="Connectors">
        {connectorWait ? (
          <ListRow name="Connectors" state={connectorWait} />
        ) : shownConnectors.length ? (
          shownConnectors.map((row, index) => {
            const id = rowId(row, index);
            return (
              <ListRow
                key={id}
                name={String(row.label ?? row.name ?? kindWords(row.id))}
                meta={kindWords(row.kind) || undefined}
                state={connectorState(row)}
                age={row.last_run_at ? `Ran ${ageWords(row.last_run_at)}` : "Never ran"}
                verbs={<Button dense onClick={() => onDryRun(id)}>Dry run</Button>}
              />
            );
          })
        ) : (
          <li><SurfaceState empty emptyLabel="No connectors" emptyGlyph="·" /></li>
        )}
      </ListDay>
    </ListView>
  );
}
