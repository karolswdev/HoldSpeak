/** Betterment A4 — the With editor (DESIGN §4, RECIPE A4).
 *
 * The minimal engine picker until Engines E5 lands: his engines, then what
 * this Mac (and, on a press, the network) has that the library does not
 * (Found), each with one verb. Use writes this automation's engine (the
 * subject assignment `subject:workbench:<id>:capability:workbench.item`; the
 * hub re-freezes a live schedule). Add puts a found engine in the library
 * (the Engines app's own paths: `connect_cli_engine` for an agent CLI,
 * define-endpoint for a server) and uses it, in one press. Every row says
 * where its prompt goes. Under the engine in use: the optional Spend limit
 * per run for this automation, when that engine can stop at a limit. */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { EgressChip, StringGadget } from "../../surface";
import { defineEndpoint } from "../../../features/concierge/api";
import { endpointDraft, endpointProfileId } from "../../../features/concierge/endpointDraft";
import { connectCliEngine, discoverLan, readDetection, type RunsOnEngine } from "../../../features/runson/api";
import { buildEngines, enginePlace, hostLabel, usd, type BoardEngine } from "../../../features/runson/model";
import type { AutomationDetail } from "./model";

export interface NativeAgentOption {
  profileId: string;
  agentId: string;
  label: string;
  executable: string;
  installed: boolean;
  ready: boolean;
}

interface NativeProfilesWire {
  profiles?: Array<{ profile_id?: string; label?: string; executable?: string }>;
}

interface NativeAgentsWire {
  agents?: Array<{ id?: string; label?: string; installed?: boolean; ready?: boolean }>;
  tmux?: { installed?: boolean };
}

/** The existing native profile and onboarding producers, joined by executable. */
export async function readNativeAgentOptions(): Promise<NativeAgentOption[]> {
  const [profileWire, agentWire] = await Promise.all([
    apiFetch<NativeProfilesWire>("/api/delivery/factory/profiles"),
    apiFetch<NativeAgentsWire>("/api/onboarding/agents"),
  ]);
  const agents = Array.isArray(agentWire.agents) ? agentWire.agents : [];
  const tmuxReady = agentWire.tmux?.installed === true;
  return (Array.isArray(profileWire.profiles) ? profileWire.profiles : [])
    .map((profile) => {
      const executable = String(profile.executable ?? "");
      const found = agents.find((agent) => String(agent.id ?? "") === executable);
      if (!found || found.installed !== true) return null;
      return {
        profileId: String(profile.profile_id ?? ""),
        agentId: executable,
        label: String(profile.label ?? found.label ?? executable),
        executable,
        installed: true,
        ready: found.ready === true && tmuxReady,
      };
    })
    .filter((option): option is NativeAgentOption => Boolean(option?.profileId));
}

/** Where an engine's prompt goes, for its chip. */
function placeOf(engine: BoardEngine): { label: string; scope: "local" | "cloud" } {
  if (engine.vendor) return { label: engine.vendor, scope: "cloud" };
  const place = enginePlace(engine);
  return { label: hostLabel(engine), scope: place.place === "mac" || place.place === "lan" ? "local" : "cloud" };
}

/** The profile id a found engine gets when it is added (the Engines paths). */
function addedId(engine: BoardEngine): string {
  if (engine.agentPreset) return `agent-${engine.agentPreset}`;
  return endpointProfileId(engine.baseUrl ?? "", engine.model || engine.name);
}

/** The id an assignment names for a library engine. A v1 endpoint has no
 *  profile revision: the assignment calls it `legacy-<id>`. */
function assignedId(engine: BoardEngine): string {
  const id = engine.profileId ?? "";
  if (!id || engine.profileRevision || id.startsWith("legacy-")) return id;
  return `legacy-${id}`;
}

function usable(engine: BoardEngine): boolean {
  if (engine.kind === "preset") return false; // a download is the Engines app's job
  if (engine.found) return Boolean(engine.agentPreset || engine.baseUrl);
  return Boolean(engine.profileId);
}

export function WithEditor(props: {
  detail: AutomationDetail;
  onUse: (profileId: string) => Promise<void>;
  onSpendLimit: (limit: number | null) => Promise<void>;
  onPending?: (pending: Promise<unknown>) => void;
  handMode?: boolean;
}) {
  if (props.handMode) return <NativeWithEditor detail={props.detail} onUse={props.onUse} />;
  return <InferenceWithEditor detail={props.detail} onUse={props.onUse}
    onSpendLimit={props.onSpendLimit} onPending={props.onPending} />;
}

function NativeWithEditor({
  detail,
  onUse,
}: {
  detail: AutomationDetail;
  onUse: (profileId: string) => Promise<void>;
}) {
  const [nativeAgents, setNativeAgents] = useState<NativeAgentOption[] | null>(null);
  const [nativeError, setNativeError] = useState<string | null>(null);
  const [nativeBusy, setNativeBusy] = useState<string | null>(null);
  const readNative = useCallback(async () => {
    try {
      setNativeAgents(await readNativeAgentOptions());
      setNativeError(null);
    } catch (error) {
      setNativeError(readableError(error));
    }
  }, []);
  useEffect(() => { void readNative(); }, [readNative]);
  return (
    <NativeAgentEditor detail={detail} agents={nativeAgents} error={nativeError}
      busy={nativeBusy} onRetry={() => void readNative()}
      onUse={async (profileId) => {
        setNativeBusy(profileId);
        setNativeError(null);
        try {
          await onUse(profileId);
          await readNative();
        } catch (error) {
          setNativeError(readableError(error));
        } finally {
          setNativeBusy(null);
        }
      }} />
  );
}

function InferenceWithEditor({
  detail,
  onUse,
  onSpendLimit,
  onPending,
}: {
  detail: AutomationDetail;
  /** Use this engine for the automation (the hub writes and re-freezes). */
  onUse: (profileId: string) => Promise<void>;
  onSpendLimit: (limit: number | null) => Promise<void>;
  /** Betterment A6: an Add or Use press in flight (Run now waits for it). */
  onPending?: (pending: Promise<unknown>) => void;
}) {
  const [found, setFound] = useState<RunsOnEngine[]>([]);
  const [engines, setEngines] = useState<BoardEngine[] | null>(null);
  const [readError, setReadError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [refusal, setRefusal] = useState<string | null>(null);
  const [looking, setLooking] = useState(false);
  const [looked, setLooked] = useState(false);
  const mounted = useRef(true);
  useEffect(() => () => { mounted.current = false; }, []);

  const read = useCallback(async () => {
    try {
      const detection = await readDetection();
      if (!mounted.current) return;
      setEngines(buildEngines(null, detection));
      setReadError(null);
    } catch (error) {
      if (mounted.current) setReadError(readableError(error));
    }
  }, []);
  useEffect(() => { void read(); }, [read]);

  const inUse = detail.assignment_summary?.profile_id ?? null;
  const all = useMemo(() => {
    const lan = buildEngines(null, { engines: found, hardware: {}, checkedAt: "", repairs: [], summaryAssignment: null });
    const seen = new Set((engines ?? []).map((e) => e.baseUrl).filter(Boolean));
    return [...(engines ?? []), ...lan.filter((e) => !e.baseUrl || !seen.has(e.baseUrl))].filter(usable);
  }, [engines, found]);
  const mine = all.filter((e) => !e.found);
  const foundRows = all.filter((e) => e.found);
  const current = mine.find((e) => assignedId(e) === inUse) ?? null;

  const press = (engine: BoardEngine) => {
    const pending = save(engine);
    onPending?.(pending);
    return pending;
  };

  const save = async (engine: BoardEngine) => {
    setBusy(engine.key);
    setRefusal(null);
    try {
      let profileId = assignedId(engine);
      if (engine.found) {
        profileId = addedId(engine);
        if (engine.agentPreset) {
          await connectCliEngine({ preset: engine.agentPreset, profileId, expectedProfileRevision: 0 });
        } else {
          await defineEndpoint(endpointDraft({
            url: engine.baseUrl ?? "",
            model: engine.model || engine.name,
            requestId: `automation-add-${Date.now()}`,
            expectedProfileRevision: 0,
          }));
        }
      }
      await onUse(profileId);
      await read();
    } catch (error) {
      if (mounted.current) setRefusal(readableError(error));
    } finally {
      if (mounted.current) setBusy(null);
    }
  };

  const lookOnNetwork = async () => {
    setLooking(true);
    try {
      const answer = await discoverLan();
      if (mounted.current) setFound(answer.engines.map((e) => ({ ...e, found: e.found || !e.profileId })));
    } catch (error) {
      if (mounted.current) setRefusal(readableError(error));
    } finally {
      if (mounted.current) { setLooking(false); setLooked(true); }
    }
  };

  const row = (engine: BoardEngine) => {
    const place = placeOf(engine);
    const using = !engine.found && assignedId(engine) === inUse;
    return (
      <li key={engine.key} className="automation-engine" data-testid="automation-engine"
        data-in-use={using || undefined}>
        <span className="automation-engine-name">{engine.name}</span>
        <EgressChip label={place.label} scope={place.scope} title={`The prompt goes to ${place.label}`} />
        {using ? (
          <span className="automation-engine-using">In use</span>
        ) : (
          <Button dense variant={engine.found ? "secondary" : "ghost"} loading={busy === engine.key}
            disabled={Boolean(busy) && busy !== engine.key}
            aria-label={`${engine.found ? "Add" : "Use"} ${engine.name}`}
            onClick={() => void press(engine)}>
            {engine.found ? "Add" : "Use"}
          </Button>
        )}
      </li>
    );
  };

  return (
    <div className="automation-with-editor" data-testid="automation-with-editor">
      {readError ? (
        <div className="automation-failure">
          <p className="automation-failure-words">{readError}</p>
          <Button dense variant="ghost" onClick={() => void read()}>Try again</Button>
        </div>
      ) : null}
      {mine.length ? (
        <section aria-label="My engines">
          <span className="automation-editor-head">My engines</span>
          <ul className="automation-engine-list">{mine.map(row)}</ul>
        </section>
      ) : null}
      {current ? <SpendLimit engine={current} detail={detail} onSave={onSpendLimit} /> : null}
      <section aria-label="Found">
        {foundRows.length ? (
          <>
            <span className="automation-editor-head">Found</span>
            <ul className="automation-engine-list">{foundRows.map(row)}</ul>
          </>
        ) : null}
        <div className="automation-editor-verbs">
          <Button dense variant="ghost" loading={looking} onClick={() => void lookOnNetwork()}>
            {looked ? "Look on my network again" : "Look on my network"}
          </Button>
        </div>
      </section>
      {engines && !all.length && looked ? (
        <p className="automation-quiet">No engine found. The Engines app can download one.</p>
      ) : null}
      {refusal ? <p className="automation-refusal" role="alert">{refusal}</p> : null}
    </div>
  );
}

function NativeAgentEditor({
  detail,
  agents,
  error,
  busy,
  onRetry,
  onUse,
}: {
  detail: AutomationDetail;
  agents: NativeAgentOption[] | null;
  error: string | null;
  busy: string | null;
  onRetry: () => void;
  onUse: (profileId: string) => Promise<void>;
}) {
  return (
    <div className="automation-with-editor" data-testid="automation-native-with-editor">
      {error ? (
        <div className="automation-failure">
          <p className="automation-failure-words">{error}</p>
          <Button dense variant="ghost" onClick={onRetry}>Try again</Button>
        </div>
      ) : null}
      {agents?.length ? (
        <section aria-label="Installed native agents">
          <span className="automation-editor-head">Installed native agents</span>
          <ul className="automation-engine-list">
            {agents.map((agent) => {
              const using = detail.agent_profile === agent.profileId;
              const place = agent.agentId === "pi"
                ? { label: "This Mac", scope: "local" as const }
                : { label: agent.agentId === "claude" ? "Anthropic" : "OpenAI", scope: "cloud" as const };
              return (
                <li key={agent.profileId} className="automation-engine" data-testid="automation-native-agent"
                  data-in-use={using || undefined}>
                  <span className="automation-engine-name">{agent.label}</span>
                  <EgressChip label={place.label} scope={place.scope} title={`The hand goes to ${place.label}`} />
                  {using ? <span className="automation-engine-using">In use</span> : (
                    <Button dense variant="ghost" loading={busy === agent.profileId}
                      disabled={Boolean(busy) || !agent.ready}
                      aria-label={`Use ${agent.label}`} onClick={() => void onUse(agent.profileId)}>
                      {agent.ready ? "Use" : "Needs attention"}
                    </Button>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      ) : agents ? (
        <p className="automation-quiet">No installed native agent is ready.</p>
      ) : null}
    </div>
  );
}

/** The automation's own Spend limit per run, for an engine that stops at
 *  one (Claude Code). Empty = the engine's own limit. */
function SpendLimit({
  engine,
  detail,
  onSave,
}: {
  engine: BoardEngine;
  detail: AutomationDetail;
  onSave: (limit: number | null) => Promise<void>;
}) {
  const own = detail.spend_limit_usd ?? null;
  const [draft, setDraft] = useState(own != null ? own.toFixed(2) : "");
  const [invalid, setInvalid] = useState(false);
  const [refusal, setRefusal] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  if (!engine.spend?.canLimit) return null;
  const engineLimit = engine.spend.limitUsd;
  const save = async (clear = false) => {
    setRefusal(null);
    const text = clear ? "" : draft.trim().replace(/^\$/, "");
    const limit = text ? Number(text) : null;
    if (limit != null && !(Number.isFinite(limit) && limit > 0 && limit <= 1000)) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    setSaving(true);
    try {
      await onSave(limit);
      if (clear) setDraft("");
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setSaving(false);
    }
  };
  return (
    <section className="automation-spend" aria-label="Spend limit per run" data-testid="automation-spend">
      <StringGadget
        label="Spend limit per run"
        caption
        value={draft}
        onChange={(next) => { setDraft(next); setInvalid(false); }}
        placeholder={engineLimit != null ? `${usd(engineLimit)} (the engine's)` : "No limit"}
      />
      <div className="automation-editor-verbs">
        <Button dense variant="secondary" loading={saving}
          disabled={!draft.trim() || draft.trim() === (own != null ? own.toFixed(2) : "")}
          onClick={() => void save()}>
          Save limit
        </Button>
        {own != null ? (
          <Button dense variant="ghost" onClick={() => void save(true)}>Use the engine's limit</Button>
        ) : null}
      </div>
      {invalid ? <p className="automation-refusal" role="alert">Type an amount above $0 and at most $1000.</p> : null}
      {refusal ? <p className="automation-refusal" role="alert">{refusal}</p> : null}
    </section>
  );
}
