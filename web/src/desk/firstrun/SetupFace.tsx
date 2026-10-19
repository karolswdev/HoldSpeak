import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { openIntelligence } from "../intelligenceNavigation";
import { closeFirstRun } from "./reopen";
import { useFirstTake } from "./useFirstTake";
import { EgressChip, FoldGadget, StateChip, StringGadget, SurfaceRow, SurfaceRows, SurfaceSection } from "../surface";
import "./setupFace.css";
import { useOwnerName } from "./ownerName";

export type SetupRowState = "found" | "pending" | "works" | "does_not_work";

export interface SetupRow {
  id: string;
  kind: string;
  label: string;
  detail?: string;
  state: SetupRowState;
  reason?: string;
  egress_host?: string | null;
  verb?: string | null;
  action?: string | null;
  payload?: Record<string, unknown>;
}

export interface SetupInventory {
  rows: SetupRow[];
  owner_name?: string;
  people?: { id: string; display_name: string; relationship_kind?: string }[];
  suggestions?: { key: string; name: string; relationship_kind?: string; one_on_one?: boolean }[];
  first_run?: boolean;
}

export function useSetupInventory(): {
  loading: boolean;
  inventory: SetupInventory | null;
  error: string;
  reload: () => Promise<void>;
} {
  const [loading, setLoading] = useState(true);
  const [inventory, setInventory] = useState<SetupInventory | null>(null);
  const [error, setError] = useState("");
  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const answer = await apiFetch<SetupInventory>("/api/setup/found");
      if (!answer || !Array.isArray(answer.rows)) {
        throw new Error("Setup returned no inventory.");
      }
      setInventory(answer);
    } catch (cause) {
      setError(readableError(cause));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void reload();
  }, [reload]);
  return { loading, inventory, error, reload };
}

function stateNode(row: SetupRow) {
  if (row.state === "works") return <StateChip state="success" label="Works" icon="●" />;
  if (row.state === "does_not_work") return <StateChip state="failure" label="Does not work" />;
  if (row.state === "pending") return <StateChip state="idle" label="Working" />;
  return <StateChip state="idle" label="Found" />;
}

function SetupInventoryRow({ row, busy, onUse }: { row: SetupRow; busy: boolean; onUse: () => void }) {
  return (
    <SurfaceRow
      glyph={<span aria-hidden="true">{row.kind === "speech" ? "◖" : row.kind === "calendar" ? "▦" : row.kind === "account" ? "⑂" : row.kind === "agents" ? "◉" : "◆"}</span>}
      title={row.label}
      detail={row.reason ? `${row.detail || ""}${row.detail ? " · " : ""}${row.reason}` : row.detail || undefined}
      meta={
        <span className="setup-face-row-meta">
          {row.egress_host ? <EgressChip label={row.egress_host} scope={row.egress_host.includes(".") ? "remote" : "local"} /> : null}
          {stateNode(row)}
        </span>
      }
      verbs={row.action && row.state !== "works" ? (
        <Button dense variant="secondary" loading={busy} disabled={busy} onClick={onUse}>
          {row.verb || "Use"}
        </Button>
      ) : undefined}
    />
  );
}

type SetupActionState = "works" | "pending" | "does_not_work" | "found";

function actionAnswer(answer: unknown): { state: SetupActionState; reason?: string } {
  const body = answer && typeof answer === "object" ? answer as Record<string, any> : {};
  const result = body.result && typeof body.result === "object" ? body.result as Record<string, any> : body;
  const entry = result.entry && typeof result.entry === "object" ? result.entry as Record<string, any> : {};
  const connection = Array.isArray(entry.connections) ? entry.connections.find((item) => item && typeof item === "object") : null;
  const state = String(result.state || result.status || entry.state || connection?.state || "").toLowerCase();
  const reason = String(
    result.error_detail || result.error || result.message || result.reason || entry.error_detail || connection?.error_detail || "",
  ).trim();
  const hasError = Boolean(
    result.error_code || result.error || result.error_detail || result.failure ||
    entry.error_detail || connection?.error_detail || result.ok === false,
  );
  if (body.success === false || result.success === false || hasError || state === "failed" || state === "degraded" || state === "error" || state === "incomplete" || state === "needs_runtime" || state === "owner_action_required") {
    return { state: "does_not_work", reason: reason || "The setup action did not work." };
  }
  if (["downloading", "pending", "working", "running", "queued", "in_progress", "indexing"].includes(state)) {
    return { state: "pending", reason: reason || "Still working." };
  }
  if (["ready", "connected", "available", "active", "enabled", "installed", "works", "success", "succeeded"].includes(state) || result.ok === true) {
    return { state: "works" };
  }
  return { state: "found", reason: "Not checked. Try again." };
}

function mergeInventory(current: SetupInventory, latest: SetupInventory): SetupInventory {
  const latestIds = new Set(latest.rows.map((row) => row.id));
  const lanRows = current.rows.filter((row) => row.id.startsWith("lan:") && !latestIds.has(row.id));
  return { ...current, ...latest, rows: [...latest.rows, ...lanRows] };
}

export function SetupFace({ initial }: { initial: SetupInventory }) {
  const [inventory, setInventory] = useState(initial);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [peopleDraft, setPeopleDraft] = useState("");
  const [peopleBusy, setPeopleBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const owner = useOwnerName();

  const handoff = useCallback(async (disposition: "completed" | "dismissed") => {
    await apiFetch("/api/desk/seed", { method: "POST" });
    await apiFetch("/api/setup/onboarding", { method: "PUT", json: { disposition } });
    closeFirstRun();
  }, []);
  const take = useFirstTake({ onHandoff: handoff });

  // ST4: the scan is a separate owner approved operation. The shared found
  // read above never asks the network.
  useEffect(() => {
    let live = true;
    void apiFetch<{ rows?: Record<string, unknown>[] }>("/api/setup/lan", { method: "POST" })
      .then((answer) => {
        if (!live || !Array.isArray(answer.rows)) return;
        const lanRows: SetupRow[] = answer.rows.map((raw) => ({
          id: `lan:${String(raw.id || raw.name || "engine")}`,
          kind: "engine",
          label: String(raw.name || raw.model || "Network engine"),
          detail: `${String(raw.host || "")} · YOUR NETWORK`,
          state: "found",
          egress_host: "YOUR NETWORK",
          verb: "Use",
          action: "lan",
          payload: { base_url: raw.baseUrl || raw.base_url, model: raw.name || raw.model },
        }));
        setInventory((current) => {
          const existing = new Set(current.rows.map((row) => row.id));
          return { ...current, rows: [...current.rows, ...lanRows.filter((row) => !existing.has(row.id))] };
        });
      })
      .catch(() => undefined);
    return () => { live = false; };
  }, []);

  const actionable = useMemo(() => inventory.rows.filter((row) => row.action && row.state === "found"), [inventory.rows]);
  const working = inventory.rows.filter((row) => row.state === "works");
  const found = inventory.rows.filter((row) => row.kind !== "owner" && (row.state === "found" || row.state === "pending"));
  const notFound = inventory.rows.filter((row) => row.kind !== "owner" && row.state === "does_not_work");

  const refreshPending = useCallback(async (rowId: string) => {
    for (let attempt = 0; attempt < 20; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 750));
      try {
        const latest = await apiFetch<SetupInventory>("/api/setup/found");
        if (!Array.isArray(latest.rows)) continue;
        const next = latest.rows.find((row) => row.id === rowId);
        setInventory((current) => mergeInventory(current, latest));
        if (!next || next.state === "works" || next.state === "does_not_work") return;
      } catch {
        // Keep the honest Working state until a later read succeeds.
      }
    }
    setInventory((current) => ({
      ...current,
      rows: current.rows.map((row) => row.id === rowId && row.state === "pending"
        ? { ...row, state: "found", reason: "Still working. Check again." }
        : row),
    }));
  }, []);

  const useRow = useCallback(async (row: SetupRow) => {
    if (!row.action) return;
    setBusyId(row.id);
    setNotice("");
    try {
      let answer: unknown = {};
      if (row.action === "agents") {
        for (const agent of (row.payload?.agents as string[] | undefined) ?? []) {
          answer = await apiFetch("/api/onboarding/agents/use", { method: "POST", json: { agent } });
        }
      } else {
        answer = await apiFetch("/api/setup/use", {
          method: "POST",
          json: { id: row.id, payload: { ...(row.payload || {}) } },
        });
      }
      const outcome = actionAnswer(answer);
      setInventory((current) => ({
        ...current,
        rows: current.rows.map((candidate) => candidate.id === row.id
          ? {
            ...candidate,
            state: outcome.state,
            reason: outcome.reason || "",
            action: outcome.state === "works" ? null : candidate.action,
            verb: outcome.state === "works" ? null : candidate.verb,
          }
          : candidate),
      }));
      if (outcome.state === "pending") void refreshPending(row.id);
    } catch (error) {
      setInventory((current) => ({
        ...current,
        rows: current.rows.map((candidate) => candidate.id === row.id
          ? { ...candidate, state: "does_not_work", reason: readableError(error) }
          : candidate),
      }));
    } finally {
      setBusyId(null);
    }
  }, [refreshPending]);

  const useEverything = useCallback(async () => {
    for (const row of actionable) await useRow(row);
  }, [actionable, useRow]);

  const addPeople = async () => {
    if (!peopleDraft.trim()) return;
    setPeopleBusy(true);
    setNotice("");
    try {
      const result = await apiFetch<{ relationships?: SetupInventory["people"] }>("/api/setup/people", {
        method: "POST", json: { names: peopleDraft },
      });
      setInventory((current) => ({ ...current, people: [...(current.people || []), ...(result.relationships || [])] }));
      setPeopleDraft("");
      setNotice("People added.");
    } catch (error) {
      setNotice(readableError(error));
    } finally {
      setPeopleBusy(false);
    }
  };

  const openDesk = () => void take.finish(() => {
    closeFirstRun();
    openIntelligence({ view: "today" });
  });
  const ownerName = owner.name || inventory.owner_name || "";
  // Optional accounts and agents can remain absent without trapping the owner.
  // Speech and the owner's name are the two facts required for the first sentence.
  const speechReady = inventory.rows.some((row) => row.id === "speech" && row.state === "works");
  const ready = speechReady && Boolean(ownerName);
  const sayOneSentence = () => {
    if (take.state === "heard" && !take.kept) return void take.keep();
    if (take.state === "idle" || take.state === "failed") void take.begin();
  };

  return (
    <section className="setup-face" aria-label="Set up HoldSpeak" data-testid="setup-face">
      <header className="setup-face-head">
        <div>
          <h1>Set up HoldSpeak</h1>
          {ready ? <p className="setup-face-ready">Ready, {ownerName}.</p> : null}
        </div>
        {actionable.length ? <Button variant="primary" dense onClick={() => void useEverything()}>Use everything found</Button> : null}
      </header>
      {found.length ? (
        <SurfaceSection label="Found on this Mac" data-testid="setup-found">
          <SurfaceRows>
            {found.map((row) => <SetupInventoryRow key={row.id} row={row} busy={busyId === row.id} onUse={() => void useRow(row)} />)}
          </SurfaceRows>
        </SurfaceSection>
      ) : null}
      {inventory.people?.length || inventory.suggestions?.length || inventory.owner_name !== undefined ? (
        <SurfaceSection label="You and your people" data-testid="setup-people">
          <SurfaceRows>
            <SurfaceRow
              title="Your name"
              detail={owner.readError || (ownerName ? ownerName : "Add your name here")}
              meta={<StateChip state={ownerName ? "success" : "idle"} label={ownerName ? "Works" : "Found"} />}
            >
              <div className="setup-face-owner-input">
                <StringGadget label="Your name" value={owner.name} onChange={owner.setName} placeholder="Your name" inputProps={{ onBlur: () => void owner.flush() }} />
              </div>
            </SurfaceRow>
            <SurfaceRow
              title="Your people"
              detail={(inventory.people || []).map((person) => person.display_name).join(", ") || "Add direct reports separated by commas"}
              verbs={<Button dense variant="secondary" loading={peopleBusy} disabled={peopleBusy || !peopleDraft.trim()} onClick={() => void addPeople()}>Add</Button>}
            >
              <div className="setup-face-people-input">
                <StringGadget label="Your people" value={peopleDraft} onChange={setPeopleDraft} placeholder="Mira Okafor, Theo Lindqvist" />
                {inventory.suggestions?.length ? <small>From your calendar: {inventory.suggestions.map((suggestion) => suggestion.name).join(", ")}</small> : null}
              </div>
            </SurfaceRow>
          </SurfaceRows>
        </SurfaceSection>
      ) : null}
      {notFound.length ? (
        <FoldGadget title="Not found" token={String(notFound.length)}>
          <SurfaceRows>{notFound.map((row) => <SetupInventoryRow key={row.id} row={row} busy={busyId === row.id} onUse={() => void useRow(row)} />)}</SurfaceRows>
        </FoldGadget>
      ) : null}
      {working.length ? (
        <FoldGadget title="Works" token={String(working.length)}>
          <SurfaceRows>{working.map((row) => <SetupInventoryRow key={row.id} row={row} busy={false} onUse={() => undefined} />)}</SurfaceRows>
        </FoldGadget>
      ) : null}
      {notice ? <p className="setup-face-notice" role="status">{notice}</p> : null}
      {take.message ? <p className="setup-face-notice" role="alert">{take.message}</p> : null}
      <div className="setup-face-foot">
        {!ready ? (
          <Button dense variant="primary" loading={take.keeping} disabled={take.keeping} onClick={openDesk}>
            Open my desk
          </Button>
        ) : null}
      </div>
      {ready ? (
        <div className="setup-face-finale">
          <Button dense variant="secondary" disabled={take.state === "listening" || take.state === "writing"} onClick={sayOneSentence}>
            {take.state === "heard" && !take.kept ? "Keep as note" : take.state === "listening" ? "Listening" : "Say one sentence"}
          </Button>
          {take.take ? <span className="setup-face-take" role="status">{take.take.text}</span> : null}
          <Button dense variant="primary" loading={take.keeping} disabled={take.keeping} onClick={openDesk}>Open my desk</Button>
        </div>
      ) : null}
    </section>
  );
}
