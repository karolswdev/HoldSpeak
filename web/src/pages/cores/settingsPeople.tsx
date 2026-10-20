/* Conductor R7: Settings › People — People MCP access (canvas K7a, RATIFIED 2026-10-07).
 *
 * The owner: "the default should be on, for HOLDSPEAK_MCP_PEOPLE_ACCESS, and I guess there's an
 * affordance to set it somewhere, right?" Ratified: (1) "Yes" (this module, as drawn); (2) "Of course
 * it should, buddy!" (while the variable overrides the setting, the strip is disabled).
 *
 * One FilterTokens strip OFF / READ / WRITE on the real GET / PUT /api/settings/people-access (an
 * admitted owner-only kernel operation); the tokens AGENTS · <mode> and SOURCE · <where>; the
 * operation's receipt after a press. No prose (UX-CANON).
 */
import { useCallback, useEffect, useState } from "react";
import { ApiError, apiFetch } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { FilterTokens, FoldGadget, GadgetGroup, GadgetRow, StateChip, StringGadget, SurfaceState } from "../../desk/surface";
import { useOwnerName } from "../../desk/firstrun/ownerName";
import { OwnerAliasField } from "../../desk/firstrun/OwnerAliasField";

export type PeopleAccess = {
  mode: string;
  effective: string;
  source: "default" | "config" | "env" | string;
  env_var?: string | null;
  agents: string;
};

type AccessReceipt = { ok: boolean; mode: string; code?: string; operationId?: string; at: string };

// PHILO-17 U35: plain words (was OFF / READ / WRITE under "MCP access").
const MODES = [
  { value: "off", label: "Off" },
  { value: "read", label: "Read" },
  { value: "write", label: "Read and write" },
];

/** The source token: where the effective value comes from. */
export function sourceToken(access: PeopleAccess): string {
  if (access.source === "env") return `SOURCE · ${access.env_var || "HOLDSPEAK_MCP_PEOPLE_ACCESS"}`;
  return access.source === "config" ? "SOURCE · SETTING" : "SOURCE · DEFAULT";
}

/** The read's failure, kept apart from the access data (Astra on #919): a code, never a sentence. */
function readFailureCode(cause: unknown): string {
  if (cause instanceof ApiError) {
    const payload = (cause.payload ?? {}) as Record<string, unknown>;
    const code = payload.code ?? payload.error_code;
    return typeof code === "string" && code ? code : `HTTP ${cause.status}`;
  }
  return "unreachable";
}

export function usePeopleAccess() {
  const [access, setAccess] = useState<PeopleAccess | null>(null);
  const [readError, setReadError] = useState<string | null>(null);
  const reload = useCallback(async () => {
    try {
      setAccess(await apiFetch<PeopleAccess>("/api/settings/people-access"));
      setReadError(null);
    } catch (cause) {
      // No stale value is shown as the truth: the access tokens leave, the
      // failure is named, and a press on Retry reads again.
      setAccess(null);
      setReadError(readFailureCode(cause));
    }
  }, []);
  useEffect(() => { void reload(); }, [reload]);
  return { access, setAccess, readError, reload };
}

/* PHILO-15 B57 (owed since 2026-10-04): his name and the other names for
 * him, after first run. The needs-you rule reads them as "me", and a
 * one-letter mishearing of the name ("Carol" for "Karol") still counts. */
export function OwnerNameGroup({ highlight }: { highlight?: string | null } = {}) {
  const owner = useOwnerName();
  if (owner.loading || owner.readError) return <GadgetGroup material="inset" label="You"><SurfaceState loading={owner.loading} error={owner.readError} onRetry={() => void owner.reload()} /></GadgetGroup>;
  return (
    <GadgetGroup material="inset" label="You">
      <GadgetRow wide label="Your name" controlWidth="full" highlight={highlight === "owner.name"}>
        <span className="prefs-text-field" data-testid="settings-owner-name">
          <StringGadget
            label="Your name"
            value={owner.name}
            onChange={owner.setName}
            placeholder="Name"
            inputProps={{ onBlur: () => void owner.flush() }}
          />
        </span>
      </GadgetRow>
      <GadgetRow wide label="Also called" controlWidth="full" highlight={highlight === "owner.aliases"}>
        <span className="prefs-text-field" data-testid="settings-owner-aliases">
          <OwnerAliasField owner={owner} />
        </span>
      </GadgetRow>
      {owner.error ? (
        <GadgetRow label="Receipt">
          <StateChip state="failure" label="NOT SAVED" />
          <Button dense variant="secondary" onClick={() => void owner.flush()}>Retry</Button>
        </GadgetRow>
      ) : null}
    </GadgetGroup>
  );
}

export function PeopleAccessModule({ highlight }: { highlight?: string | null } = {}) {
  const { access, setAccess, readError, reload } = usePeopleAccess();
  const [busy, setBusy] = useState(false);
  const [receipt, setReceipt] = useState<AccessReceipt | null>(null);

  const press = async (mode: string) => {
    if (!access || mode === access.mode) return;
    setBusy(true);
    const at = new Date().toTimeString().slice(0, 5);
    try {
      const next = await apiFetch<PeopleAccess & { operation_id?: string }>("/api/settings/people-access", {
        method: "PUT",
        json: { mode },
      });
      setAccess(next);
      setReceipt({ ok: true, mode, operationId: next.operation_id, at });
    } catch (cause) {
      const payload = cause instanceof ApiError ? (cause.payload as Record<string, unknown>) : {};
      setReceipt({
        ok: false,
        mode,
        code: String(payload?.code ?? payload?.error_code ?? "refused"),
        operationId: typeof payload?.operation_id === "string" ? payload.operation_id : undefined,
        at,
      });
      void reload();
    } finally {
      setBusy(false);
    }
  };

  if (!access && !readError && !receipt) return null;
  const held = access?.source === "env";
  return (
    <GadgetGroup material="inset" label="Agents">
      {readError ? (
        <GadgetRow label="Access">
          <span data-testid="people-access-read-failed" data-code={readError}>
            <StateChip state="failure" label="READ FAILED" />{" "}
            <span className="surface-token" data-chip>{readError.toUpperCase()}</span>{" "}
            <Button variant="secondary" dense onClick={() => void reload()}>Retry</Button>
          </span>
        </GadgetRow>
      ) : null}
      {access ? (<>
      <GadgetRow label="Agent access" wide controlWidth="full" highlight={highlight === "people.access"}>
        <span data-testid="people-access">
          <FilterTokens
            label="Agent access"
            value={held ? access.effective : access.mode}
            options={MODES}
            disabled={held || busy}
            onChange={(mode) => void press(mode)}
          />
        </span>
      </GadgetRow>
      <GadgetRow label="Agents you start">
        <span className="prefs-value" data-testid="people-access-agents">
          {access.agents === "off" ? "Off" : "Read"}
        </span>
      </GadgetRow>
      {held ? <GadgetRow label="Access source"><span data-testid="people-access-source">Set by environment</span><FoldGadget title="Details"><code>{access.env_var || "HOLDSPEAK_MCP_PEOPLE_ACCESS"}</code></FoldGadget></GadgetRow> : null}
      </>) : null}
      {receipt ? (
        <GadgetRow label="Receipt">
          <span
            data-testid="people-access-receipt"
            data-outcome={receipt.ok ? "succeeded" : "refused"}
            data-operation-id={receipt.operationId}
          >
            {receipt.ok
              ? <StateChip state="success" label={`Saved · ${MODES.find((m) => m.value === receipt.mode)?.label ?? "Access"}`} />
              : <StateChip state="failure" label={`Not saved · ${receipt.code === "people_access_env_override" ? "Set by environment" : "Access could not change"}`} />}
          </span>
        </GadgetRow>
      ) : null}
    </GadgetGroup>
  );
}

/** The Settings hub row's cell (the row is in settingsPrefs). PHILO-17 U35:
 *  one plain fact (was MCP · <effective> · AGENTS · <mode>). */
export function PeopleHubCells() {
  const { access } = usePeopleAccess();
  if (!access) return null;
  // `agents` is what a started agent gets: read unless access is off.
  const text = access.agents === "off" ? "Agents: off" : "Agents can read People";
  return <span className="surface-token" data-chip data-testid="people-hub-access">{text}</span>;
}
