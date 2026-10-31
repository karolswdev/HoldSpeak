/* Programs PG-REQ (PROGRAMS-REQUIREMENTS-2026-10-31 §7, §9; canvas
 * programs-requirements-2026-10-31.html, direction A "the checklist").
 *
 * The Requirements board: a fold under the Your turn well, open while one
 * is Unmet or waits on his word, closed with its token ("5 of 5 met") when
 * all are met. One 32 px row per requirement, grouped The program (judged
 * after the last step) · Every step · Steps' own:
 *   R3 · DotWord(state) · the sentence · Token(kind) · where · proof · verbs
 * Where is "Step 5", "The program", or for an every-step one six small dots
 * (one per step, the station track's species) and "4 of 6 steps". The proof
 * is one press away: Open log (the log in a well under the row), Open shot
 * (the shot's own window), the reviewer's line in muted words, "You ·
 * 09:12". The verbs his state allows: Met / Unmet for his word, Send back /
 * Waive when Unmet. A press on the sentence opens a two-line well under the
 * row (its facts, the shot's thumbnail, Edit, Waive). Unmet and Waive ask
 * one line in place; no modal. The last row is Add requirement. */
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { apiBlob, apiFetch } from "../../lib/api";
import { DESK_APPLICATIONS } from "../applications";
import { useDesk } from "../store";
import { CheckGadget, CycleGadget, DotWord, EditInPlace, FoldGadget, StringGadget, SurfaceCode } from "../surface";
import { Token } from "../surface/Token";
import { plainFail } from "../surface/plainFailure";
import { addRequirement, decideRequirement, editRequirement, type RequirementChoice } from "./api";
import { KIND_WORDS, everyStepState, guessKind, requirementTone, requirementWord, type Tone } from "./model";
import type { Program, ProgramStep, Requirement, RequirementKind, RequirementState } from "./types";

type Failure = { words: string; title: string } | null;

function clock(at: string | null | undefined): string {
  const ms = Date.parse(String(at ?? ""));
  if (!Number.isFinite(ms)) return "";
  return new Date(ms).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
}

/** The sentence, with a command in backticks drawn as code. */
export function SentenceWords({ text }: { text: string }) {
  const parts = text.split(/(`[^`]+`)/);
  return (
    <>
      {parts.map((part, index) => part.startsWith("`") && part.endsWith("`") && part.length > 2
        ? <code key={index} className="pg-req-code">{part.slice(1, -1)}</code>
        : <span key={index}>{part}</span>)}
    </>
  );
}

function stateTone(state: RequirementState): Tone {
  return state === "met" ? "ok" : state === "unmet" ? "fail" : "idle";
}

/** Six small dots, one per step (the station track's species), each in
 *  its copy's state. `numbered` draws the step number beside each. */
export function StepDots({ row, numbered = false }: { row: Requirement; numbered?: boolean }) {
  return (
    <span className="pg-req-dots" data-numbered={numbered ? "" : undefined} aria-hidden={numbered ? undefined : true}>
      {(row.steps ?? []).map((copy) => (
        <span key={copy.step_id} className="pg-req-dot-cell" title={`Step ${copy.ordinal} · ${requirementWord({ state_word: copy.state.replace("_", " "), running: false })}`}>
          <span className="pg-req-dot" data-state={copy.state} data-tone={stateTone(copy.state)} />
          {numbered ? <span className="pg-req-dot-n">{copy.ordinal}</span> : null}
        </span>
      ))}
    </span>
  );
}

/** The image a Shot requirement's evidence holds, read through the hub's
 *  evidence route (the hub serves it to this desk only). */
export function useEvidenceImage(url: string | null | undefined): { src: string | null; failed: boolean } {
  const [state, setState] = useState<{ src: string | null; failed: boolean }>({ src: null, failed: false });
  useEffect(() => {
    if (!url) return;
    let alive = true;
    let made: string | null = null;
    apiBlob(url).then((blob) => {
      if (!alive) return;
      made = URL.createObjectURL(blob);
      setState({ src: made, failed: false });
    }).catch(() => { if (alive) setState({ src: null, failed: true }); });
    return () => {
      alive = false;
      if (made) URL.revokeObjectURL(made);
    };
  }, [url]);
  return state;
}

/** The shot's thumbnail (240 px wide): "how it is met" is a picture. */
export function EvidenceThumb({ row }: { row: Requirement }) {
  const image = useEvidenceImage(row.evidence.url);
  if (image.failed) return <DotWord tone="warn" data-testid="programs-req-thumb-missing">The shot is not there any more</DotWord>;
  if (!image.src) return <span className="pg-req-thumb" data-loading="" aria-hidden="true" />;
  return (
    <img className="pg-req-thumb" src={image.src} width={240} alt={`${row.label} shot: ${row.evidence.case ?? row.spec.case ?? ""} at ${row.evidence.width ?? row.spec.width ?? ""}`}
      data-testid="programs-req-thumb" />
  );
}

export function openShot(programId: string, requirementId: string): void {
  useDesk.getState().openPullout(`program-shot:${programId}:${requirementId}`);
}

/** Where a requirement applies: `The program`, `Step 5`, `4 of 6 steps`. */
function whereWords(row: Requirement, steps: readonly ProgramStep[]): string {
  if (row.scope === "program") return "The program";
  if (row.scope === "every_step") {
    const view = everyStepState(row);
    return view.total ? `${view.met} of ${view.total} steps` : "Every step";
  }
  const step = steps.find((candidate) => candidate.id === row.step_id);
  return step ? `Step ${step.ordinal}` : "A step";
}

/** The proof in muted words when it is not a verb (`“…” · round 1`, `You · 09:12`). */
function proofWords(row: Requirement): string {
  const evidence = row.evidence ?? {};
  if (row.state === "waived") return row.waived_reason ? `You · “${row.waived_reason}”` : "You";
  if (evidence.kind === "finding" && evidence.line) return `“${evidence.line}”${evidence.round ? ` · round ${evidence.round}` : ""}`;
  if (evidence.kind === "press") return evidence.line || "You";
  if (evidence.kind === "log" && !evidence.url && evidence.line) return evidence.line;
  if (row.scope === "program" && row.state === "not_yet") return "after the last step";
  return "";
}

type Ask = { choice: RequirementChoice; label: string; verb: string; needed: boolean } | null;

/** The line a press asks for (Unmet, Waive), in place under the row. */
function LineWell({ ask, busy, onSend, onCancel }: {
  ask: NonNullable<Ask>; busy: boolean; onSend(line: string): void; onCancel(): void;
}) {
  const [line, setLine] = useState("");
  return (
    <div className="pg-req-ask" data-testid="programs-req-ask" data-choice={ask.choice}>
      <span className="pg-req-ask-field">
        <StringGadget label={ask.label} value={line} onChange={setLine} placeholder={ask.label} autoFocus
          onKeyDown={(event) => { if (event.key === "Enter" && (line.trim() || !ask.needed)) onSend(line.trim()); if (event.key === "Escape") onCancel(); }} />
      </span>
      <Button dense variant="ghost" disabled={busy} onClick={onCancel} data-testid="programs-req-ask-cancel">Not now</Button>
      <Button dense variant="primary" loading={busy} disabled={busy || (ask.needed && !line.trim())} onClick={() => onSend(line.trim())}
        data-testid="programs-req-ask-send">{ask.verb}</Button>
    </div>
  );
}

function asked(choice: string): Ask {
  if (choice === "waive") return { choice: "waive", label: "Why you waive it", verb: "Waive", needed: true };
  if (choice === "unmet") return { choice: "unmet", label: "What is missing", verb: "Unmet", needed: false };
  return null;
}

/** One requirement row (32 px; two lines at 393). */
export function RequirementRow({ program, row, onApplied }: {
  program: Program; row: Requirement; onApplied(next: Program | null): void;
}) {
  const [open, setOpen] = useState(false);
  const [ask, setAsk] = useState<Ask>(null);
  const [log, setLog] = useState<{ text: string } | { failed: string } | null>(null);
  const [busy, setBusy] = useState("");
  const [failed, setFailed] = useState<Failure>(null);
  const every = row.scope === "every_step" ? everyStepState(row) : null;
  const state = every?.state ?? row.state;
  const word = every ? every.word : requirementWord(row);
  const tone = every ? (state === "met" ? "ok" : state === "unmet" ? "fail" : requirementTone(row)) : requirementTone(row);
  const his = tone === "ask";
  const evidence = row.evidence ?? {};
  const choices = new Set(row.choices ?? []);

  const press = async (choice: RequirementChoice, line?: string) => {
    setBusy(choice);
    setFailed(null);
    try {
      onApplied(await decideRequirement(program.id, row.id, choice, line));
      setAsk(null);
    } catch (cause) {
      setFailed(plainFail(choice === "waive" ? `${row.label} was not waived` : `Your answer on ${row.label} did not reach the program`,
        cause, `${row.label} is unchanged`, "Try again"));
    } finally {
      setBusy("");
    }
  };
  const choose = (choice: string) => {
    const needs = asked(choice);
    if (needs) setAsk((now) => (now?.choice === needs.choice ? null : needs));
    else void press(choice as RequirementChoice);
  };
  const openLog = async () => {
    if (log) { setLog(null); return; }
    if (!evidence.url) return;
    try {
      const text = await apiFetch<string>(evidence.url, { headers: { Accept: "text/plain" } });
      setLog({ text: typeof text === "string" ? text : JSON.stringify(text, null, 2) });
    } catch (cause) {
      setLog({ failed: plainFail("The log did not open", cause, "Nothing changed", "Try again").words });
    }
  };

  // The verbs on the row: his word, or Send back / Waive when Unmet.
  const verbs: { choice: string; word: string; primary?: boolean }[] = [];
  if (row.kind === "word" && row.state === "not_yet" && choices.has("met")) {
    verbs.push({ choice: "met", word: "Met", primary: true }, { choice: "unmet", word: "Unmet" });
  } else if (row.state === "unmet") {
    if (choices.has("send_back")) verbs.push({ choice: "send_back", word: "Send back", primary: true });
    if (choices.has("waive")) verbs.push({ choice: "waive", word: "Waive", primary: !choices.has("send_back") });
  }
  const waiveInWell = choices.has("waive") && !verbs.some((verb) => verb.choice === "waive");
  const proof = proofWords(row);

  return (
    <li className="pg-req" data-state={state} data-tone={tone} data-kind={row.kind} data-scope={row.scope}
      data-selected={open ? "" : undefined} data-his={his ? "" : undefined} data-testid="programs-req" data-req={row.id} data-label={row.label}>
      <div className="pg-req-row">
        <span className="pg-req-id">{row.label}</span>
        <span className="pg-req-state">
          <DotWord tone={tone} live={row.running || his} className="pg-req-word" data-testid="programs-req-state">{word}</DotWord>
        </span>
        <Button variant="chrome" className="pg-req-text" aria-expanded={open} onClick={() => setOpen((now) => !now)}
          title={row.text.replace(/`/g, "")} data-testid="programs-req-select">
          <SentenceWords text={row.text} />
        </Button>
        <span className="pg-req-kind"><Token className="surface-token pg-kind" data-kind={row.kind}>{row.kind_word || KIND_WORDS[row.kind]}</Token></span>
        <span className="pg-req-where" data-testid="programs-req-where">
          {every ? <StepDots row={row} /> : null}
          <span>{whereWords(row, program.steps)}</span>
        </span>
        <span className="pg-req-proof" data-testid="programs-req-proof">
          {evidence.kind === "log" && evidence.url ? (
            <Button dense variant="secondary" aria-expanded={Boolean(log)} onClick={() => void openLog()} title={evidence.line || undefined}
              data-testid="programs-req-open-log">Open log</Button>
          ) : null}
          {evidence.kind === "shot" && evidence.url ? (
            <Button dense variant="secondary" onClick={() => openShot(program.id, row.id)} title={evidence.line || undefined}
              data-testid="programs-req-open-shot">Open shot</Button>
          ) : null}
          {proof ? <span className="pg-req-proof-words" title={proof}>{proof}</span> : null}
        </span>
        <span className="pg-req-verbs">
          {verbs.map((verb) => (
            <Button key={verb.choice} dense variant={verb.primary ? "primary" : "secondary"} loading={busy === verb.choice}
              disabled={Boolean(busy)} aria-pressed={ask?.choice === verb.choice ? true : undefined}
              onClick={() => choose(verb.choice)} data-testid={`programs-req-${verb.choice.replace("_", "-")}`}>
              {verb.word}
            </Button>
          ))}
        </span>
      </div>
      {ask ? <LineWell ask={ask} busy={Boolean(busy)} onSend={(line) => void press(ask.choice, line || undefined)} onCancel={() => setAsk(null)} /> : null}
      {log ? (
        <div className="pg-req-log" data-testid="programs-req-log">
          {"text" in log ? <SurfaceCode>{log.text.split("\n").slice(-40).join("\n")}</SurfaceCode> : <DotWord tone="warn">{log.failed}</DotWord>}
        </div>
      ) : null}
      {open ? (
        <RequirementWell program={program} row={row} busy={Boolean(busy)} onApplied={onApplied} onFailed={setFailed}
          waive={waiveInWell ? () => choose("waive") : undefined} />
      ) : null}
      {failed ? <p className="pg-failure" role="status" title={failed.title} data-testid="programs-req-failure">{failed.words}</p> : null}
    </li>
  );
}

/** The two-line well under a selected row: its facts, the shot, Edit. */
function RequirementWell({ program, row, busy, onApplied, onFailed, waive }: {
  program: Program; row: Requirement; busy: boolean; onApplied(next: Program | null): void; onFailed(failure: Failure): void;
  waive?: () => void;
}) {
  const evidence = row.evidence ?? {};
  const commit = evidence.commit ?? row.judged_commit;
  const edit = async (text: string) => {
    if (text === row.text) return;
    onFailed(null);
    try {
      onApplied(await editRequirement(program.id, row.id, { text }));
    } catch (cause) {
      onFailed(plainFail(`${row.label} was not changed`, cause, "The sentence is as it was", "Try again"));
    }
  };
  return (
    <div className="pg-req-well" data-testid="programs-req-well">
      <dl className="pg-req-facts">
        <dt>Requirement</dt>
        <dd className="pg-req-edit">
          {row.state === "waived" || program.closed_at ? <SentenceWords text={row.text} />
            : <EditInPlace label={`${row.label} sentence`} value={row.text} onCommit={edit} />}
        </dd>
        {row.spec.command ? (<><dt>Command</dt><dd><SurfaceCode>{row.spec.command}</SurfaceCode></dd></>) : null}
        {row.kind === "shot" && (row.spec.case || evidence.case) ? (
          <><dt>Window</dt><dd>{`${evidence.case ?? row.spec.case} at ${evidence.width ?? row.spec.width}`}</dd></>
        ) : null}
        {row.scope === "every_step" ? (<><dt>Steps</dt><dd><StepDots row={row} numbered /></dd></>) : null}
        {commit ? (
          <>
            <dt>Judged on</dt>
            <dd>
              <code className="pg-ref" title={commit}>{commit.slice(0, 7)}</code>
              {[evidence.by && evidence.by !== "owner" && evidence.by !== "engine" ? evidence.by : "", evidence.round ? `round ${evidence.round}` : "", clock(evidence.at)]
                .filter(Boolean).map((part) => <span key={part} className="pg-req-fact-sub"> · {part}</span>)}
            </dd>
          </>
        ) : null}
        {evidence.line && evidence.kind !== "press" ? (<><dt>{evidence.kind === "finding" ? "The reviewer" : "Result"}</dt><dd>{evidence.line}</dd></>) : null}
        {row.rounds ? (<><dt>Rounds</dt><dd>{row.rounds}</dd></>) : null}
        {row.kind === "shot" && evidence.url ? (<><dt>Shot</dt><dd><EvidenceThumb row={row} /></dd></>) : null}
      </dl>
      {waive ? (
        <span className="pg-req-well-verbs">
          <Button dense variant="secondary" disabled={busy} onClick={waive} data-testid="programs-req-waive">Waive</Button>
        </span>
      ) : null}
    </div>
  );
}

/** The cases a Shot can render: the desk's windows (the sweep's cases) and
 *  a Program's own window. */
function shotCases(): { value: string; label: string }[] {
  const seen = new Set<string>();
  const out: { value: string; label: string }[] = [];
  for (const app of DESK_APPLICATIONS) {
    if (app.parked || !app.windowId?.startsWith("surface-")) continue;
    const value = app.windowId.slice("surface-".length);
    if (seen.has(value)) continue;
    seen.add(value);
    out.push({ value, label: app.label });
  }
  out.push({ value: "program", label: "A program" });
  return out;
}

const KINDS: { value: RequirementKind; label: string }[] = [
  { value: "check", label: "Check" }, { value: "review", label: "Review" }, { value: "shot", label: "Shot" }, { value: "word", label: "Your word" },
];
const WIDTHS = [{ value: "393", label: "393" }, { value: "1440", label: "1440" }];

/** Add requirement (§9, the Drafting row's species): one sentence (with its
 *  mic); the kind follows the rule as he types until he picks one; where;
 *  the kind's one field; Required; Add. A kind this repository cannot prove
 *  withholds Add and says why. */
export function AddRequirementRow({ program, onApplied, defaultScope = "every" }: {
  program: Program; onApplied(next: Program | null): void; defaultScope?: string;
}) {
  const [text, setText] = useState("");
  const [kind, setKind] = useState<RequirementKind>("review");
  const [kindPicked, setKindPicked] = useState(false);
  const [scope, setScope] = useState(defaultScope);
  const [command, setCommand] = useState("");
  const [commandPicked, setCommandPicked] = useState(false);
  const [shot, setShot] = useState<{ case: string; width: string }>({ case: "people", width: "393" });
  const [required, setRequired] = useState(true);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState<Failure>(null);
  const cases = useMemo(shotCases, []);
  const input = useRef<HTMLInputElement | null>(null);
  useEffect(() => setScope(defaultScope), [defaultScope]);

  const type = (next: string) => {
    setText(next);
    const guess = guessKind(next);
    if (!kindPicked) setKind(guess.kind);
    if (guess.command && !commandPicked) setCommand(guess.command);
    if (guess.case && guess.width) setShot({ case: guess.case, width: String(guess.width) });
  };
  const open = program.steps.filter((step) => !step.race_of && !(step.frozen && "requirements" in step.frozen));
  const scopes = [
    { value: "program", label: "The program" },
    { value: "every", label: "Every step" },
    ...open.map((step) => ({ value: step.id, label: `Step ${step.ordinal}` })),
  ];
  const prove = program.can_prove;
  const cannot = prove && prove[kind] === false
    ? (kind === "shot" ? prove.shot_reason || "No shot command in this repository" : "This repository cannot prove it")
    : "";
  const next = Math.max(0, ...(program.requirements ?? []).map((row) => row.ordinal),
    ...program.steps.flatMap((step) => (step.requirements ?? []).map((row) => row.ordinal))) + 1;
  const ready = Boolean(text.trim()) && !cannot && (kind !== "check" || Boolean(command.trim()));

  const add = async () => {
    if (!ready) return;
    setBusy(true);
    setFailed(null);
    const spec = kind === "check" ? { command: command.trim() } : kind === "shot" ? { case: shot.case, width: Number(shot.width) } : undefined;
    try {
      onApplied(await addRequirement(program.id, {
        text: text.trim(), kind, required,
        ...(scope === "every" ? { each_step: true } : scope === "program" ? {} : { step_id: scope }),
        ...(spec ? { spec } : {}),
      }));
      setText(""); setKindPicked(false); setKind("review"); setCommand(""); setCommandPicked(false);
      input.current?.focus();
    } catch (cause) {
      setFailed(plainFail("The requirement was not added", cause, "Your sentence is kept", "Try again"));
    } finally {
      setBusy(false);
    }
  };

  let field: ReactNode = null;
  if (kind === "check") {
    field = (
      <span className="pg-req-add-command">
        <StringGadget label="Command" value={command} mic={false} placeholder="Command"
          onChange={(value) => { setCommand(value); setCommandPicked(true); }} />
      </span>
    );
  } else if (kind === "shot") {
    field = (
      <span className="pg-req-add-shot">
        <CycleGadget label="Window" value={shot.case} options={cases} onChange={(value) => setShot((now) => ({ ...now, case: value }))} />
        <CycleGadget label="Width" value={shot.width} options={WIDTHS} onChange={(value) => setShot((now) => ({ ...now, width: value }))} />
      </span>
    );
  }
  return (
    <li className="pg-req-add" data-testid="programs-req-add">
      <div className="pg-req-add-row">
        <span className="pg-req-id">{`R${next}`}</span>
        <span className="pg-req-add-text">
          <StringGadget label="Add a requirement" value={text} onChange={type} placeholder="Add a requirement" inputRef={input}
            onKeyDown={(event) => { if (event.key === "Enter") void add(); }} />
        </span>
        <span className="pg-req-add-kind">
          <CycleGadget label="Kind" value={kind} options={KINDS} onChange={(value) => { setKind(value as RequirementKind); setKindPicked(true); }} />
        </span>
        <span className="pg-req-add-scope">
          <CycleGadget label="Where" value={scope} options={scopes} onChange={setScope} />
        </span>
        <span className="pg-req-add-field">{field}</span>
        <span className="pg-req-add-required">
          <CheckGadget variant="token" label="Required" checked={required} onChange={setRequired} />
        </span>
        <span className="pg-req-add-verb">
          <Button dense variant="primary" loading={busy} disabled={busy || !ready} onClick={() => void add()} data-testid="programs-req-add-verb">Add</Button>
        </span>
      </div>
      {cannot ? <div className="pg-req-add-why"><DotWord tone="warn" data-testid="programs-req-add-why">{cannot}</DotWord></div> : null}
      {failed ? <p className="pg-failure" role="status" title={failed.title} data-testid="programs-req-add-failure">{failed.words}</p> : null}
    </li>
  );
}

/** The required ones, Program-wide, as the fold's token (`6 of 13 met · 1
 *  waits on you`); a count of zero is never drawn. */
export function boardToken(program: Program): string {
  const met = program.requirements_met;
  if (!met?.total) return "";
  const parts = [met.met || met.unmet ? `${met.met} of ${met.total} met` : `${met.total} ${met.total === 1 ? "requirement" : "requirements"}`];
  if (met.his) parts.push(`${met.his} ${met.his === 1 ? "waits" : "wait"} on you`);
  return parts.join(" · ");
}

/** The Requirements board (direction A, the checklist). */
export function RequirementsBoard({ program, onApplied }: { program: Program; onApplied(next: Program | null): void }) {
  const own = (program.requirements ?? []).filter((row) => row.scope === "program");
  const every = (program.requirements ?? []).filter((row) => row.scope === "every_step");
  const steps = program.steps.filter((step) => !step.race_of);
  const stepsOwn = steps.flatMap((step) => (step.requirements ?? []).filter((row) => row.scope === "step"));
  const total = own.length + every.length + stepsOwn.length;
  const met = program.requirements_met;
  const wants = Boolean(met && (met.unmet || met.his));
  const [open, setOpen] = useState(wants || !total);
  const was = useRef(wants);
  useEffect(() => {
    if (wants && !was.current) setOpen(true);
    was.current = wants;
  }, [wants]);
  const finished = program.state === "done" || Boolean(program.closed_at);
  if (!total && finished) return null;
  const band = (key: string, word: string, sub: string | null, rows: Requirement[]) => rows.length ? (
    <section key={key} className="kit-listday pg-req-band" aria-label={word} data-band={key}>
      <h4 className="kit-listday-label">{word}{sub ? <span className="pg-fold-sub">{` · ${sub}`}</span> : null}</h4>
      <ul className="pg-reqs">
        {rows.map((row) => <RequirementRow key={row.id} program={program} row={row} onApplied={onApplied} />)}
      </ul>
    </section>
  ) : null;
  const token = boardToken(program);
  return (
    <FoldGadget className="pg-req-board" title="Requirements" token={token || undefined} open={open} onToggle={setOpen}>
      <div className="pg-req-list" data-testid="programs-requirements">
        {total ? (
          <div className="pg-req-head" aria-hidden="true">
            <span /><span>State</span><span>Requirement</span><span>Kind</span><span>Where</span><span>Proof</span><span />
          </div>
        ) : null}
        {band("program", "The program", "judged after the last step", own)}
        {band("every", "Every step", null, every)}
        {band("own", "Steps' own", null, stepsOwn)}
        {finished ? null : <ul className="pg-reqs"><AddRequirementRow program={program} onApplied={onApplied} /></ul>}
      </div>
    </FoldGadget>
  );
}
