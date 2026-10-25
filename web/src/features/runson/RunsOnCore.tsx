// PHILO-16 (C) — Runs on: the Models window as a Switchboard.
//
// COMPOSITOR.md §12 "The exemplar: Runs on", canvas Board 2. Composed from
// the kit: the AppHead (the one fact `M engines` with its status
// strip), the Switchboard (the app's one species), and the Foot (the
// receipt `PATCHED <time> · <job> → <engine>`, the egress chip of the last
// engine used, Undo). A change applies on the drop; there is no Save.

import { useContext, useEffect, useMemo, useRef, type ReactNode } from "react";
import {
  CheckGadget,
  EgressChip,
  FoldGadget,
  StateChip,
  StringGadget,
  SurfaceWell,
  SurfaceSwitchboard,
  useSwitchboardLayout,
  wireDate,
  type SwitchEngine,
  type SwitchJob,
  type SwitchLamp,
  type SwitchWire,
} from "../../desk/surface";
import { TitleSlotContext } from "../../desk/surface/title";
import { StatusBar, ToolGlyph, Toolbar, type StatusBarItem } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { Button } from "../../components/signal/Signal";
import type { CoreProps } from "../../pages/cores/core-types";
import { endpointHostPort, isLanAddress } from "../concierge/endpointDraft";
import { MeaningSearchRow } from "../concierge/MeaningSearchRow";
import {
  DEFAULT_JOB,
  JOB_ORDER,
  JOB_PROBE_CAPABILITIES,
  MEETINGS_JOB,
  SPEECH_JOB,
  agentChip,
  costTokens,
  enginePlace,
  foundAgentName,
  hostLabel,
  jobName,
  jobState,
  jobOf,
  leadEngine,
  leadLine,
  limitTokens,
  ownEntries,
  splitEngines,
  taskDetail,
  taskLine,
  type BoardEngine,
} from "./model";
import { stateClass, stateWord } from "./stateWord";
import { useRunsOn, type AddKind, type RunsOnController } from "./useRunsOn";
import type { ServicePreset, ServiceTile } from "./api";
import { SpeechSetup, useSpeechSetup } from "../../desk/firstrun/SpeechSetup";
import { useBuilderTools } from "../../desk/builderTools";
import { WhatRunsWhere } from "./WhatRunsWhere";
// The Meaning search row draws with the Concierge's ledger cells.
import "../concierge/concierge.css";
import "./runson.css";

function lampFor(engine: BoardEngine, busy: boolean): SwitchLamp {
  if (busy) return "busy";
  if (engine.kind === "preset") return "warn";
  const word = stateWord(engine.state);
  if (word === "READY") return "ok";
  if (word === "BROKEN") return "broken";
  if (word === "OFF") return "off";
  return engine.state === "unknown" ? "off" : "warn";
}

function hardwareToken(det: RunsOnController["detection"]): string | null {
  const cap = det?.hardware?.capability;
  if (!cap) return null;
  const parts = ["This Mac"];
  if (cap.apple_silicon) parts.push("M‑series");
  const gb = cap.ram_gb ?? (cap.total_memory_bytes ? Math.round(cap.total_memory_bytes / 1024 ** 3) : null);
  if (gb) parts.push(`${gb} GB`);
  return parts.join(" · ");
}

function AddEngineRow({ ctrl, service }: { ctrl: RunsOnController; service?: ServiceTile }) {
  const a = ctrl.add;
  const host = endpointHostPort(a.url).toUpperCase();
  return (
    <div className="runson-add" data-testid="concierge-add-engine-row">
      {service ? null : (
        <StringGadget
          label="Server address"
          caption
          value={a.url}
          onChange={a.setUrl}
          placeholder="http://<host>:<port>/v1"
          autoFocus
        />
      )}
      <span className="runson-add-key" data-testid="concierge-add-key">
        <StringGadget
          label={service ? `${service.name} key` : "Key"}
          caption
          type="password"
          mic={false}
          value={a.key}
          onChange={a.setKey}
          placeholder={service ? "Paste the key" : "optional"}
          autoFocus={Boolean(service)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && a.url.trim()) void a.check();
          }}
        />
      </span>
      {service ? null : (
        <span data-testid="concierge-add-my-server">
          <CheckGadget variant="token" label="MY SERVER" checked={a.mine} onChange={a.setMine} />
        </span>
      )}
      <span className="runson-add-verbs">
        {host ? (
          <span data-testid="concierge-add-egress">
            <EgressChip label={host} scope={isLanAddress(a.url) ? "local" : "cloud"} />
          </span>
        ) : null}
        <Button
          dense
          variant="ghost"
          onClick={() => void a.check()}
          disabled={!a.url.trim() || a.state === "CHECKING"}
          loading={a.state === "CHECKING"}
          data-testid="concierge-add-check"
        >
          Check
        </Button>
      </span>
      {a.state === "READY" ? (
        <>
          <span className="runson-add-answer">
            <StateChip state="success" label="READY" icon="●" />
            {a.tools ? (
              <span className="surface-token" data-testid="concierge-add-tools">
                {a.tools === "yes" ? "TOOLS" : a.tools === "no" ? "NO TOOLS" : "TOOLS UNKNOWN"}
              </span>
            ) : null}
          </span>
          <ModelPicker ctrl={ctrl} presets={service?.presets ?? []} />
        </>
      ) : null}
      {a.state === "KEY_REQUIRED" ? (
        <span className="runson-add-answer" role="alert" data-testid="concierge-add-key-answer">
          <StateChip state="failure" label="KEY REQUIRED" />
        </span>
      ) : null}
      {a.state === "KEY_INVALID" ? (
        <span className="runson-add-answer" role="alert" data-testid="concierge-add-key-answer">
          <StateChip state="failure" label="KEY INVALID" />
          <span className="surface-token">BAD CHARACTERS</span>
        </span>
      ) : null}
      {/* A.3: the answer is tokens (the word and the host), never the
          server's sentence. */}
      {a.state === "UNREACHABLE" ? (
        <span className="runson-add-answer" role="alert" data-testid="concierge-add-unreachable">
          <StateChip state="failure" label="UNREACHABLE" />
          <span className="surface-token" data-testid="concierge-add-reason">{host || "NO ADDRESS"}</span>
        </span>
      ) : null}
      {a.state === "NOT_ADDED" ? (
        <span className="runson-add-answer" role="alert">
          <StateChip state="failure" label="NOT ADDED" />
          <span className="surface-token" data-testid="concierge-add-reason">{a.reason}</span>
        </span>
      ) : null}
    </div>
  );
}

/** More models than this, and the picker has a search field. */
const PICKER_SEARCH_FROM = 7;

/** Betterment E3: Check fills this list; nothing is picked for him. Use on a
 *  row saves that model as its own engine; the list stays, so a second model
 *  on the same host is one more press. */
function ModelPicker({ ctrl, presets = [] }: { ctrl: RunsOnController; presets?: ServicePreset[] }) {
  const a = ctrl.add;
  const query = a.query.trim().toLowerCase();
  // Betterment E4: the catalog presets the service serves go on top, with
  // their short name; every other model follows in the server's order.
  const served = new Set(a.models);
  const top = presets.filter((preset) => served.has(preset.model));
  const named = new Map(top.map((preset) => [preset.model, preset.label.replace(/^.*·\s*/, "")]));
  const ordered = [...top.map((preset) => preset.model), ...a.models.filter((model) => !named.has(model))];
  const shown = query
    ? ordered.filter((m) => m.toLowerCase().includes(query) || (named.get(m) ?? "").toLowerCase().includes(query))
    : ordered;
  return (
    <div className="runson-picker" data-testid="concierge-add-picker">
      {a.models.length >= PICKER_SEARCH_FROM ? (
        <span data-testid="concierge-add-search">
          <StringGadget label="Find a model" caption value={a.query} onChange={a.setQuery} placeholder="Model name" />
        </span>
      ) : null}
      {shown.length ? (
        <ul className="runson-picker-list">
          {shown.map((model) => {
            const context = a.contexts[model];
            const used = a.used.includes(model);
            const preset = named.get(model);
            return (
              <li key={model} className="runson-picker-row" data-testid="concierge-add-pick" data-model={model} data-preset={preset ? "" : undefined}>
                {preset ? <span className="surface-token runson-picker-preset">{preset}</span> : null}
                <span className="surface-token runson-picker-model">{model}</span>
                {context ? <span className="surface-token">{context.toLocaleString("en-US")} TOKENS</span> : null}
                {used ? (
                  <StateChip state="success" label="ADDED" icon="●" />
                ) : (
                  <Button dense variant="primary" disabled={ctrl.busy} onClick={() => void a.save(model)} data-testid="concierge-add-use">
                    Use
                  </Button>
                )}
              </li>
            );
          })}
        </ul>
      ) : (
        <span className="surface-token" data-testid="concierge-add-no-match">NO MODEL MATCHES</span>
      )}
    </div>
  );
}

/** Betterment E2: an agent engine's row, unfolded: Spend limit per run (No
 *  limit, or an amount the CLI enforces) and today's and this week's
 *  reported cost. A CLI that cannot stop a run at a limit says so. */
function AgentSpend({ ctrl, engine }: { ctrl: RunsOnController; engine: BoardEngine }) {
  const a = ctrl.agent;
  const spend = engine.spend;
  const label = engine.model || engine.name;
  return (
    <span className="runson-agent-spend" data-testid={`runson-agent-spend-${engine.key}`}>
      {spend?.canLimit ? (
        <>
          <StringGadget
            label="Spend limit per run"
            caption
            value={a.draft}
            onChange={a.setDraft}
            placeholder="No limit"
            inputProps={{ inputMode: "decimal" }}
            onKeyDown={(event) => {
              if (event.key === "Enter") void a.save(engine.key);
            }}
          />
          <Button dense variant="primary" disabled={ctrl.busy} data-testid="runson-agent-spend-save" onClick={() => void a.save(engine.key)}>
            Save
          </Button>
          {spend.limitUsd != null ? (
            <Button dense variant="ghost" disabled={ctrl.busy} data-testid="runson-agent-spend-clear" onClick={() => void a.save(engine.key, true)}>
              No limit
            </Button>
          ) : null}
          {a.invalid ? (
            <span role="alert" data-testid="runson-agent-spend-invalid">
              <StateChip state="failure" label="MORE THAN $0, UP TO $1000" />
            </span>
          ) : null}
        </>
      ) : (
        <span className="surface-token" data-testid={`runson-agent-no-limit-${engine.key}`}>
          {`NO SPEND LIMIT IN ${label.toUpperCase()}`}
        </span>
      )}
      <span className="surface-token" data-testid={`runson-agent-cost-${engine.key}`}>
        {costTokens(spend, label).join(" · ")}
      </span>
    </span>
  );
}

/** Betterment E4: the five kinds, named by where the prompt goes. */
const KINDS: Array<{ kind: AddKind; name: string; hint: string }> = [
  { kind: "agent", name: "An agent on this Mac", hint: "CLAUDE CODE · CODEX" },
  { kind: "service", name: "A service", hint: "OPENROUTER · OPENAI · ANTHROPIC · GEMINI" },
  { kind: "lan", name: "A server on my network", hint: "LLAMA.CPP · VLLM · OLLAMA" },
  { kind: "local", name: "A model on this Mac", hint: "DOWNLOAD" },
  { kind: "mesh", name: "Another HoldSpeak", hint: "MESH" },
];

/** Betterment E4: Add an engine unfolds in place into the five kinds; a
 *  kind asks only what it needs. */
function AddByKind({
  ctrl,
  foundAgents,
  meshEngines,
  local,
}: {
  ctrl: RunsOnController;
  foundAgents: BoardEngine[];
  meshEngines: BoardEngine[];
  local: ReactNode;
}) {
  const a = ctrl.add;
  const services = ctrl.detection?.services ?? [];
  const agents = ctrl.detection?.agents ?? [];
  const service = services.find((tile) => tile.id === a.service);
  return (
    <div className="runson-kinds" data-testid="runson-add-kinds">
      <div className="runson-kind-tiles" role="group" aria-label="Kind of engine">
        {KINDS.map((tile) => (
          <Button
            key={tile.kind}
            variant={a.kind === tile.kind ? "primary" : "secondary"}
            className="runson-kind-tile"
            aria-pressed={a.kind === tile.kind}
            data-testid={`runson-kind-${tile.kind}`}
            onClick={() => a.choose(a.kind === tile.kind ? null : tile.kind)}
          >
            <span className="runson-kind-name">{tile.name}</span>
            <span className="runson-kind-hint">{tile.hint}</span>
          </Button>
        ))}
        <Button dense variant="ghost" className="runson-kind-close" data-testid="runson-add-close" onClick={a.close}>
          Close
        </Button>
      </div>

      {a.kind === "agent" ? (
        <ul className="runson-kind-list" data-testid="runson-kind-agents">
          {agents.map((agent) => {
            const found = foundAgents.find((engine) => engine.agentPreset === agent.preset);
            return (
              <li key={agent.preset} className="runson-kind-row" data-testid={`runson-agent-tile-${agent.preset}`}>
                <span className="runson-kind-row-name">{agent.name}</span>
                <EgressChip {...agentChip(agent.vendor, agent.vendorScope)} />
                {agent.added ? (
                  <StateChip state="success" label="ADDED" icon="●" />
                ) : found ? (
                  <Button dense variant="primary" disabled={ctrl.busy} data-testid={`runson-agent-add-${agent.preset}`} onClick={() => void ctrl.useFound(found.key)}>
                    Add
                  </Button>
                ) : agent.install ? (
                  <span className="runson-kind-install">
                    <span className="surface-token">NOT ON THIS MAC · INSTALL</span>
                    <code data-testid={`runson-agent-install-${agent.preset}`}>{agent.install}</code>
                  </span>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : null}

      {a.kind === "service" ? (
        <>
          <div className="runson-kind-tiles" role="group" aria-label="Service">
            {services.map((tile) => (
              <Button
                key={tile.id}
                dense
                variant={a.service === tile.id ? "primary" : "secondary"}
                aria-pressed={a.service === tile.id}
                data-testid={`runson-service-${tile.id}`}
                onClick={() => a.choose("service", tile.id)}
              >
                {tile.name}
              </Button>
            ))}
          </div>
          {service ? <AddEngineRow ctrl={ctrl} service={service} /> : null}
        </>
      ) : null}

      {a.kind === "lan" ? (
        <>
          <span className="runson-engine-actions">
            <Button
              dense
              variant="secondary"
              data-testid="runson-kind-find-lan"
              onClick={() => void ctrl.findOnLan()}
              disabled={ctrl.busy || ctrl.lanDiscovery === "CHECKING"}
              loading={ctrl.lanDiscovery === "CHECKING"}
            >
              Find on LAN
            </Button>
          </span>
          <AddEngineRow ctrl={ctrl} />
        </>
      ) : null}

      {a.kind === "local" ? <div data-testid="runson-local-models">{local}</div> : null}

      {a.kind === "mesh" ? (
        <div className="runson-kind-list" data-testid="runson-mesh-nodes">
          {meshEngines.map((engine) => (
            <span key={engine.key} className="runson-kind-row">
              <span className="runson-kind-row-name">{engine.name}</span>
              <StateChip state="success" label="ADDED" icon="●" />
            </span>
          ))}
          <span className="runson-kind-install">
            <span className="surface-token">ON THE OTHER MAC, RUN</span>
            <code data-testid="runson-mesh-command">{`holdspeak mesh serve --hub ${typeof window === "undefined" ? "http://<this-mac>:8765" : window.location.origin}`}</code>
          </span>
        </div>
      ) : null}
    </div>
  );
}

export function RunsOnCore({ scope, title, onBack }: CoreProps & { title?: string; onBack?: () => void }) {
  const ctrl = useRunsOn(scope);
  // Betterment E5 (DECISIONS #8): the drag switchboard is parked behind
  // Builder tools; What runs where is the face.
  const builder = useBuilderTools((state) => state.on);
  const setTitle = useContext(TitleSlotContext);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const layout = useSwitchboardLayout(rootRef);

  useEffect(() => {
    setTitle?.(title ?? "Engines");
  }, [setTitle, title]);
  // Window grammar (2026-10-24): the toolbar and the status bar touch the
  // frame; the engine sheets below keep their own inset.
  useWindowInterior("editor");

  const { roster, detection, engines } = ctrl;
  // PHILO-17 speech: with no speech model on this device the Speech job says
  // so and offers the one download, in place of an engine repair it cannot use.
  const speech = useSpeechSetup();
  const repairs = detection?.repairs ?? [];
  const { have, found } = useMemo(() => splitEngines(engines), [engines]);

  /* ── a repair's one verb (HS-200-04), on its engine; on its first job
     when the engine is not on the board ── */
  const repairButton = (repair: (typeof repairs)[number], testId: string): ReactNode => {
    const label =
      repair.control === "model_library" ? "Download" : repair.control === "endpoint_editor" ? "Fix address" : repair.control === "connections" ? "Key" : "Choose";
    return (
      <Button
        dense
        variant="secondary"
        data-testid={testId}
        onClick={() => {
          if (repair.control === "endpoint_editor") ctrl.add.openRow(repair.baseUrl);
          else if (repair.control === "model_library" && repair.presetId) {
            const preset = engines.find((e) => e.presetId === repair.presetId);
            if (preset) void ctrl.download(preset.key);
          } else if (repair.control === "connections") {
            void import("../../desk/shell").then(({ openSurfaceOr }) => openSurfaceOr("configure-integrations", "/settings"));
          } else if (repair.groups[0]) ctrl.select(repair.groups[0]);
        }}
      >
        {label}
      </Button>
    );
  };
  const onBoard = (engineId: string) => engines.some((e) => !e.found && e.detectId === engineId);

  // A cold desk leads with discovery. Assignment follows a saved engine;
  // optional local downloads stay in their own fold.
  const noEngine = !have.some((e) => e.profileId);

  /* ── the jobs ── */
  const jobs: SwitchJob[] = [];
  const wires: SwitchWire[] = [];
  const words: Record<string, ReturnType<typeof stateWord>> = {};
  const detailJob = ctrl.selected ?? (layout === "list" ? JOB_ORDER.find((job) => roster?.rows.some((row) => jobOf(row.id) === job)) : null);
  for (const job of JOB_ORDER) {
    const row = roster?.rows.find((r) => jobOf(r.id) === job);
    if (!row) continue;
    const word = jobState(job, row, engines, repairs);
    words[job] = word;
    const effective = ctrl.engineForJob(job);
    // Astra r1 (M2): the lead names the route the job really takes (for
    // summaries, the capability's own assignment).
    // Astra r2 (M1): until detection says the summary route, it is withheld.
    const lead = leadEngine(job, effective, detection, engines, ctrl.detectionFailed);
    const leadKnown = typeof lead === "object" && lead ? lead : undefined;
    // The words under the name on the phone list (and its open card).
    const leadWhere = leadKnown
      ? `${leadKnown.name} · on ${enginePlace(leadKnown).words}`
      : lead === null
        ? "OFF"
        : lead === "checking"
          ? "CHECKING…"
          : lead === "unknown"
            ? "NOT KNOWN"
            : lead === undefined
              ? "no engine"
              : word;
    const result = ctrl.results[job];
    const jobRepair = repairs.find((r) => r.groups.includes(job));
    const listening = job === SPEECH_JOB && ctrl.listening;
    const bindings = ctrl.trialBindingsForJob(job);
    const canTry = bindings.length > 0 && (job === SPEECH_JOB || Boolean(JOB_PROBE_CAPABILITIES[job]));
    const tryVerb: ReactNode = canTry ? (
      <span className="runson-trial-action">
      {bindings.filter((binding) => binding.host !== "THIS DEVICE").filter((binding, index, all) => all.findIndex((other) => other.host === binding.host) === index).map((binding) => (
        <span key={binding.host} data-testid={`runson-trial-egress-${job}`}><EgressChip label={binding.host} scope={binding.scope} /></span>
      ))}
      <Button
        dense
        variant="secondary"
        loading={ctrl.trying?.job === job && !listening}
        disabled={Boolean(ctrl.trying && ctrl.trying.job !== job)}
        onClick={() => ctrl.tryJob(job, bindings)}
        data-testid={`runson-try-${job}`}
      >
        {listening ? "Stop" : "Try it"}
      </Button>
      </span>
    ) : undefined;
    const feedback: ReactNode = result ? (
      <span className="runson-trial-result" data-tone={result.tone === "ok" ? undefined : result.tone}>
        <span role="status" aria-live="polite" aria-busy={result.tone === "busy" || undefined} data-testid={`runson-trial-state-${job}`}>{result.tokens.join(" · ")}</span>
        {result.egress ? <EgressChip label={result.egress.label} scope={result.egress.scope} /> : null}
        {result.sampleInput || result.sampleOutput ? <SurfaceWell>
          {result.sampleInput ? <span className="runson-trial-sample"><span className="runson-trial-caption">Sample</span><span data-testid={`runson-trial-input-${job}`}>{result.sampleInput}</span></span> : null}
          {result.sampleOutput ? <span className="runson-trial-sample"><span className="runson-trial-caption">Result</span><span data-testid={`runson-trial-output-${job}`}>{result.sampleOutput}</span></span> : null}
        </SurfaceWell> : null}
      </span>
    ) : lead === "unknown" ? (
      <Button dense variant="secondary" data-testid="runson-read-again" onClick={ctrl.readAgain}>Try again</Button>
    ) : jobRepair ? (
      <span data-tone="danger" data-testid={`runson-job-repair-${job}`}>
        {jobRepair.token}
        {jobRepair.groups[0] === job && !(jobRepair.engineId && onBoard(jobRepair.engineId)) ? repairButton(jobRepair, `runson-repair-job-${job}`) : null}
      </span>
    ) : word === "LIMITED" && limitTokens(job, effective).length ? (
      <span data-tone="warn">{limitTokens(job, effective).join(" · ")}</span>
    ) : undefined;
    const details = detailJob === job && job !== DEFAULT_JOB ? taskDetail(job, roster) : "";
    jobs.push({
      id: job,
      // PHILO-17 (U16): the card leads with what he gets and where it runs;
      // the task names are the card's details.
      name: jobName(job, row),
      lead: leadLine(job, row, lead),
      detail: taskDetail(job, roster),
      tasks: taskLine(job, roster, row),
      state: stateClass(word),
      isDefault: job === DEFAULT_JOB,
      verb: layout === "board" ? tryVerb : undefined,
      runsOn: leadWhere,
      // Astra r2 (M2): the open card on the phone shows the summary route,
      // not the Meetings wire (OFF and an unknown route show no engine).
      shows: job === MEETINGS_JOB ? (leadKnown ? leadKnown.key : null) : undefined,
      // C4: the engine the job runs on now, even when it follows the default.
      current: effective?.key,
      // For summaries: only while their capability has no head of its own.
      currentToken:
        effective &&
        row.inherited_from === "global" &&
        job !== DEFAULT_JOB &&
        !(job === MEETINGS_JOB && roster?.tasks.find((t) => t.id === "meeting.deferred_analysis")?.has_override)
          ? "Uses default engine"
          : undefined,
      // The limitation is a token on the job (§12 rule 6), until a Try
      // answers in its place; a repair names itself there too.
      // Astra r1 (finding 5): the setup stays while speech is not ready, also
      // after a Try it answered (its answer cannot repair a missing model).
      result: (layout === "list" && tryVerb) || feedback || details || (job === SPEECH_JOB && speech.notSetUp) ? (
        <span className="runson-job-content">
          {layout === "list" ? tryVerb : null}
          {feedback}
          {job === SPEECH_JOB && speech.notSetUp ? <SpeechSetup setup={speech} primary={false} testId="runson-speech-setup" /> : null}
          {details ? <span onClick={(event) => event.stopPropagation()}><FoldGadget title="Details"><span className="runson-job-details">{details}</span></FoldGadget></span> : null}
        </span>
      ) : undefined,
    });
    ownEntries(row).forEach((entry, order) => {
      wires.push({
        job,
        engine: entry.profile_id,
        order,
        tone:
          entry.readiness === "missing"
            ? "broken"
            : order === 0 && word === "LIMITED"
              ? "limited"
              : order === 0 && word === "BROKEN"
                ? "broken"
                : undefined,
      });
    });
  }

  /* ── the engines ── */
  const repairVerb = (engine: BoardEngine): ReactNode => {
    const repair = repairs.find((r) => r.engineId && r.engineId === engine.detectId);
    return repair ? repairButton(repair, `runson-repair-${engine.key}`) : undefined;
  };

  const plate = (engine: BoardEngine): SwitchEngine => {
    const progress = ctrl.downloads[engine.key];
    const downloading = progress != null;
    let verb: ReactNode = repairVerb(engine);
    let egress: ReactNode;
    let detail: ReactNode;
    if (engine.kind === "agent") {
      // Betterment E2: the prompt goes to the agent's vendor; the row
      // unfolds in place to its spend limit and cost.
      const open = ctrl.agent.open === engine.key;
      egress = <EgressChip {...agentChip(engine.vendor || hostLabel(engine), engine.vendorScope)} />;
      verb = (
        <Button
          dense
          variant="ghost"
          aria-expanded={open}
          data-testid={`runson-agent-open-${engine.key}`}
          onClick={() => ctrl.agent.toggle(engine.key)}
        >
          Spend
        </Button>
      );
      detail = open ? <AgentSpend ctrl={ctrl} engine={engine} /> : undefined;
    }
    const tokens = [...engine.tokens];
    const stopped = ctrl.failedDownloads[engine.key];
    if (engine.kind === "preset") {
      if (stopped && !downloading) {
        // V3: a stopped download keeps its reason on the plate until retried.
        const at = tokens.indexOf("NOT DOWNLOADED");
        if (at >= 0) tokens[at] = `STOPPED · ${stopped}`;
      }
      if (downloading) {
        const at = tokens.indexOf("NOT DOWNLOADED");
        if (at >= 0) tokens[at] = `${Math.round(progress)} %`;
      } else {
        // The file comes from the internet: the chip names that host.
        egress = <EgressChip label={(engine.downloadHost ?? "huggingface.co").toUpperCase()} scope="cloud" />;
        verb = (
          <Button dense variant="secondary" data-testid={`runson-download-${engine.key}`} onClick={() => void ctrl.download(engine.key)}>
            Download
          </Button>
        );
      }
    }
    return {
      id: engine.key,
      emblem: engine.emblem,
      name: engine.name,
      tokens,
      lamp: stopped && !downloading ? "broken" : lampFor(engine, ctrl.trying?.engine === engine.key || downloading),
      progress: downloading ? progress : null,
      verb,
      egress,
      detail,
      draggable: Boolean(engine.profileId),
    };
  };

  const haveEngines = have.filter((engine) => engine.kind !== "preset").map(plate);
  const localDownloads = have.filter((engine) => engine.kind === "preset").map(plate);
  const foundEngines: SwitchEngine[] = found.map((engine) => {
    if (engine.agentPreset) {
      // Betterment E2: an agent CLI on this Mac; one press adds it.
      return {
        id: engine.key,
        emblem: engine.emblem,
        name: foundAgentName(engine),
        tokens: [],
        lamp: lampFor(engine, false),
        egress: <EgressChip {...agentChip(engine.vendor || hostLabel(engine), engine.vendorScope)} />,
        verb: (
          <Button dense variant="secondary" disabled={ctrl.busy} data-testid={`runson-add-${engine.key}`} onClick={() => void ctrl.useFound(engine.key)}>
            Add
          </Button>
        ),
      };
    }
    const endpoint = engine.baseUrl ? endpointHostPort(engine.baseUrl).toUpperCase() : "";
    let host = "";
    if (engine.baseUrl) {
      try {
        host = new URL(engine.baseUrl).hostname.toUpperCase();
      } catch {
        host = engine.host.toUpperCase();
      }
    }
    const tokens = engine.baseUrl
      ? [endpoint, ...engine.tokens.filter((token) => token.trim().toUpperCase() !== host)].filter(Boolean)
      : engine.tokens;
    return {
      id: engine.key,
      emblem: engine.emblem,
      name: engine.name,
      tokens,
      lamp: lampFor(engine, false),
      verb: (
        <Button dense variant="secondary" disabled={ctrl.busy} data-testid={`runson-use-${engine.key}`} onClick={() => void ctrl.useFound(engine.key)}>
          Use it
        </Button>
      ),
    };
  });

  // Betterment E2: when every found row is on this Mac, the caption says so.
  const foundOnMac = found.every((engine) => engine.emblem === "MAC" || engine.emblem === "CLI");

  // The local downloads: in their own fold, or in the "A model on this Mac"
  // kind while that is open.
  const localContent: ReactNode = (
    <>
      {localDownloads.length ? <div className="runson-catalog">
        <SurfaceSwitchboard layout="board" jobs={[]} engines={localDownloads} wires={[]} />
      </div> : null}
      {roster ? <div className="concierge-root runson-meaning-host">
        <ul className="concierge-set-list runson-meaning"><MeaningSearchRow /></ul>
      </div> : null}
    </>
  );
  const localInKind = ctrl.add.open && ctrl.add.kind === "local";
  const meshEngines = have.filter((engine) => engine.kind === "lan" && !engine.baseUrl && engine.profileId);

  const engineFoot = ctrl.add.open ? (
    <AddByKind
      ctrl={ctrl}
      foundAgents={found.filter((engine) => engine.agentPreset)}
      meshEngines={meshEngines}
      local={localContent}
    />
  ) : null;

  /* ── the AppHead ── */
  const engineCount = have.filter((e) => e.profileId).length;
  const ready = Object.values(words).filter((w) => w === "READY").length;
  const limited = Object.values(words).filter((w) => w === "LIMITED").length;
  const broken = Object.values(words).filter((w) => w === "BROKEN").length;
  const waiting = Object.values(words).filter((w) => w === "WAITING").length;
  // PHILO-17 (U16): the one fact is what he has, never a count of jobs.
  const fact = engineCount ? `${engineCount} ${engineCount === 1 ? "engine" : "engines"}` : "No engine yet";
  const checked = detection?.checkedAt
    ? wireDate(detection.checkedAt)?.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false })
    : null;
  const hw = hardwareToken(detection);

  /* ── the status bar: what he has, in warm words; never a zero ── */
  const stripText = [
    ready ? `${ready} ready` : null,
    limited ? `${limited} limited` : null,
    broken ? `${broken} broken` : null,
    waiting ? `${waiting} waiting` : null,
    hw,
    checked ? `Checked ${checked}` : detection ? null : roster ? "Checking" : null,
  ].filter(Boolean).join(" · ");
  const statusItems: Array<StatusBarItem | null> = [
    { key: "fact", lamp: engineCount ? "ok" : "warn", text: <span data-testid="runson-fact">{roster ? fact : "Engines"}</span> },
    stripText ? {
      key: "strip",
      lamp: broken ? "fail" : limited ? "warn" : undefined,
      text: <span className="runson-strip" data-testid="runson-strip">{stripText}</span>,
    } : null,
    ctrl.receipt ? {
      key: "receipt",
      lamp: ctrl.receipt.tone === "danger" ? "fail" : undefined,
      text: (
        <span className="runson-receipt" data-testid="runson-receipt" data-tone={ctrl.receipt.tone}>
          {ctrl.receipt.text}
        </span>
      ),
    } : null,
  ];

  /* ── the foot ── */
  // Keep the useful roster-first paint, but do not call the face settled
  // while its initial reads can still add the strip, engines or speech row.
  const reading = (!roster && !ctrl.error)
    || (!detection && !ctrl.detectionFailed)
    || speech.ai.read.kind === "loading";
  return (
    <div className="runson-root" ref={rootRef} data-testid="runson-root" aria-busy={reading || undefined}>
      {/* Window grammar (2026-10-24): title bar → Toolbar [Add an engine]
          [Find on LAN] [Check all] → the engines and what runs where →
          StatusBar (`3 engines · 6 ready · 1 limited`, the hardware, the
          last check; the last change's receipt, Undo and its egress). No
          headline, no mono strip. */}
      <Toolbar label="Engines" data-testid="runson-toolbar">
        {/* One primary: a cold desk leads with discovery (Find on LAN); with
            an engine, Add an engine leads. */}
        <Button
          dense
          variant={noEngine ? "secondary" : "primary"}
          className="runson-add-open"
          aria-expanded={ctrl.add.open}
          data-testid="concierge-add-engine"
          onClick={() => (ctrl.add.open ? ctrl.add.close() : ctrl.add.openRow())}
        >
          <ToolGlyph kind="new" />
          Add an engine
        </Button>
        <Button
          dense
          variant={noEngine ? "primary" : "secondary"}
          className="runson-find-lan"
          data-testid="runson-find-lan"
          onClick={() => void ctrl.findOnLan()}
          disabled={ctrl.busy || ctrl.lanDiscovery === "CHECKING"}
          loading={ctrl.lanDiscovery === "CHECKING"}
        >
          <ToolGlyph kind="engine" />
          Find on LAN
        </Button>
        <Button dense variant="secondary" data-testid="runson-check-all" disabled={reading} onClick={ctrl.readAgain}>
          <ToolGlyph kind="retry" />
          Check all
        </Button>
      </Toolbar>

      <div className="runson-sheet">
      {engineFoot ? <div className="runson-choice" data-testid="runson-engine-choice">{engineFoot}</div> : null}
      {foundEngines.length ? (
        <div className="runson-catalog" data-testid="runson-found-engines">
          <SurfaceSwitchboard layout="board" jobs={[]} engines={[]} found={foundEngines} wires={[]} captions={{ found: foundOnMac ? "Found on this Mac" : "Found" }} />
        </div>
      ) : null}
      {noEngine && speech.notSetUp ? <SpeechSetup setup={speech} primary={false} testId="runson-speech-setup" /> : null}
      {roster && !builder ? (
        <div className="runson-catalog runson-engine-list" data-testid="runson-engines">
          {/* No wires here (What runs where assigns): plates are not dragged. */}
          <SurfaceSwitchboard layout="board" jobs={[]} engines={haveEngines.map((e) => ({ ...e, draggable: false }))} wires={[]} captions={{ engines: "Your engines" }} />
        </div>
      ) : null}
      {roster && !noEngine && !builder ? <WhatRunsWhere ctrl={ctrl} /> : null}
      {roster && builder ? (
        <div className={noEngine ? "runson-catalog" : undefined} data-testid="runson-assignments">
        <SurfaceSwitchboard
          layout={layout}
          jobs={noEngine ? [] : jobs}
          engines={haveEngines}
          wires={wires}
          selected={ctrl.selected}
          onSelect={ctrl.select}
          pulse={ctrl.trying?.job ?? null}
          accepts={ctrl.accepts}
          onPatch={(job, key, fallback) => void ctrl.patch(job, key, fallback)}
          onRefuse={ctrl.refuse}
          captions={{ jobs: noEngine ? undefined : "What HoldSpeak does", engines: "What you have", or: "Or", others: noEngine ? "" : "Other jobs" }}
        />
        </div>
      ) : ctrl.error ? (
        <span className="surface-token" data-tone="danger" role="alert">NOT READ</span>
      ) : null}

      {(localDownloads.length || roster) && !localInKind ? (
        <FoldGadget title="Download a local model" className="runson-downloads">
          {localContent}
        </FoldGadget>
      ) : null}

      </div>

      <StatusBar
        className="runson-foot"
        data-testid="runson-status"
        items={statusItems}
        egress={
          ctrl.egress ? (
            <span data-testid="runson-egress">
              <EgressChip label={ctrl.egress.label} scope={ctrl.egress.scope} />
            </span>
          ) : undefined
        }
        verbs={
          ctrl.canUndo || onBack ? (
            <>
              {ctrl.canUndo ? (
                <Button dense variant="secondary" disabled={ctrl.busy} data-testid="runson-undo" onClick={() => void ctrl.undo()}>
                  Undo
                </Button>
              ) : null}
              {onBack ? (
                <Button dense variant="secondary" className="prefs-back" onClick={onBack}>
                  <span aria-hidden="true">«</span> Settings
                </Button>
              ) : null}
            </>
          ) : undefined
        }
      />
    </div>
  );
}
