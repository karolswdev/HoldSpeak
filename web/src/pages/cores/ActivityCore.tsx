// HS-95-04 — the Activity surface's core: everything the flat page did,
// minus the flat chrome. Cores are host-agnostic (Constitution, Article I:
// features do not own surfaces): no page chrome, no router coupling — the
// guard in tests/unit/test_page_cores_guard.py keeps it that way. The
// `hero` slot lets a host wrap the core's own verbs in its chrome; the
// desk window passes nothing and gets the surface verb bar.
// HS-98-04 — re-crafted native on the surface kit; wire calls unchanged.
import { useState, type ReactNode } from "react";
import {
  Button,
  Field,
  InlineMessage,
  StatusPill,
  Switch,
  Tabs,
  TextInput,
} from "../../components/signal/Signal";
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

const TABS = ["records", "rules", "candidates", "connectors"].map((id) => ({
  id,
  label: id[0].toUpperCase() + id.slice(1),
}));

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
  const source =
    active === "records"
      ? records
      : active === "rules"
        ? rules
        : active === "candidates"
          ? candidates
          : connectors;
  const rows = asRows(
    source.data,
    active === "records"
      ? ["records", "items"]
      : active === "rules"
        ? ["rules"]
        : active === "candidates"
          ? ["candidates"]
          : ["connectors"],
  );
  const filtered = rows.filter(
    (row) =>
      !query || JSON.stringify(row).toLowerCase().includes(query.toLowerCase()),
  );
  const invoke = async (
    url: string,
    init: Parameters<typeof apiFetch>[1] = { method: "POST", json: {} },
  ) => {
    setBusy(true);
    setMessage("");
    try {
      await apiFetch(url, init);
      await source.reload();
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
      <Switch
        label={enabled ? "Watching" : "Paused"}
        checked={enabled}
        onChange={(event) =>
          void invoke("/api/activity/settings", {
            method: "PUT",
            json: { enabled: event.target.checked },
          })
        }
      />
    </>
  );
  return (
    <>
      {hero ? hero(verbs) : <SurfaceVerbs>{verbs}</SurfaceVerbs>}
      {message ? <InlineMessage tone="error">{message}</InlineMessage> : null}
      <SurfaceSection
        label="Activity intelligence"
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
        <Tabs
          label="Activity sections"
          tabs={TABS}
          active={active}
          onChange={setActive}
        />
        <Field label="Filter this view">
          {({ id }) => (
            <TextInput
              id={id}
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          )}
        </Field>
        <SurfaceState
          loading={source.loading}
          error={source.error}
          empty={!filtered.length}
          emptyLabel="No activity yet"
          emptyGlyph="◍"
          onRetry={() => void source.reload()}
        >
          <SurfaceRows>
            {filtered.map((row, index) => {
              const id = rowId(row, index);
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
                    <StatusPill
                      tone={
                        row.enabled === false || row.status === "dismissed"
                          ? "warning"
                          : "neutral"
                      }
                    >
                      {String(
                        row.kind ??
                          row.status ??
                          (row.enabled === false ? "off" : "local"),
                      )}
                    </StatusPill>
                  }
                  verbs={
                    <>
                      {active === "connectors" ? (
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
                      {active === "candidates" && row.status !== "started" ? (
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
                      {active === "rules" ? (
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
      </SurfaceSection>
    </>
  );
}
