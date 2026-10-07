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
import { FilterTokens, GadgetGroup, GadgetRow, StateChip } from "../../desk/surface";

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

export function usePeopleAccess() {
  const [access, setAccess] = useState<PeopleAccess | null>(null);
  const reload = useCallback(async () => {
    try {
      setAccess(await apiFetch<PeopleAccess>("/api/settings/people-access"));
    } catch {
      setAccess(null);
    }
  }, []);
  useEffect(() => { void reload(); }, [reload]);
  return { access, setAccess, reload };
}

export function PeopleAccessModule() {
  const { access, setAccess, reload } = usePeopleAccess();
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

  if (!access) return null;
  const held = access.source === "env";
  return (
    <GadgetGroup label="MCP access">
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
