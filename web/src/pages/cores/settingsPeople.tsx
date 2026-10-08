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
import { FilterTokens, GadgetGroup, GadgetRow, StateChip, StringGadget } from "../../desk/surface";
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

const MODES = [
  { value: "off", label: "OFF" },
  { value: "read", label: "READ" },
  { value: "write", label: "WRITE" },
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
export function OwnerNameGroup() {
  const owner = useOwnerName();
  return (
    <GadgetGroup label="You">
      <GadgetRow label="Your name">
        <span data-testid="settings-owner-name">
          <StringGadget
            label="Your name"
            value={owner.name}
            onChange={owner.setName}
            placeholder="Name"
            inputProps={{ onBlur: () => void owner.flush() }}
          />
        </span>
      </GadgetRow>
      <GadgetRow label="Also called">
        <span data-testid="settings-owner-aliases">
          <OwnerAliasField owner={owner} />
        </span>
      </GadgetRow>
      {owner.error ? (
        <GadgetRow label="Receipt">
          <StateChip state="failure" label="NOT SAVED" />
        </GadgetRow>
      ) : null}
    </GadgetGroup>
  );
}

export function PeopleAccessModule() {
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
    <GadgetGroup label="MCP access">
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
      <GadgetRow label="Access">
        <span data-testid="people-access">
          <FilterTokens
            label="People MCP access"
            value={held ? access.effective : access.mode}
            options={MODES}
            disabled={held || busy}
            onChange={(mode) => void press(mode)}
          />
        </span>
      </GadgetRow>
      <GadgetRow label="Agents">
        <span className="surface-token" data-chip data-testid="people-access-agents">
          {`AGENTS · ${access.agents.toUpperCase()}`}
        </span>
        <span className="surface-token" data-chip data-muted data-wrap data-testid="people-access-source">
          {sourceToken(access)}
        </span>
      </GadgetRow>
      </>) : null}
      {receipt ? (
        <GadgetRow label="Receipt">
          <span
            data-testid="people-access-receipt"
            data-outcome={receipt.ok ? "succeeded" : "refused"}
            data-operation-id={receipt.operationId}
          >
            {receipt.ok
              ? <StateChip state="success" label="SUCCEEDED" />
              : <StateChip state="failure" label="REFUSED" />}{" "}
            <span className="surface-token" data-chip>{`ACCESS · ${receipt.mode.toUpperCase()}`}</span>{" "}
            {!receipt.ok && receipt.code ? (
              <span className="surface-token" data-chip>{receipt.code.toUpperCase()}</span>
            ) : null}{" "}
            <span className="surface-token" data-chip>BY OWNER</span>{" "}
            <span className="surface-token" data-chip data-muted>{receipt.at}</span>
          </span>
        </GadgetRow>
      ) : null}
    </GadgetGroup>
  );
}

/** The Settings hub row's cells: MCP · <effective> · AGENTS · <mode> (the row is in settingsPrefs). */
export function PeopleHubCells() {
  const { access } = usePeopleAccess();
  if (!access) return null;
  return (
    <>
      <span className="surface-token" data-chip>{`MCP · ${access.effective.toUpperCase()}`}</span>
      <span className="surface-token" data-chip>{`AGENTS · ${access.agents.toUpperCase()}`}</span>
    </>
  );
}
