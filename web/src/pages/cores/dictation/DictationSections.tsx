// Runtime, Hooks, and Nudges — small configure-door sections.
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { openSurfaceOr } from "../../../desk/shell";
import { apiFetch } from "../../../lib/api";
import { asRows, rowId, useResource } from "../../pageSupport";
import type {
  DictationAgentHooksResponse,
  ActivityNudgesResponse,
} from "../core-types";
import {
  presentValue,
  streamDate,
  streamTime,
} from "../../../desk/surface/format";
import {
  SurfaceCode,
  SurfaceState,
} from "../../../desk/surface/Surface";
import {
  CheckGadget,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
} from "../../../desk/surface/gadgets";

/* HS-112-01 — one dial: the runtime destination is edited ONLY in the
   Prefs `models` module. This face states the fact and hands over. */
export function Runtime() {
  return (
    <GadgetGroup label="Dictation runtime">
      <div className="prefs-elsewhere">
        <span className="prefs-elsewhere-fact">RUNS ON LIVES IN MODELS</span>
        <Button
          dense
          onClick={() => openSurfaceOr("configure-runs-on", "/settings")}
        >
          Open Models
        </Button>
      </div>
    </GadgetGroup>
  );
}

/* HS-111-02 — Hooks is a designed face, not a JSON dump: the capture
   check, one fact row per agent destination with a SET/— chip (a
   recent captured session = SET), the raw wire behind Raw trace. */
export function Hooks() {
  const [capture, setCapture] = useState(false);
  const resource = useResource<DictationAgentHooksResponse>(
    `/api/dictation/agent-hooks?capture_messages=${capture}`,
    {},
  );
  const destinations = (resource.data.destinations ?? {}) as Record<string, unknown>;
  const agents = (resource.data.agents ?? {}) as Record<string, unknown>;
  const chip = (agent: string) => {
    const info = agents[agent] as Record<string, unknown> | undefined;
    const set = Boolean(info && info.latest_session);
    return (
      <span className="gadget-chip" data-set={set || undefined}>
        {set ? "SET" : "—"}
      </span>
    );
  };
  return (
    <GadgetGroup label="Automation hooks">
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <GadgetRow label="Capture messages" fact="hook template option">
          <CheckGadget
            label="Capture messages"
            checked={capture}
            onChange={setCapture}
          />
        </GadgetRow>
        <GadgetRow label="Claude" fact={presentValue(destinations.claude)}>
          {chip("claude")}
        </GadgetRow>
        <GadgetRow label="Codex" fact={presentValue(destinations.codex)}>
          {chip("codex")}
        </GadgetRow>
        <FoldGadget title="Raw trace">
          <SurfaceCode>{JSON.stringify(resource.data, null, 2)}</SurfaceCode>
        </FoldGadget>
      </SurfaceState>
    </GadgetGroup>
  );
}

/* HS-111-02 — nudges are ledger rows: HH:MM · domain · KIND with the
   USE / DISMISS verbs. The surveillance sentence died. */
export function Nudges() {
  const resource = useResource<ActivityNudgesResponse>("/api/activity/nudges?limit=8", {});
  const rows = asRows(resource.data, ["nudges", "items"]);
  const act = async (
    row: Record<string, unknown>,
    action: "select" | "dismiss",
  ) => {
    await apiFetch(
      action === "select"
        ? "/api/activity/nudges/select"
        : `/api/activity/nudges/${encodeURIComponent(String(row.id ?? row.key))}/dismiss`,
      {
        method: "POST",
        json: action === "select" ? { record_id: row.record_id ?? row.id } : {},
      },
    );
    await resource.reload();
  };
  const token = (row: Record<string, unknown>): string => {
    const citation = (
      Array.isArray(row.citations) ? row.citations[0] : null
    ) as Record<string, unknown> | null;
    const time = streamTime(
      streamDate(citation?.last_seen_at ?? row.window_since),
    );
    const where =
      presentValue(citation?.domain) ||
      presentValue(row.title ?? row.text) ||
      "recent work";
    const kind = String(
      citation?.entity_type ?? row.kind ?? "activity",
    ).toUpperCase();
    return [time, where, kind].filter(Boolean).join(" · ");
  };
  return (
    <GadgetGroup label="Activity nudges">
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        empty={!rows.length}
        emptyLabel="No recent activity to cite"
        emptyGlyph="⌁"
        onRetry={() => void resource.reload()}
      >
        {rows.map((row, index) => (
          <div className="speak-nudge-row" key={rowId(row, index)}>
            <span className="speak-nudge-token">{token(row)}</span>
            <span className="surface-row-verbs">
              <Button dense onClick={() => void act(row, "select")}>
                Use
              </Button>
              <Button
                dense
                variant="ghost"
                onClick={() => void act(row, "dismiss")}
              >
                Dismiss
              </Button>
            </span>
          </div>
        ))}
      </SurfaceState>
    </GadgetGroup>
  );
}
