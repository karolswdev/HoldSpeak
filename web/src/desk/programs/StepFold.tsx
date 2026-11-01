/* Programs PG-REQ (PROGRAMS-REQUIREMENTS-2026-10-31 §7, §8, §9; canvas
 * programs-requirements-2026-10-31 "The step fold, the ledger per step,
 * and adjust"). The step fold replaces the Gate fold.
 *
 * PG-WINDOW W3 (PROGRAM-WINDOW-2026-10-31, direction A): the open step
 * unfolds under its row on the board, with no fold head. First what it must
 * prove (its requirement lines, each with its lamp, and Add a requirement
 * with this step as its Where), then what the agent did (the hub's story:
 * at most three plain lines), then the parts strip (Brief · Gate · Findings
 * · Handoffs · Ledger; none open unless his eye needs one: a red check opens
 * Gate, findings open Findings) and the step's verbs. A press on the open
 * token closes it.
 *
 * Head: "Step 3 · Projections off the loop" · a FilterTokens strip (Brief ·
 * Requirements · Gate · Findings · Handoffs · Ledger; a token with nothing
 * behind it is not drawn) · at the right, for a Planned step Move up · Move
 * down · Insert before (and Alt+↑ / Alt+↓), for a started step Amend brief
 * · Hand off. The first token is the one his eye needs: Gate when the check
 * is red, Requirements when one is Unmet, Findings when one waits on him,
 * else Brief.
 *
 * Brief: a Planned step's fields are the Drafting gadgets, saved in place;
 * a started step's brief is the text the agent read, with his additions
 * under it, and every frozen field is text with its reason as the hover
 * title ("The agent has read it"). Amend brief adds a line that HoldSpeak
 * types at the next turn boundary. */
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { WorkMenu } from "../components/DeskMenu";
import { CheckGadget, CycleGadget, DotWord, FilterTokens, PadGadget, StringGadget } from "../surface";
import { Token } from "../surface/Token";
import { plainFail } from "../surface/plainFailure";
import { amendStep, changeStep, handoff, insertStep } from "./api";
import { GateFacts } from "./GateFold";
import { HandoffLine, StepLedger, clock } from "./Ledger";
import { AddRequirementRow, RequirementRow } from "./Requirements";
import { runsOnLabel } from "./StepRow";
import type { Program, ProgramStep } from "./types";

type Failure = { words: string; title: string } | null;
type Part = "brief" | "gate" | "findings" | "handoffs" | "ledger";

const PART_WORDS: Record<Part, string> = {
  brief: "Brief", gate: "Gate", findings: "Findings", handoffs: "Handoffs", ledger: "Ledger",
};

export function isPlanned(step: ProgramStep): boolean {
  return step.state === "planned" || step.state === "ready";
}

/** The step a move puts this one before (`end` past the last), or null
 *  where it cannot go. */
export function moveTarget(program: Program, step: ProgramStep, dir: -1 | 1): string | null {
  const top = program.steps.filter((row) => !row.race_of).sort((a, b) => a.ordinal - b.ordinal);
  const index = top.findIndex((row) => row.id === step.id);
  if (index < 0) return null;
  if (dir < 0) return index > 0 ? top[index - 1].id : null;
  if (index >= top.length - 1) return null;
  return index + 2 < top.length ? top[index + 2].id : "end";
}

/** Why a move is refused before it is sent: a step does not move above a
 *  step it comes after, nor below one that comes after it. */
export function moveRefusal(program: Program, step: ProgramStep, dir: -1 | 1): string | null {
  const top = program.steps.filter((row) => !row.race_of).sort((a, b) => a.ordinal - b.ordinal);
  const index = top.findIndex((row) => row.id === step.id);
  const other = top[index + dir];
  if (!other) return null;
  if (dir < 0 && step.after.includes(other.ordinal)) return `Step ${step.ordinal} comes after step ${other.ordinal}`;
  if (dir > 0 && other.after.includes(step.ordinal)) return `Step ${other.ordinal} comes after step ${step.ordinal}`;
  return null;
}

/** Move a Planned step one place (the verbs and Alt+↑ / Alt+↓). */
export async function moveStep(program: Program, step: ProgramStep, dir: -1 | 1): Promise<{ program: Program | null } | { refused: string }> {
  const refused = moveRefusal(program, step, dir);
  if (refused) return { refused };
  const target = moveTarget(program, step, dir);
  if (!target) return { refused: dir < 0 ? `Step ${step.ordinal} is the first step` : `Step ${step.ordinal} is the last step` };
  return { program: await changeStep(program.id, step.id, { before: target }) };
}

function partsOf(program: Program, step: ProgramStep): Part[] {
  const parts: Part[] = ["brief"];
  if (step.history || step.check.verdict || step.check.running || step.station >= 2) parts.push("gate");
  if (step.findings.length) parts.push("findings");
  if (step.handoffs?.length) parts.push("handoffs");
  if (program.checkpoints.some((row) => row.step_id === step.id)) parts.push("ledger");
  return parts;
}

/** The part his eye needs, or none: a red check opens Gate, findings open
 *  Findings, a Planned step opens its Brief (its fields); else nothing. */
function firstPart(step: ProgramStep, parts: readonly Part[]): Part | "" {
  if ((step.history || step.state === "check_failed") && parts.includes("gate")) return "gate";
  if (step.state === "findings" && parts.includes("findings")) return "findings";
  if (isPlanned(step) && step.editable?.includes("brief")) return "brief";
  return "";
}

const EFFORTS = [{ value: "low", label: "Low" }, { value: "medium", label: "Medium" }, { value: "high", label: "High" }];
const AGENTS = [
  { profile: "claude-default", word: "Claude Code" },
  { profile: "codex-default", word: "Codex" },
  { profile: "pi-default", word: "pi" },
];

/** A frozen field: its words, with the reason as the hover title. */
function Frozen({ name, value, reason, testId }: { name: string; value: string; reason?: string; testId?: string }) {
  return (
    <span className="pg-frozen" title={reason} data-frozen={reason ? "" : undefined} data-testid={testId}>
      <span className="pg-frozen-name">{name}</span> {value}
    </span>
  );
}

/** A Planned step's brief: its fields, edited in place. */
function PlannedBrief({ program, step, onApplied, onFailed }: {
  program: Program; step: ProgramStep; onApplied(next: Program | null): void; onFailed(failure: Failure): void;
}) {
  const [title, setTitle] = useState(step.title);
  const [brief, setBrief] = useState(step.brief);
  useEffect(() => { setTitle(step.title); setBrief(step.brief); }, [step.id, step.title, step.brief]);
  const editable = new Set(step.editable ?? []);
  const save = async (body: Parameters<typeof changeStep>[2]) => {
    onFailed(null);
    try {
      onApplied(await changeStep(program.id, step.id, body));
    } catch (cause) {
      onFailed(plainFail(`Step ${step.ordinal} was not changed`, cause, "The step is as it was", "Try again"));
    }
  };
  const earlier = program.steps.filter((row) => !row.race_of && row.ordinal < step.ordinal);
  const afterOptions = [{ value: "", label: "None" }, ...earlier.map((row) => ({ value: String(row.ordinal), label: `After ${row.ordinal}` }))];
  return (
    <div className="pg-sf-brief" data-testid="programs-step-brief" data-planned="">
      <div className="pg-sf-fields">
        <span className="pg-sf-title">
          <StringGadget label={`Step ${step.ordinal} title`} value={title} onChange={setTitle}
            inputProps={{ onBlur: () => { if (title.trim() && title !== step.title) void save({ title: title.trim() }); } }} />
        </span>
        {step.owns.length ? <span className="pg-sf-owns">{step.owns.slice(0, 2).map((path) => <Token key={path} code>{path}</Token>)}</span> : null}
        {editable.has("agent") ? (
          <span className="pg-sf-agent">
            <CycleGadget label={`Step ${step.ordinal} agent`} value={step.profile ?? program.default.profile ?? "claude-default"}
              options={AGENTS.map((row) => ({ value: row.profile, label: row.word }))}
              onChange={(profile) => void save({ profile, engine: null })} />
          </span>
        ) : null}
        {editable.has("effort") ? (
          <span className="pg-sf-effort">
            <CycleGadget label={`Step ${step.ordinal} effort`} value={step.effort ?? "medium"} options={EFFORTS}
              onChange={(effort) => void save({ effort: effort as "low" | "medium" | "high" })} />
          </span>
        ) : null}
        {editable.has("after") ? (
          <span className="pg-sf-after">
            <CycleGadget label={`Step ${step.ordinal} after`} value={step.after.length ? String(step.after[step.after.length - 1]) : ""}
              options={afterOptions} onChange={(value) => void save({ after: value ? [Number(value)] : [] })} />
          </span>
        ) : null}
      </div>
      {editable.has("brief") ? (
        <div className="pg-sf-pad">
          <PadGadget label={`Step ${step.ordinal} brief`} rows={3} value={brief} onChange={setBrief}
            inputProps={{ onBlur: () => { if (brief !== step.brief) void save({ brief }); } }} />
        </div>
      ) : null}
    </div>
  );
}

/** A started step's brief: as it was sent, his additions under it, and
 *  Amend brief. */
function StartedBrief({ program, step, onApplied, onFailed, amendRef }: {
  program: Program; step: ProgramStep; onApplied(next: Program | null): void; onFailed(failure: Failure): void;
  amendRef: React.MutableRefObject<HTMLInputElement | null>;
}) {
  const [line, setLine] = useState("");
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState(step.title);
  useEffect(() => setTitle(step.title), [step.id, step.title]);
  const frozen = step.frozen ?? {};
  const editable = new Set(step.editable ?? []);
  const amend = async () => {
    if (!line.trim()) return;
    setBusy(true);
    onFailed(null);
    try {
      onApplied(await amendStep(program.id, step.id, line.trim()));
      setLine("");
    } catch (cause) {
      onFailed(plainFail("The line was not added to the brief", cause, "Your line is kept", "Try again"));
    } finally {
      setBusy(false);
    }
  };
  const rename = async () => {
    if (!title.trim() || title === step.title) return;
    onFailed(null);
    try {
      onApplied(await changeStep(program.id, step.id, { title: title.trim() }));
    } catch (cause) {
      onFailed(plainFail(`Step ${step.ordinal} was not renamed`, cause, "The title is as it was", "Try again"));
    }
  };
  const why = frozen.brief ?? "The agent has read it";
  return (
    <div className="pg-sf-brief" data-testid="programs-step-brief">
      {editable.has("title") ? (
        <div className="pg-sf-fields">
          <span className="pg-sf-title">
            <StringGadget label={`Step ${step.ordinal} title`} value={title} onChange={setTitle} inputProps={{ onBlur: () => void rename() }} />
          </span>
        </div>
      ) : null}
      <div className="pg-sf-frozen" data-testid="programs-step-frozen">
        <DotWord title={why}>{`Frozen · ${why.charAt(0).toLowerCase()}${why.slice(1)}`}</DotWord>
        <span className="pg-sf-frozen-facts">
          <Frozen name="Owns" value={step.owns.length ? step.owns.join(", ") : "nothing named"} reason={frozen.owns} testId="programs-frozen-owns" />
          <Frozen name="Effort" value={(step.effort ?? "medium").replace(/^./, (c) => c.toUpperCase())} reason={frozen.effort} testId="programs-frozen-effort" />
          <Frozen name="After" value={step.after.length ? step.after.join(", ") : "none"} reason={frozen.after} testId="programs-frozen-after" />
          <Frozen name="Agent" value={runsOnLabel(step.profile, step.engine)} reason={frozen.agent} testId="programs-frozen-agent" />
        </span>
      </div>
      <div className="pg-sf-brieftext" title={why} data-testid="programs-step-brieftext">
        <span className="pg-sf-brieftext-body">{step.brief || "No brief"}</span>
        {(step.amendments ?? []).map((row, index) => (
          <span key={`${row.at}-${index}`} className="pg-sf-amendment" data-testid="programs-step-amendment" data-sent={row.sent_at ? "" : undefined}>
            <b>{`Added by ${row.by === "owner" ? "you" : "an agent"} · ${clock(row.at)} · ${row.sent_at ? `typed at ${clock(row.sent_at)}` : "waits for the next turn"}`}</b>
            {row.line}
          </span>
        ))}
      </div>
      {editable.has("amend") ? (
        <div className="pg-sf-amend" data-testid="programs-step-amend">
          <span className="pg-sf-amend-field">
            <StringGadget label="Add to the brief" value={line} onChange={setLine} placeholder="Add to the brief" inputRef={amendRef}
              onKeyDown={(event) => { if (event.key === "Enter") void amend(); }} />
          </span>
          <Button dense variant="primary" loading={busy} disabled={busy || !line.trim()} onClick={() => void amend()}
            data-testid="programs-step-amend-send">Amend brief</Button>
        </div>
      ) : null}
    </div>
  );
}

/** Insert before: a new Planned step at this one's place. */
function InsertRow({ program, step, onApplied, onDone }: {
  program: Program; step: ProgramStep; onApplied(next: Program | null): void; onDone(): void;
}) {
  const [title, setTitle] = useState("");
  const [waits, setWaits] = useState(true);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState<Failure>(null);
  const insert = async () => {
    if (!title.trim()) return;
    setBusy(true);
    setFailed(null);
    try {
      onApplied(await insertStep(program.id, step.id, {
        title: title.trim(), brief: "", profile: program.default.profile, engine: program.default.engine?.id ?? null,
        after: [...step.after],
      }, waits));
      onDone();
    } catch (cause) {
      setFailed(plainFail("The step was not inserted", cause, "The plan is as it was", "Try again"));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="pg-sf-insert" data-testid="programs-step-insert">
      <span className="pg-sf-insert-n" aria-hidden="true">+</span>
      <span className="pg-sf-insert-title">
        <StringGadget label="The new step's title" value={title} onChange={setTitle} placeholder="The new step's title" autoFocus
          onKeyDown={(event) => { if (event.key === "Enter") void insert(); if (event.key === "Escape") onDone(); }} />
      </span>
      <CheckGadget variant="token" label={`${step.ordinal} waits`} checked={waits} onChange={setWaits} />
      <Button dense variant="ghost" disabled={busy} onClick={onDone} data-testid="programs-step-insert-cancel">Not now</Button>
      <Button dense variant="primary" loading={busy} disabled={busy || !title.trim()} onClick={() => void insert()}
        data-testid="programs-step-insert-send">{`Insert as step ${step.ordinal}`}</Button>
      {failed ? <p className="pg-failure" role="status" title={failed.title}>{failed.words}</p> : null}
    </div>
  );
}

const FINDING_TONE: Record<string, "fail" | "ask" | "idle"> = { required: "fail", should: "ask" };

/** What the agent did (the hub's story, PG-WINDOW W1). */
function StepStory({ step }: { step: ProgramStep }) {
  const story = step.story ?? [];
  if (!story.length) return null;
  return (
    <section className="pg-sf-story" aria-label="What the agent did" data-testid="programs-step-story">
      <h4 className="pg-sf-cap">What the agent did</h4>
      <ul className="pg-sf-story-lines">
        {story.map((row, index) => (
          <li key={`${row.at}-${index}`} className="pg-sf-story-line">
            <span className="pg-sf-story-at">{row.at ? clock(row.at) : ""}</span>
            <span className="pg-sf-story-words">{row.line}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** What it must prove: the step's requirement lines and Add a requirement. */
function StepProve({ program, step, onApplied }: { program: Program; step: ProgramStep; onApplied(next: Program | null): void }) {
  const [adding, setAdding] = useState(false);
  const rows = step.requirements ?? [];
  const canAdd = Boolean(step.editable?.includes("requirements")) && !program.closed_at;
  if (!rows.length && !canAdd) return null;
  return (
    <section className="pg-sf-prove" aria-label="What it must prove" data-testid="programs-step-requirements">
      <h4 className="pg-sf-cap">What it must prove</h4>
      {rows.length || adding ? (
        <ul className="pg-reqs">
          {rows.map((row) => <RequirementRow key={row.id} program={program} row={row} onApplied={onApplied} />)}
          {adding ? <AddRequirementRow program={program} onApplied={onApplied} defaultScope={step.id} /> : null}
        </ul>
      ) : null}
      {canAdd ? (
        <span className="pg-sf-prove-verbs">
          <Button dense variant="ghost" aria-expanded={adding} onClick={() => setAdding((now) => !now)} data-testid="programs-step-add-requirement">
            {adding ? "Not now" : "Add a requirement"}
          </Button>
        </span>
      ) : null}
    </section>
  );
}

export function StepFold({ program, step, onApplied }: {
  program: Program; step: ProgramStep; onApplied(next: Program | null): void;
}) {
  const parts = partsOf(program, step);
  const [part, setPart] = useState<Part | "">(() => firstPart(step, parts));
  const [inserting, setInserting] = useState(false);
  const [busy, setBusy] = useState("");
  const [failed, setFailed] = useState<Failure>(null);
  const [handing, setHanding] = useState<DOMRect | null>(null);
  const handOpener = useRef<HTMLButtonElement | null>(null);
  const amendRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    setPart(firstPart(step, partsOf(program, step)));
    setInserting(false);
    setFailed(null);
  }, [step.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const shown: Part | "" = part && parts.includes(part) ? part : "";
  const planned = isPlanned(step) && Boolean(step.editable?.includes("position"));
  const finished = ["merged", "done", "parked", "failed"].includes(step.state);
  const started = !isPlanned(step) && !finished;

  const move = async (dir: -1 | 1) => {
    setBusy(dir < 0 ? "up" : "down");
    setFailed(null);
    try {
      const answer = await moveStep(program, step, dir);
      if ("refused" in answer) setFailed({ words: `${answer.refused} · It keeps its place`, title: answer.refused });
      else onApplied(answer.program);
    } catch (cause) {
      setFailed(plainFail(`Step ${step.ordinal} did not move`, cause, "The order is as it was", "Try again"));
    } finally {
      setBusy("");
    }
  };
  const handTo = async (profile: string) => {
    setBusy("hand");
    setFailed(null);
    try {
      onApplied(await handoff(program.id, step.id, { profile, engine: null }));
    } catch (cause) {
      setFailed(plainFail(`Step ${step.ordinal} was not handed off`, cause, "The agent goes on", "Try again"));
    } finally {
      setBusy("");
    }
  };
  let body = null;
  if (shown === "brief") {
    body = planned || (isPlanned(step) && step.editable?.includes("brief"))
      ? <PlannedBrief program={program} step={step} onApplied={onApplied} onFailed={setFailed} />
      : <StartedBrief program={program} step={step} onApplied={onApplied} onFailed={setFailed} amendRef={amendRef} />;
  } else if (shown === "gate") {
    body = <GateFacts step={step} />;
  } else if (shown === "findings") {
    body = (
      <ul className="pg-sf-findings" data-testid="programs-step-findings">
        {step.findings.map((finding) => (
          <li key={finding.id} className="pg-sf-finding">
            <DotWord tone={finding.decision ? "idle" : FINDING_TONE[String(finding.level)] ?? "idle"}>
              {finding.level ? `${String(finding.level).charAt(0).toUpperCase()}${String(finding.level).slice(1)}` : "Finding"}
            </DotWord>
            <span className="pg-sf-finding-text" title={finding.text}>{finding.text}</span>
            {finding.decision ? <span className="pg-sf-finding-decision">{finding.decision.replace("_", " ")}</span> : null}
          </li>
        ))}
      </ul>
    );
  } else if (shown === "handoffs") {
    body = <ul className="pg-ledger">{(step.handoffs ?? []).map((entry, index) => <HandoffLine key={`${entry.at}-${index}`} id={`${step.id}-${index}`} step={step} entry={entry} />)}</ul>;
  } else if (shown === "ledger") {
    body = <StepLedger program={program} step={step} onStarted={onApplied} />;
  }

  const verbs = planned ? (
    <>
      <Button dense variant="secondary" loading={busy === "up"} disabled={Boolean(busy) || !moveTarget(program, step, -1)}
        title="Alt+↑" onClick={() => void move(-1)} data-testid="programs-step-up">Move up</Button>
      <Button dense variant="secondary" loading={busy === "down"} disabled={Boolean(busy) || !moveTarget(program, step, 1)}
        title="Alt+↓" onClick={() => void move(1)} data-testid="programs-step-down">Move down</Button>
      <Button dense variant="secondary" disabled={Boolean(busy)} aria-expanded={inserting} onClick={() => setInserting((now) => !now)}
        data-testid="programs-step-insert-before">Insert before</Button>
    </>
  ) : started ? (
    <>
      {step.editable?.includes("amend") ? (
        <Button dense variant="secondary" onClick={() => { setPart("brief"); window.setTimeout(() => amendRef.current?.focus(), 0); }}
          data-testid="programs-step-amend-open">Amend brief</Button>
      ) : null}
      {step.launch_id ? (
        <Button ref={handOpener} dense variant="secondary" loading={busy === "hand"} disabled={Boolean(busy)} aria-haspopup="menu"
          aria-expanded={Boolean(handing)} onClick={() => setHanding((now) => (now ? null : handOpener.current?.getBoundingClientRect() ?? null))}
          data-testid="programs-step-hand-off">Hand off</Button>
      ) : null}
    </>
  ) : null;

  return (
    <div className="pg-sf" data-testid="programs-step-fold" data-step={step.id} data-part={shown || undefined}>
      <StepProve program={program} step={step} onApplied={onApplied} />
      <StepStory step={step} />
      <div className="pg-sf-head">
        <FilterTokens label={`Step ${step.ordinal}`} value={shown} emptyLabel="Parts"
          onChange={(next) => setPart((now) => (now === next ? "" : next as Part))}
          options={parts.map((value) => ({ value, label: PART_WORDS[value] }))} />
        <span className="pg-sf-verbs">{verbs}</span>
      </div>
      {inserting ? <InsertRow program={program} step={step} onApplied={onApplied} onDone={() => setInserting(false)} /> : null}
      {failed ? <p className="pg-failure" role="status" title={failed.title} data-testid="programs-step-failure">{failed.words}</p> : null}
      {body ? <div className="pg-sf-body">{body}</div> : null}
      {handing ? (
        <WorkMenu label="Hand off" x={handing.left} y={handing.bottom} opener={handOpener.current} autoFocus
          returnFocus={() => handOpener.current?.focus()} onClose={() => setHanding(null)}
          entries={AGENTS.filter((row) => row.profile !== step.profile).map((row) => ({
            type: "item" as const, id: row.profile, label: `Hand to ${row.word}`, onSelect: () => void handTo(row.profile),
          }))} />
      ) : null}
    </div>
  );
}
