import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
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
  CheckGadget,
  LampGadget,
  StringGadget,
} from "../../desk/surface/gadgets";
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
import { humanTime, presentValue } from "../../desk/surface/format";
import { useAction, useCoreWings } from "./core-hooks";
import { CoreResourceGuard, renderHeroSlot } from "./core-layout";

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
  const verbs = (
    <>
      <Button
        dense
        loading={action.busy}
        onClick={() => void invoke("/api/activity/refresh")}
      >
        Refresh now
      </Button>
      <span className="gadget-checkline">
        <CheckGadget
          label="Watching"
          checked={enabled}
          onChange={(next) =>
            void invoke("/api/activity/settings", {
              method: "PUT",
              json: { enabled: next },
            })
          }
        />
        <span className="gadget-checkline-word">
          {enabled ? "Watching" : "Paused"}
        </span>
      </span>
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
        emptyLabel="No activity yet"
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

  const filter = (
    <StringGadget
      label="Filter this view"
      placeholder="FILTER"
      value={query}
      onChange={setQuery}
    />
  );

  return (
    <>
      {renderHeroSlot(hero, verbs)}
      {action.message ? <SurfaceState error={action.message} /> : null}
      {wings.doorOpen ? (
        <>
          <SurfaceSection label="Meeting candidates">
            {filter}
            {list("candidates")}
          </SurfaceSection>
          <SurfaceSection label="Connectors">
            {list("connectors")}
          </SurfaceSection>
        </>
      ) : (
        <SurfaceSection
          label={wings.view === "records" ? "Records" : "Project rules"}
          actions={
            wings.view === "records" ? (
              <ConfirmVerb
                label="Clear records"
                confirmLabel="Clear all?"
                busy={action.busy}
                onConfirm={() =>
                  void invoke("/api/activity/records", { method: "DELETE" })
                }
              />
            ) : undefined
          }
        >
          {filter}
          {list(wings.view as Kind)}
        </SurfaceSection>
      )}
      <SurfaceFooter />
    </>
  );
}
