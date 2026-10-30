// Betterment E5 — What runs where (DESIGN §4, RECIPE E5); since the
// Engines grammar canvas (2026-10-30, direction B) the "What HoldSpeak does"
// list beside the engines.
//
// One row for each job, with a picker of the engines that can serve it (the
// hub's assignment editor decides: only compatible candidates come back).
// A press applies at once; Undo is in the window's foot. Try it runs the
// hub's sample on the row's engine and shows the answer, or the error in
// words, under the row. A row that has no engine of its own reads
// "Everything else". It replaces the drag switchboard (DECISIONS #8), which
// is parked behind Builder tools.

import { useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { EgressChip, SurfaceWell } from "../../desk/surface";
import { DotWord } from "../../desk/surface/kit";
import { ListDay, ListRow, type ListRowState } from "../../desk/surface/objects/ListView";
import { spriteUrl } from "../../desk/sprites";
import type { RowEditor } from "./api";
import { agentChip, enginePlace, hostLabel, notAnswering, type BoardEngine } from "./model";
import type { RunsOnController } from "./useRunsOn";
import { EVERYTHING_ELSE, WHAT_ROWS, type WhatRow } from "./whatRows";

/** An egress chip's words in sentence case (window grammar: never a caps
 *  chip): a host in lower case, a vendor with one capital, `LAN` kept. */
export function chipWords(label: string): string {
  return label
    .split(" · ")
    .map((part) => {
      const word = part.trim();
      if (word === "LAN" || word === "THIS DEVICE") return word === "LAN" ? word : "This device";
      if (/[.:]/.test(word)) return word.toLowerCase();
      return word ? word[0].toUpperCase() + word.slice(1).toLowerCase() : word;
    })
    .join(" · ");
}

/** The egress chip for one engine, in sentence case. */
export function engineChip(engine: BoardEngine | undefined): ReactNode {
  if (!engine) return null;
  if (engine.vendor) {
    const chip = agentChip(engine.vendor, engine.vendorScope);
    return <EgressChip label={chipWords(chip.label)} scope={chip.scope} />;
  }
  const place = enginePlace(engine).place;
  return <EgressChip label={chipWords(hostLabel(engine))} scope={place === "cloud" ? "cloud" : "local"} />;
}

export const NOT_ASSIGNED = "Not assigned";
/** Before the row's read lands: a quiet word, never a bare ellipsis (the
 *  sweep reads an ellipsis as clipped text). */
export const READING = "Reading";

/** The words a row's picker shows: its own engine, or where it follows. */
function shownName(row: WhatRow, editor: RowEditor | undefined, nameOf: (id: string, label: string) => string): string {
  if (!editor) return READING;
  if (editor.own) return nameOf(editor.own.profileId, editor.own.label);
  // Owner, 2026-08-31 (lost in Settings > Models): a row with no engine
  // says "Not assigned", never a blank and never a vaguer word.
  if (row.id === EVERYTHING_ELSE) return NOT_ASSIGNED;
  if (!editor.effective) return NOT_ASSIGNED;
  if (editor.effective.inheritedFrom === "global") return "Everything else";
  return nameOf(editor.effective.profileId, editor.effective.label);
}

/** The engine's 20 px sprite: an agent wears its own, every other engine
 *  the cartridge. */
export function engineSprite(engine: BoardEngine | undefined): string {
  if (engine?.kind === "agent") return spriteUrl("coder", engine.key, "rest", engine.agentPreset ?? engine.name, 20);
  return spriteUrl("model", engine?.key ?? "engine", "rest", null, 20);
}

/** Engines grammar (2026-10-30, canvas direction B): the jobs, one 32 px
 *  row each, beside the engines. A row names its engine in its chooser (a
 *  library Button; a press unfolds the choices in place, no modal) and says
 *  a state only when it changes what he does (Not answering, Not read);
 *  an unassigned job's chooser says Not assigned.
 *  A press on the row selects the job; its engine's row lights in the other
 *  list (`onSelect`), and an engine selected there lights the jobs it runs
 *  (`lit`). No host chip on a row (UX-CANON A.9): the address is in the
 *  engine's own fold. */
export function WhatRunsWhere({
  ctrl,
  selected,
  lit,
  onSelect,
}: {
  ctrl: RunsOnController;
  /** The selected job's row id. */
  selected?: string | null;
  /** The profile id of the engine selected in the engines list. */
  lit?: string | null;
  onSelect?: (job: string | null, profileId: string | null) => void;
}) {
  const [open, setOpen] = useState<string | null>(null);
  const [more, setMore] = useState(false);
  // The host (RunsOnCore) reads the rows once the roster is in; a write
  // reads them again.
  const { editors } = ctrl.what;
  const engineOf = (profileId: string) => ctrl.engines.find((e) => e.profileId === profileId);
  const nameOf = (profileId: string, label: string) => engineOf(profileId)?.name || label;

  // Everything else is text work: a speech engine is offered on its own row.
  const speechEditor = editors.speech;
  const speechIds = new Set(
    speechEditor && speechEditor !== "failed" ? speechEditor.candidates.map((c) => c.profileId) : [],
  );
  const own = (row: WhatRow) => {
    const editor = editors[row.id];
    return Boolean(editor && editor !== "failed" && editor.own);
  };
  const shown = WHAT_ROWS.filter((row) => more || row.lead || own(row) || row.id === selected);
  const hidden = WHAT_ROWS.length - shown.length;

  return (
    <ListDay label="What HoldSpeak does" data-testid="runson-what">
      {shown.map((row) => {
        const raw = editors[row.id];
        const editor = raw === "failed" ? undefined : raw;
        const picking = open === row.id;
        const result = ctrl.results[`what:${row.id}`];
        const effective = editor?.effective ? engineOf(editor.effective.profileId) : undefined;
        // Everything else tries the Answers sample, so only while Answers
        // follows it (else the sample would run on Answers' own engine).
        const answers = editors.answers;
        const followsDefault = row.id !== EVERYTHING_ELSE
          || Boolean(answers && answers !== "failed" && answers.effective?.inheritedFrom === "global");
        const canTry = Boolean(row.probe && editor?.effective && followsDefault);
        const shownWord = shownName(row, editor, nameOf);
        // A row that follows Everything else names the engine it lands on.
        const follows = editor && !editor.own && editor.effective && row.id !== EVERYTHING_ELSE
          ? nameOf(editor.effective.profileId, editor.effective.label)
          : null;
        // W1-TRUTH: a job on an engine whose server did not answer says so.
        const state: ListRowState | null = raw === "failed"
          ? { word: "Not read", tone: "fail" }
          : editor?.effective && notAnswering(effective)
            ? { word: "Not answering", tone: "fail", testId: `runson-what-down-${row.id}` }
            : null;
        const picker = raw === "failed" ? null : (
          <Button
            dense
            variant="secondary"
            className="runson-what-pick"
            aria-expanded={picking}
            aria-label={`${row.name}: ${shownWord}`}
            disabled={!editor || ctrl.busy}
            data-testid={`runson-what-pick-${row.id}`}
            onClick={() => setOpen(picking ? null : row.id)}
          >
            <span className="runson-what-name">{shownWord}</span>
            <span className="runson-what-caret" aria-hidden="true">▾</span>
          </Button>
        );
        const tryVerb = canTry ? (
          <Button
            dense
            variant="ghost"
            loading={ctrl.trying?.job === `what:${row.id}`}
            disabled={Boolean(ctrl.trying && ctrl.trying.job !== `what:${row.id}`)}
            data-testid={`runson-what-try-${row.id}`}
            onClick={() => void ctrl.what.tryRow(row.id)}
          >
            Try it
          </Button>
        ) : null;
        const options = picking && editor ? (
          <ul className="runson-what-options" data-testid={`runson-what-options-${row.id}`}>
            {row.id !== EVERYTHING_ELSE ? (
              <li className="runson-what-option">
                <Button
                  dense
                  variant={editor.own ? "ghost" : "primary"}
                  aria-pressed={!editor.own}
                  data-testid={`runson-what-option-${row.id}-default`}
                  onClick={() => {
                    setOpen(null);
                    if (editor.own) void ctrl.what.set(row.id, null);
                  }}
                >
                  {/* Betterment setup ST1 (FOLLOWUPS ST0/E5): speech
                      never takes the default (a chat engine); with no
                      row of its own it has no engine. */}
                  {row.id === "speech" ? "No engine" : "Everything else"}
                </Button>
              </li>
            ) : null}
            {editor.candidates.filter((candidate) => row.id !== EVERYTHING_ELSE || !speechIds.has(candidate.profileId)).map((candidate) => {
              const engine = engineOf(candidate.profileId);
              const current = editor.own?.profileId === candidate.profileId;
              return (
                <li key={candidate.profileId} className="runson-what-option">
                  <img className="runson-what-glyph" src={engineSprite(engine)} alt="" width={20} height={20} draggable={false} />
                  <Button
                    dense
                    variant={current ? "primary" : "ghost"}
                    aria-pressed={current}
                    data-testid={`runson-what-option-${row.id}-${candidate.profileId}`}
                    onClick={() => {
                      setOpen(null);
                      if (!current) void ctrl.what.set(row.id, candidate.profileId);
                    }}
                  >
                    {nameOf(candidate.profileId, candidate.label)}
                  </Button>
                  {notAnswering(engine) ? <DotWord tone="fail">Not answering</DotWord> : null}
                  {candidate.status === "savable_with_repair" ? <DotWord tone="warn">Limited</DotWord> : null}
                </li>
              );
            })}
            {!editor.candidates.length ? (
              <li data-testid={`runson-what-none-${row.id}`}><DotWord>No engine can do this job</DotWord></li>
            ) : null}
          </ul>
        ) : null;
        const answer = result ? (
          <span className="runson-trial-result runson-what-result" data-tone={result.tone === "ok" ? undefined : result.tone}>
            <span role="status" aria-live="polite" aria-busy={result.tone === "busy" || undefined} data-testid={`runson-what-state-${row.id}`}>
              {result.tokens.join(" · ")}
            </span>
            {result.sampleInput || result.sampleOutput ? (
              <SurfaceWell>
                {result.sampleInput ? <span className="runson-trial-sample"><span className="runson-trial-caption">Sample</span><span>{result.sampleInput}</span></span> : null}
                {result.sampleOutput ? <span className="runson-trial-sample"><span className="runson-trial-caption">Result</span><span data-testid={`runson-what-output-${row.id}`}>{result.sampleOutput}</span></span> : null}
              </SurfaceWell>
            ) : null}
          </span>
        ) : null;
        return (
          <ListRow
            key={row.id}
            data-testid={`runson-what-${row.id}`}
            name={row.name}
            meta={follows ? `On ${follows}` : undefined}
            onOpen={() => onSelect?.(selected === row.id ? null : row.id, editor?.effective?.profileId ?? null)}
            openLabel={row.name}
            openTestId={`runson-what-open-${row.id}`}
            selected={selected === row.id}
            lit={Boolean(lit && editor?.effective?.profileId === lit)}
            state={state}
            verbs={<>{picker}{tryVerb}</>}
            fold={options || answer ? <>{options}{answer}</> : undefined}
          />
        );
      })}
      {hidden > 0 || more ? (
        <li className="runson-what-more-row">
          <Button dense variant="ghost" className="runson-what-more" aria-expanded={more} data-testid="runson-what-more" onClick={() => setMore(!more)}>
            {more ? "Fewer jobs" : `${hidden} more jobs`}
          </Button>
        </li>
      ) : null}
    </ListDay>
  );
}
