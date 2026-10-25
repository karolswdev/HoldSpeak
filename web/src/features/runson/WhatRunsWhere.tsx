// Betterment E5 — What runs where (DESIGN §4, RECIPE E5).
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
import { PrefSection } from "../../pages/cores/settingsWindow";
import type { RowEditor } from "./api";
import { agentChip, enginePlace, hostLabel, type BoardEngine } from "./model";
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
const chipOf = engineChip;

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

/** Window grammar (2026-10-24), the list + inspector shape: the
 *  assignment editor is a label/control grid under the engine list (one
 *  row per job: its name, then its chooser). `selected` is the engine
 *  selected in the list: a row it runs says so in the accent ink. */
export function WhatRunsWhere({ ctrl, selected }: { ctrl: RunsOnController; selected?: string | null }) {
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
  const shown = WHAT_ROWS.filter((row) => more || row.lead || own(row));
  const hidden = WHAT_ROWS.length - shown.length;

  return (
    <div className="runson-what" data-testid="runson-what">
      <PrefSection id="runson-what" label="What runs where">
      <ul className="runson-what-list">
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
          return (
            <li key={row.id} className="runson-what-row" data-testid={`runson-what-${row.id}`}
              data-runs-selected={selected && editor?.effective?.profileId === selected ? "" : undefined}>
              <span className="runson-what-job">{row.name}</span>
              <span className="runson-what-engine">
                {raw === "failed" ? (
                  <DotWord tone="fail">Not read</DotWord>
                ) : (
                  <Button
                    dense
                    variant="secondary"
                    className="runson-what-pick"
                    aria-expanded={picking}
                    aria-label={`${row.name}: ${shownName(row, editor, nameOf)}`}
                    disabled={!editor || ctrl.busy}
                    data-testid={`runson-what-pick-${row.id}`}
                    onClick={() => setOpen(picking ? null : row.id)}
                  >
                    {!editor ? (
                      <DotWord className="runson-what-name">{READING}</DotWord>
                    ) : shownName(row, editor, nameOf) === NOT_ASSIGNED ? (
                      <DotWord className="runson-what-name">{NOT_ASSIGNED}</DotWord>
                    ) : (
                      <span className="runson-what-name">{shownName(row, editor, nameOf)}</span>
                    )}
                    <span className="runson-what-caret" aria-hidden="true">▾</span>
                  </Button>
                )}
                {editor?.effective ? chipOf(effective) : null}
                {canTry ? (
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
                ) : null}
              </span>
              {picking && editor ? (
                <ul className="runson-what-options" data-testid={`runson-what-options-${row.id}`}>
                  {row.id !== EVERYTHING_ELSE ? (
                    <li>
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
                        {chipOf(engine)}
                        {candidate.status === "savable_with_repair" ? <DotWord tone="warn">Limited</DotWord> : null}
                      </li>
                    );
                  })}
                  {!editor.candidates.length ? (
                    <li data-testid={`runson-what-none-${row.id}`}><DotWord>No engine can do this job</DotWord></li>
                  ) : null}
                </ul>
              ) : null}
              {result ? (
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
              ) : null}
            </li>
          );
        })}
      </ul>
      {hidden > 0 || more ? (
        <Button dense variant="ghost" className="runson-what-more" aria-expanded={more} data-testid="runson-what-more" onClick={() => setMore(!more)}>
          {more ? "Fewer jobs" : `${hidden} more jobs`}
        </Button>
      ) : null}
      </PrefSection>
    </div>
  );
}
