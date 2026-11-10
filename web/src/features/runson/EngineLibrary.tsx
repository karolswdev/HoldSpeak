// Settings owns the model library; these controls use the existing Runs on controller.
import { useState, type ReactNode } from "react";
import { openSurfaceOr } from "../../desk/shell";
import { Button } from "../../components/signal/Signal";
import { CheckGadget, EgressChip, StateChip, StringGadget, PaneInspector, PaneActions, GadgetGroup, GadgetRow, SegmentedTabs, PaneGroup, type ListVerb } from "../../desk/surface";
import { DotWord, ToolGlyph } from "../../desk/surface/kit";
import { Token } from "../../desk/surface/Token";
import { endpointHostPort, isLanAddress } from "../concierge/endpointDraft";
import { MeaningSearchRow } from "../concierge/MeaningSearchRow";
import { ListView } from "../../desk/surface/objects/ListView";
import { speechStateWord, licenceWords, useSpeechModels } from "./PhoneSpeech";
import { SpeechSetup, useSpeechSetup } from "../../desk/firstrun/SpeechSetup";
import { SettingsLedger, SettingLine } from "../../pages/cores/settings/native";
import { agentChip, costTokens, enginePlace, hostLabel, checkedWords, limitNoticeWords, type BoardEngine } from "./model";
import { stateWord } from "./stateWord";
import type { RunsOnController, AddKind } from "./useRunsOn";
import type { ServicePreset, ServiceTile } from "./api";

function AddEngineRow({ ctrl, service }: { ctrl: RunsOnController; service?: ServiceTile }) {
  const a = ctrl.add;
  const host = endpointHostPort(a.url);
  return (
    <div className="surface-preference-pane" data-testid="concierge-add-engine-row">
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
      <span className="surface-pane-group" data-testid="concierge-add-key">
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
          <CheckGadget variant="token" label="My server" checked={a.mine} onChange={a.setMine} />
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
          <span className="surface-pane-actions">
            <StateChip state="success" label="Ready" icon="●" />
            {a.tools ? (
              <Token className="surface-token" data-testid="concierge-add-tools">
                {a.tools === "yes" ? "Tools" : a.tools === "no" ? "No tools" : "Tools unknown"}
              </Token>
            ) : null}
          </span>
          <ModelPicker ctrl={ctrl} presets={service?.presets ?? []} />
        </>
      ) : null}
      {a.state === "KEY_REQUIRED" ? (
        <span className="surface-pane-actions" role="alert" data-testid="concierge-add-key-answer">
          <StateChip state="failure" label="Key required" />
        </span>
      ) : null}
      {a.state === "KEY_INVALID" ? (
        <span className="surface-pane-actions" role="alert" data-testid="concierge-add-key-answer">
          <StateChip state="failure" label="Key invalid" />
          <Token className="surface-token">Bad characters</Token>
        </span>
      ) : null}
      {/* A.3: the answer is tokens (the word and the host), never the
          server's sentence. */}
      {a.state === "UNREACHABLE" ? (
        <span className="surface-pane-actions" role="alert" data-testid="concierge-add-unreachable">
          <StateChip state="failure" label="Unreachable" />
          <Token code={Boolean(host)} className="surface-token" data-testid="concierge-add-reason">{host || "No address"}</Token>
        </span>
      ) : null}
      {a.state === "NOT_ADDED" ? (
        <span className="surface-pane-actions" role="alert">
          <StateChip state="failure" label="Not added" />
          <Token className="surface-token" data-testid="concierge-add-reason">{a.reason}</Token>
        </span>
      ) : null}
    </div>
  );
}

/** A caps token line in sentence case (window grammar: no caps soup); the
 *  engine's own name keeps its spelling. */
function sentence(text: string, keep?: string): string {
  if (!text) return text;
  let out = text.toLowerCase();
  out = out[0].toUpperCase() + out.slice(1);
  if (keep) out = out.replace(new RegExp(keep.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"), keep);
  return out;
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
  const [picked, pick] = useState<string | null>(null);
  return <div className="surface-preference-pane" data-testid="concierge-add-picker">
    {a.models.length >= PICKER_SEARCH_FROM ? <StringGadget label="Find a model" caption value={a.query} onChange={a.setQuery} placeholder="Model name" /> : null}
    <ListView label="Available models" ordered rows={shown.map((model) => ({ id: model, kind: "model", name: named.get(model) || model,
      cells: { context: a.contexts[model] ? `${a.contexts[model].toLocaleString("en-US")} tokens` : "" },
      state: a.used.includes(model) ? { label: "Added", tone: "ok" as const } : undefined,
    }))} columns={[{ key: "name", word: "Model" }, { key: "context", word: "Context", track: "140px" }, { key: "state", word: "State", track: "90px" }]}
      selectedId={picked} onSelect={pick} defaultVerb="use" verbs={[{ id: "use", label: "Use", key: "Enter", enabled: (row) => Boolean(row) && !ctrl.busy && !a.used.includes(row!.id), run: (row) => { if (row) void a.save(row.id); } }]} />
  </div>;
}

/** Betterment E2: an agent engine's row, unfolded: Spend limit per run (No
 *  limit, or an amount the CLI enforces) and today's and this week's
 *  reported cost. A CLI that cannot stop a run at a limit says so. */
function AgentSpend({ ctrl, engine }: { ctrl: RunsOnController; engine: BoardEngine }) {
  const a = ctrl.agent;
  const spend = engine.spend;
  const label = engine.model || engine.name;
  return (
    <span className="surface-preference-pane" data-testid={`runson-agent-spend-${engine.key}`}>
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
              <DotWord tone="fail">More than $0, up to $1000</DotWord>
            </span>
          ) : null}
        </>
      ) : (
        <span className="runson-quiet" data-testid={`runson-agent-no-limit-${engine.key}`}>
          {`No spend limit in ${label}`}
        </span>
      )}
      <span className="runson-quiet" data-testid={`runson-agent-cost-${engine.key}`}>
        {sentence(costTokens(spend, label).join(" · "), label)}
      </span>
    </span>
  );
}

/** Betterment E4: the five kinds, named by where the prompt goes. */
const KINDS: Array<{ kind: AddKind; name: string; hint: string }> = [
  { kind: "agent", name: "An agent on this Mac", hint: "Claude Code · Codex" },
  { kind: "service", name: "A service", hint: "OpenRouter · OpenAI · Anthropic · Gemini" },
  { kind: "lan", name: "A server on my network", hint: "llama.cpp · vLLM · Ollama" },
  { kind: "local", name: "A model on this Mac", hint: "Download" },
  { kind: "mesh", name: "Another HoldSpeak", hint: "Mesh" },
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
  const [picked, pick] = useState<string | null>(null);
  const services = ctrl.detection?.services ?? [];
  const agents = ctrl.detection?.agents ?? [];
  const service = services.find((tile) => tile.id === a.service);
  return (
    <div className="surface-preference-pane" data-testid="runson-add-kinds">
      <div className="surface-pane-actions" role="group" aria-label="Kind of engine">
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

          </Button>
        ))}
        <Button dense variant="ghost" className="runson-kind-close" data-testid="runson-add-close" onClick={a.close}>
          Close
        </Button>
      </div>

      {a.kind === "agent" ? <>
        <ListView label="Agent engines" rows={agents.map((agent) => ({ id: agent.preset, kind: "agent", name: agent.name, cells: { vendor: agent.vendor }, state: { label: agent.added ? "Added" : foundAgents.some((engine) => engine.agentPreset === agent.preset) ? "Found" : "Not installed", tone: agent.added ? "ok" as const : "idle" as const } }))}
          columns={[{ key: "name", word: "Agent" }, { key: "vendor", word: "Prompts go to", track: "140px" }, { key: "state", word: "State", track: "110px" }]}
          selectedId={picked} onSelect={pick} verbs={[{ id: "add", label: "Add", enabled: (row) => !ctrl.busy && Boolean(foundAgents.find((engine) => engine.agentPreset === row?.id)) && !agents.find((agent) => agent.preset === row?.id)?.added,
            run: (row) => { const found = foundAgents.find((engine) => engine.agentPreset === row?.id); if (found) void ctrl.useFound(found.key); } }]} />
        {agents.find((agent) => agent.preset === picked)?.install ? <code className="surface-command-code">{agents.find((agent) => agent.preset === picked)?.install}</code> : null}
      </> : null}

      {a.kind === "service" ? (
        <>
          <div className="surface-pane-actions" role="group" aria-label="Service">
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
          <span className="surface-pane-actions">
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
              <StateChip state="success" label="Added" icon="●" />
            </span>
          ))}
          <span className="runson-kind-install">
            <Token className="surface-token">On the other Mac, run</Token>
            <code data-testid="runson-mesh-command">{`holdspeak mesh serve --hub ${typeof window === "undefined" ? "http://<this-mac>:8765" : window.location.origin}`}</code>
          </span>
        </div>
      ) : null}
    </div>
  );
}


export function EngineLibrary({ ctrl }: { ctrl: RunsOnController }) {
  const [picked, setPicked] = useState<string | null>(null);
  const [tab, setTab] = useState("engines");
  const [speechPicked, pickSpeech] = useState<string | null>(null);
  const [inspecting, inspect] = useState(false);
  const models = useSpeechModels();
  const speech = useSpeechSetup();
  const found = ctrl.engines.filter((e) => e.found && e.agentPreset);
  const mesh = ctrl.engines.filter((e) => e.kind === "lan" && !e.baseUrl && e.profileId);
  const engines = ctrl.engines;
  const selected = engines.find((engine) => engine.key === picked);
  const verbs: ListVerb[] = [
    { id: "add", label: "Add an engine", symbol: "+", run: () => ctrl.add.openRow() },
    { id: "open", label: "Inspect", key: "Enter", enabled: (row) => Boolean(row), run: () => inspect(true) },
    { id: "use", label: "Add", enabled: (row) => !ctrl.busy && Boolean(engines.find((engine) => engine.key === row?.id)?.found), run: (row) => { if (row) void ctrl.useFound(row.id); } },
    { id: "download", label: "Download", enabled: (row) => !ctrl.busy && engines.find((engine) => engine.key === row?.id)?.kind === "preset", run: (row) => { if (row) void ctrl.download(row.id); } },
  ];
  const list = <ListView label="Model library" ordered rows={engines.map((engine) => ({ id: engine.key, kind: "engine", name: engine.name,
    cells: { where: engine.kind === "agent" || engine.kind === "local" || engine.kind === "preset" ? "This Mac" : engine.host },
    state: { label: engine.found ? "Found" : engine.kind === "preset" ? "Download" : stateWord(engine.state) === "READY" ? "Ready" : "Not ready", tone: stateWord(engine.state) === "READY" ? "ok" as const : "warn" as const },
  }))} columns={[{ key: "name", word: "Engine", track: "minmax(0, 1.5fr)" }, { key: "where", word: "Where", track: "minmax(0, 1fr)" }, { key: "state", word: "State", track: "110px" }]}
    selectedId={picked} onSelect={setPicked} defaultVerb="open" verbs={verbs} rowProps={(row) => ({ "data-testid": `settings-engine-${row.id}` })} />;
  return <div className="surface-preference-pane" data-testid="settings-engines-library">
    {ctrl.detectionFailed ? <PaneActions><span role="alert">Engine checks failed</span><Button onClick={ctrl.readAgain}>Retry</Button></PaneActions> : null}
    <SegmentedTabs label="Model library" value={tab} onChange={setTab} tabs={[{ id: "engines", label: "Engines" }, { id: "speech", label: "Speech" }, { id: "search", label: "Search" }]}>
      <div className="surface-tab-panel" hidden={tab !== "engines"}>
    {ctrl.add.open ? <PaneInspector label="Add engine" onClose={ctrl.add.close}><AddByKind ctrl={ctrl} foundAgents={found} meshEngines={mesh} local={list} /></PaneInspector>
    : inspecting && selected ? <PaneInspector label={selected.name} onClose={() => inspect(false)}>
      <GadgetGroup><GadgetRow label="Prompts go to">{selected.baseUrl || selected.vendor || (enginePlace(selected).place === "mac" ? "This Mac" : hostLabel(selected))}</GadgetRow>
        {selected.modelId || selected.model ? <GadgetRow label="Model">{selected.modelId || selected.model}</GadgetRow> : null}
        {selected.limitNotice ? <GadgetRow label="Usage">{limitNoticeWords(selected.limitNotice)}</GadgetRow> : null}
      </GadgetGroup>
      {selected.agentPreset && !selected.found ? <><Button dense aria-expanded={ctrl.agent.open === selected.key} onClick={() => ctrl.agent.toggle(selected.key)}>Spend limit</Button>
        {ctrl.agent.open === selected.key ? <AgentSpend ctrl={ctrl} engine={selected} /> : null}</> : null}
      {ctrl.failedDownloads[selected.key] ? <span role="alert">{ctrl.failedDownloads[selected.key]}</span> : null}
    </PaneInspector> : list}
      </div>
      <div className="surface-tab-panel" hidden={tab !== "speech"}>
        <PaneGroup label="Speech to text" grow={false}><SpeechSetup setup={speech} toolbar testId="settings-engines-speech" /></PaneGroup>
        {models.rows ? <ListView label="Phone speech" ordered rows={models.rows.map((model) => ({ id: model.id, kind: "model", name: model.label,
          cells: { licence: licenceWords(model) }, state: { label: model.state === "missing" ? "Missing" : speechStateWord(model).label, tone: speechStateWord(model).tone },
        }))} columns={[{ key: "name", word: "Model" }, { key: "licence", word: "Licence", track: "minmax(0, 1fr)" }, { key: "state", word: "State", track: "120px" }]}
          selectedId={speechPicked} onSelect={pickSpeech} verbs={[{ id: "download", label: "Download", enabled: (row) => !models.pressed && Boolean(models.rows?.some((model) => model.id === row?.id && ["missing", "partial", "failed"].includes(model.state))), run: (row) => { if (row) void models.download(row.id); } }]} /> : models.reading ? <span role="status">Reading speech models…</span> : <PaneActions><span role="alert">Speech models not read</span></PaneActions>}
      </div>
      <div className="surface-tab-panel" hidden={tab !== "search"}><MeaningSearchRow form /></div>
    </SegmentedTabs>
  </div>;
}
