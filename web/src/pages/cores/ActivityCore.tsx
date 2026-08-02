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
import { useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import {
  CheckGadget,
  LampGadget,
  StringGadget,
} from "../../desk/surface/gadgets";
import { apiFetch, readableError, type JsonRecord } from "../../lib/api";
import { asRows, rowId, useResource } from "../pageSupport";
import {
  ConfirmVerb,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { humanTime, presentValue } from "../../desk/surface/format";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";

const WINGS = [
  { id: "records", label: "Records" },
  { id: "rules", label: "Rules" },
];

export interface CoreProps {
  /** Optional chrome the host renders around the core's own verbs. */
  hero?: (actions: ReactNode) => ReactNode;
  /** The subject this window is scoped to (a qualified ref). */
  scope?: string;
  /** The subject's product label (hosts resolve it; never a raw ref). */
  scopeLabel?: string;
}

export function ActivityCore({ hero }: CoreProps) {
  const [active, setActive] = useState("records");
  const [doorOpen, setDoorOpen] = useState(false);
  useWindowWings(
    <SurfaceWings
      wings={WINGS}
      active={doorOpen ? "" : active}
      onChange={(id) => {
        setDoorOpen(false);
        setActive(id);
      }}
      door="Candidates and connectors"
      doorOpen={doorOpen}
      onDoor={() => setDoorOpen((open) => !open)}
    />,
    [active, doorOpen],
  );
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const status = useResource<JsonRecord>("/api/activity/status", {});
  const records = useResource<JsonRecord>(
    "/api/activity/records?limit=100",
    {},
  );
  const rules = useResource<JsonRecord>("/api/activity/project-rules", {});
  const candidates = useResource<JsonRecord>(
    "/api/activity/meeting-candidates",
    {},
  );
  const connectors = useResource<JsonRecord>(
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
  const invoke = async (
    url: string,
    init: Parameters<typeof apiFetch>[1] = { method: "POST", json: {} },
  ) => {
    setBusy(true);
    setMessage("");
    try {
      await apiFetch(url, init);
      await Promise.all(
        (doorOpen ? ["candidates", "connectors"] : [active]).map((kind) =>
          sources[kind as Kind].resource.reload(),
        ),
      );
      await status.reload();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setBusy(false);
    }
  };
  const enabled = Boolean(
    (status.data.settings as JsonRecord | undefined)?.enabled,
  );
  const verbs = (
    <>
      <Button
        dense
        loading={busy}
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
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        empty={!rows.length}
        emptyLabel="No activity yet"
        emptyGlyph="◍"
        onRetry={() => void resource.reload()}
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
      </SurfaceState>
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
      {hero ? hero(verbs) : <SurfaceVerbs>{verbs}</SurfaceVerbs>}
      {message ? <SurfaceState error={message} /> : null}
      {doorOpen ? (
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
          label={active === "records" ? "Records" : "Project rules"}
          actions={
            active === "records" ? (
              <ConfirmVerb
                label="Clear records"
                confirmLabel="Clear all?"
                busy={busy}
                onConfirm={() =>
                  void invoke("/api/activity/records", { method: "DELETE" })
                }
              />
            ) : undefined
          }
        >
          {filter}
          {list(active as Kind)}
        </SurfaceSection>
      )}
    </>
  );
}
