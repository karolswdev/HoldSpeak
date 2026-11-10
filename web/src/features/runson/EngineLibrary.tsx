// Settings owns the model library; these controls use the existing Runs on controller.
import { useState, type ReactNode } from "react";
import { openSurfaceOr } from "../../desk/shell";
import { Button } from "../../components/signal/Signal";
import { CheckGadget, EgressChip, StateChip, StringGadget } from "../../desk/surface";
import { DotWord, ToolGlyph } from "../../desk/surface/kit";
import { Token } from "../../desk/surface/Token";
import { endpointHostPort, isLanAddress } from "../concierge/endpointDraft";
import { MeaningSearchRow } from "../concierge/MeaningSearchRow";
import { ListView } from "../../desk/surface/objects/ListView";
import { PhoneSpeechDay, useSpeechModels } from "./PhoneSpeech";
import { SpeechSetup, useSpeechSetup } from "../../desk/firstrun/SpeechSetup";
import { SettingsLedger, SettingLine } from "../../pages/cores/settings/native";
import { agentChip, costTokens, enginePlace, hostLabel, checkedWords, limitNoticeWords, type BoardEngine } from "./model";
import { stateWord } from "./stateWord";
import type { RunsOnController, AddKind } from "./useRunsOn";
import type { ServicePreset, ServiceTile } from "./api";
import "../concierge/concierge.css";
function AddEngineRow({ ctrl, service }: { ctrl: RunsOnController; service?: ServiceTile }) {
  const a = ctrl.add;
  const host = endpointHostPort(a.url);
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
          <span className="runson-add-answer">
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
        <span className="runson-add-answer" role="alert" data-testid="concierge-add-key-answer">
          <StateChip state="failure" label="Key required" />
        </span>
      ) : null}
      {a.state === "KEY_INVALID" ? (
        <span className="runson-add-answer" role="alert" data-testid="concierge-add-key-answer">
          <StateChip state="failure" label="Key invalid" />
          <Token className="surface-token">Bad characters</Token>
        </span>
      ) : null}
      {/* A.3: the answer is tokens (the word and the host), never the
          server's sentence. */}
      {a.state === "UNREACHABLE" ? (
        <span className="runson-add-answer" role="alert" data-testid="concierge-add-unreachable">
          <StateChip state="failure" label="Unreachable" />
          <Token code={Boolean(host)} className="surface-token" data-testid="concierge-add-reason">{host || "No address"}</Token>
        </span>
      ) : null}
      {a.state === "NOT_ADDED" ? (
        <span className="runson-add-answer" role="alert">
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
                {preset ? <Token className="surface-token runson-picker-preset">{preset}</Token> : null}
                <Token className="surface-token runson-picker-model">{model}</Token>
                {context ? <Token className="surface-token">{context.toLocaleString("en-US")} tokens</Token> : null}
                {used ? (
                  <StateChip state="success" label="Added" icon="●" />
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
        <Token className="surface-token" data-testid="concierge-add-no-match">No model matches</Token>
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
                  <StateChip state="success" label="Added" icon="●" />
                ) : found ? (
                  <Button dense variant="primary" disabled={ctrl.busy} data-testid={`runson-agent-add-${agent.preset}`} onClick={() => void ctrl.useFound(found.key)}>
                    Add
                  </Button>
                ) : agent.install ? (
                  <span className="runson-kind-install">
                    <DotWord tone="idle">Not on this Mac · Install it with</DotWord>
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
  const models = useSpeechModels();
  const speech = useSpeechSetup();
  const found = ctrl.engines.filter((e) => e.found && e.agentPreset);
  const mesh = ctrl.engines.filter((e) => e.kind === "lan" && !e.baseUrl && e.profileId);
  const local = <>
    <SettingsLedger label="Downloads">{ctrl.engines.filter((e) => e.kind === "preset").map(engineRow)}</SettingsLedger>
    <div className="concierge-root"><ul className="concierge-set-list"><MeaningSearchRow /></ul></div>
  </>;
  function engineRow(engine: BoardEngine) {
    const open = picked === engine.key;
    const progress = ctrl.downloads[engine.key];
    const failed = ctrl.failedDownloads[engine.key];
    const word = failed ? "Download stopped" : engine.signedIn === "no" ? "Not signed in"
      : engine.installed === false && engine.kind === "agent" ? "Not on this Mac"
      : engine.keySet === false && engine.kind === "cloud" ? "No key" : progress != null ? `Downloading ${Math.round(progress)}%`
      : engine.found ? "Found" : engine.kind === "preset" ? "Not downloaded"
      : ({ READY: "Ready", BROKEN: "Not working", LIMITED: "Limited", WAITING: "Checking", OFF: "Off" })[stateWord(engine.state)];
    const repair = ctrl.detection?.repairs.find((r) => r.engineId === engine.detectId);
    return <SettingLine key={engine.key} label={engine.name} value={word} open={open}
      testId={`settings-engine-${engine.key}`} verb={<Button dense variant="secondary" aria-expanded={open}
        onClick={() => setPicked(open ? null : engine.key)}>{open ? "Close" : "Inspect"}</Button>}>
      <div className="engines-editor">
        <span>{engine.kind === "preset" ? `Downloads from ${engine.downloadHost ?? "huggingface.co"}`
          : `Prompts go to ${engine.baseUrl || engine.vendor || (enginePlace(engine).place === "mac" ? "This Mac" : hostLabel(engine))}`}</span>
        {engine.modelId || engine.model ? <span>Model · {engine.modelId || engine.model}</span> : null}
        {engine.limitNotice ? <span>{limitNoticeWords(engine.limitNotice)}</span> : null}
        {ctrl.detection?.checkedAt ? <span>{checkedWords(ctrl.detection.checkedAt)}</span> : null}
        {failed ? <span role="alert">{failed}</span> : null}
        <div className="engines-verbs">
          {engine.found ? <Button disabled={ctrl.busy} onClick={() => void ctrl.useFound(engine.key)}>Add</Button> : null}
          {engine.kind === "preset" && progress == null ? <Button disabled={ctrl.busy} onClick={() => void ctrl.download(engine.key)}>Download</Button> : null}
          {repair?.control === "model_library" && repair.presetId ? <Button disabled={ctrl.busy} onClick={() => void ctrl.download(ctrl.engines.find((e) => e.presetId === repair.presetId)?.key ?? "")}>Download</Button> : null}
          {repair?.control === "endpoint_editor" ? <Button onClick={() => ctrl.add.openRow(repair.baseUrl)}>Fix address</Button> : null}
          {repair?.control === "connections" ? <Button onClick={() => openSurfaceOr("configure-integrations", "/settings")}>Set key</Button> : null}
          {engine.agentPreset && !engine.found ? <Button aria-expanded={ctrl.agent.open === engine.key}
            onClick={() => ctrl.agent.toggle(engine.key)}>Spend limit</Button> : null}
        </div>
        {engine.agentPreset && ctrl.agent.open === engine.key ? <AgentSpend ctrl={ctrl} engine={engine} /> : null}
      </div>
    </SettingLine>;
  }
  return <div className="engines-library" data-testid="settings-engines-library">
    <div className="engines-verbs">
      <Button variant="primary" aria-expanded={ctrl.add.open} data-testid="concierge-add-engine"
        onClick={() => ctrl.add.open ? ctrl.add.close() : ctrl.add.openRow()}>Add an engine</Button>
      <Button disabled={ctrl.busy || ctrl.lanDiscovery === "CHECKING"} data-testid="runson-find-lan"
        onClick={() => void ctrl.findOnLan()}>Find on LAN</Button>
    </div>
    {ctrl.add.open ? <AddByKind ctrl={ctrl} foundAgents={found} meshEngines={mesh} local={local} /> : null}
    <SettingsLedger label="Model library">{ctrl.engines.filter((e) => e.kind !== "preset").map(engineRow)}</SettingsLedger>
    {!ctrl.add.open || ctrl.add.kind !== "local" ? local : null}
    <SpeechSetup setup={speech} toolbar testId="settings-engines-speech" />
    <ListView label="Phone speech"><PhoneSpeechDay models={models} /></ListView>
  </div>;
}
