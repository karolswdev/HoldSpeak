/* Settings > Engines (the language, 2026-11-11). The owner got lost in
 * Settings > Models: this section says the one chain every job falls back
 * to, in order, and whether each engine is ready. The mast: "Codex first,
 * Gemini CLI second · 2 ready". The plate: an engine in the chain that is
 * not ready, with Fix; no engine, with Add an engine; else the first
 * engine, raised. The ledger: each engine with its place and its one verb
 * (Use first, Add), the spend limit of each agent CLI that takes one, and
 * Each job, which opens the Engines window. One controller (`useRunsOn`)
 * and one client (`features/runson/api.ts`) serve this section and the
 * Engines window. */
import { Button } from "../../../components/signal/Signal";
import { StringGadget } from "../../../desk/surface/gadgets";
import { openSurfaceOr } from "../../../desk/shell";
import { DEFAULT_JOB, accepts as acceptsRule, ownEntries, usd, type BoardEngine } from "../../../features/runson/model";
import { stateWord } from "../../../features/runson/stateWord";
import { useRunsOn } from "../../../features/runson/useRunsOn";
import { SectionMast, SettingLine, SettingsLedger, SettingsPlate } from "./native";

const PLACES = ["first", "second", "third", "fourth"];
const STATE: Record<ReturnType<typeof stateWord>, string> = {
  READY: "Ready", LIMITED: "Limited", BROKEN: "Not working", WAITING: "Checking", OFF: "Off",
};

/** The engine's state in one word, and what stops it when it says so. */
function stateLine(engine: BoardEngine): string {
  const word = STATE[stateWord(engine.state)];
  const stop = engine.tokens.find((token) => token.startsWith("NOT "));
  return stop ? `${word} · ${stop.charAt(0)}${stop.slice(1).toLowerCase()}` : word;
}

const openEngines = () => openSurfaceOr("configure-runs-on", "/models");

export function EnginesSection() {
  const ctrl = useRunsOn();
  const row = ctrl.roster?.rows.find((r) => r.id === "global");
  const engineOf = (id: string) => ctrl.engines.find((engine) => engine.key === id);
  const chain = ownEntries(row).map((entry) => engineOf(entry.profile_id)).filter((e): e is BoardEngine => Boolean(e));
  // A model record the default chain accepts (a download offer and a
  // speech engine are not; the same rule as the Engines window).
  const others = ctrl.engines.filter((e) => !e.found && e.profileId && !chain.includes(e) && acceptsRule(DEFAULT_JOB, e).ok);
  const ready = [...chain, ...others].filter((e) => stateWord(e.state) === "READY");
  const limited = [...chain, ...others].filter((e) => e.agentPreset && e.profileId && e.spend?.canLimit);
  const facts = [
    chain.length ? chain.map((e, i) => `${e.name} ${PLACES[i] ?? ""}`.trim()).join(", ") : "",
    ready.length ? `${ready.length} ready` : "",
  ].filter(Boolean).join(" · ");
  const loading = !ctrl.roster && !ctrl.error;
  const problem = chain.find((e) => stateWord(e.state) !== "READY");
  const firstReady = others.find((e) => stateWord(e.state) === "READY");

  const plate = ctrl.error ? (
    <SettingsPlate tone="coral" title="Engines unreadable" testId="settings-engines-plate"
      verbs={<Button variant="primary" onClick={openEngines}>Open Engines</Button>} />
  ) : loading ? null : problem ? (
    <SettingsPlate tone={stateWord(problem.state) === "BROKEN" ? "coral" : "brass"} title={problem.name}
      facts={stateLine(problem)} testId="settings-engines-plate"
      verbs={<Button variant="primary" onClick={openEngines} data-testid="settings-engines-fix">Fix</Button>} />
  ) : chain.length ? (
    <SettingsPlate tone="moss" title={chain[0].name} facts={`Runs your work · ${stateLine(chain[0])}`} testId="settings-engines-plate"
      verbs={<Button variant="secondary" disabled={ctrl.busy} onClick={ctrl.readAgain}>Check again</Button>} />
  ) : firstReady ? (
    <SettingsPlate tone="brass" title="No default engine" facts={`${firstReady.name} · ${stateLine(firstReady)}`} testId="settings-engines-plate"
      verbs={<Button variant="primary" disabled={ctrl.busy} onClick={() => void ctrl.patch(DEFAULT_JOB, firstReady.key, false)}
        data-testid="settings-engines-use">Use {firstReady.name}</Button>} />
  ) : (
    <SettingsPlate tone="brass" title="No engine yet" testId="settings-engines-plate"
      verbs={<Button variant="primary" onClick={openEngines} data-testid="settings-engines-add">Add an engine</Button>} />
  );

  const agent = ctrl.agent;
  return (
    <>
      <SectionMast id="engines" label="Engines" sprite="models" facts={facts} />
      {loading ? <p className="settings-reading" role="status">Reading engines…</p> : null}
      {plate}
      {ctrl.receipt ? (
        <p className="settings-receipt" role="status" data-tone={ctrl.receipt.tone} data-testid="settings-engines-receipt">{ctrl.receipt.text}</p>
      ) : null}
      {chain.length || others.length ? (
        <SettingsLedger label="Order">
          {chain.map((engine, index) => (
            <SettingLine key={engine.key} label={engine.name} testId={`settings-engine-${engine.key}`}
              value={`${(PLACES[index] ?? "").replace(/^./, (c) => c.toUpperCase())} · ${stateLine(engine)}`}
              verb={index > 0 ? <Button dense variant="secondary" disabled={ctrl.busy}
                onClick={() => void ctrl.patch(DEFAULT_JOB, engine.key, false)}>Use first</Button> : undefined} />
          ))}
          {others.map((engine) => (
            <SettingLine key={engine.key} label={engine.name} testId={`settings-engine-${engine.key}`} value={stateLine(engine)}
              verb={<Button dense variant="secondary" disabled={ctrl.busy}
                onClick={() => void ctrl.patch(DEFAULT_JOB, engine.key, chain.length > 0)}>{chain.length ? "Add" : "Use first"}</Button>} />
          ))}
        </SettingsLedger>
      ) : null}
      <SettingsLedger label="Limits and jobs">
        {limited.map((engine) => {
          const open = agent.open === engine.key;
          const limit = engine.spend?.limitUsd;
          return (
            <SettingLine key={engine.key} label={`Spend limit · ${engine.name}`} open={open} testId={`settings-spend-${engine.key}`}
              value={limit != null ? `${usd(limit)} per run` : "No limit"}
              verb={<Button dense variant="secondary" aria-expanded={open} onClick={() => agent.toggle(engine.key)}>{open ? "Close" : "Set"}</Button>}>
              <div className="settings-line-editor">
                <StringGadget label="Spend limit per run" caption mic={false} value={agent.draft} onChange={agent.setDraft}
                  placeholder="0.50" onKeyDown={(event) => { if (event.key === "Enter") void agent.save(engine.key); }} />
                {agent.invalid ? <span className="settings-line-refusal" role="alert">Between $0.01 and $1000</span> : null}
                <Button dense variant="primary" disabled={ctrl.busy} onClick={() => void agent.save(engine.key)}>Save</Button>
                {limit != null ? <Button dense variant="ghost" disabled={ctrl.busy} onClick={() => void agent.save(engine.key, true)}>No limit</Button> : null}
              </div>
            </SettingLine>
          );
        })}
        <SettingLine label="Each job" value="Speech, summaries, answers"
          verb={<Button dense variant="secondary" onClick={openEngines} data-testid="settings-engines-page-link">Open Engines</Button>} />
      </SettingsLedger>
    </>
  );
}
