/* Programs: the shaping bar (PROGRAM-LANGUAGE-2026-10-31 §4, §9.2, §9.6,
 * §14; LANG4; canvas program-language-2026-10-31, direction S-A "the bar
 * and the well").
 *
 * One row under the Program toolbar: a StringGadget "Change the program"
 * with its mic (the kit's one mic authority for this window) and the
 * library Button Shape (Return sends). The hub sends the sentence and the
 * Program's text to the planning engine in one call and answers the change
 * rows (POST …/shape); the rows open in the window's change well with the
 * source "sentence", Apply and Not this as for a typed text. Nothing
 * applies silently: below YOLO every row waits for Apply; at YOLO the hub
 * lands the allowed rows at once and the ShapedWell says what landed, with
 * Overturn. A row that lowers the bar waits for its own press at every
 * level.
 *
 * While the engine reads, the bar keeps the sentence, a breathing lamp
 * says "Reading the program · <engine>", and the window stays usable. A
 * refusal (no engine, the engine did not answer, an answer it could not
 * read) is one line in place of that lamp, with its verbs. A question back
 * is one line; his next sentence answers it (sent with the first one).
 *
 * LANG5 (§4.2, J3): the bar's mic is the window's one mic. A finished
 * dictation (the end of the capture) settles into the well and is sent at
 * once; while the engine reads, the bar says what it heard. A question back
 * after a spoken sentence names the mic for the answer. Rows that wait in
 * the well (`pending`) go with each next sentence, so the engine adds to
 * them: three sentences in a row are one well. */
import { useCallback, useEffect, useState, type KeyboardEvent } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError } from "../../lib/api";
import { openSurfaceOr } from "../shell";
import { ChangeWell, DiffRow, DotWord, StringGadget } from "../surface";
import { failureTitle } from "../surface/plainFailure";
import { overturn, readShapeEngine, shapeProgram } from "./api";
import type { Program, ShapeAnswer, TextChange } from "./types";

/** `qwen3.8-27b · 2.8 s` (a reply under a tenth of a second: `under 1 s`). */
export function engineFact(answer: Pick<ShapeAnswer, "engine" | "seconds">): string {
  const time = answer.seconds >= 0.1 ? `${answer.seconds.toFixed(1)} s` : "under 1 s";
  return answer.engine ? `${answer.engine} · ${time}` : time;
}

/** The engine that shapes on this desk, read once per window. */
export function useShapeEngine(programId: string): string | null | undefined {
  const [engine, setEngine] = useState<string | null | undefined>(undefined);
  useEffect(() => {
    let live = true;
    readShapeEngine(programId).then((answer) => { if (live) setEngine(answer?.engine ?? null); })
      .catch(() => { if (live) setEngine(undefined); });
    return () => { live = false; };
  }, [programId]);
  return engine;
}

type Refusal = { words: string; title: string; code: string };

function refusalOf(cause: unknown): Refusal {
  const payload = cause instanceof ApiError ? (cause.payload as { code?: string; detail?: string } | null) : null;
  const code = payload?.code ?? "";
  if (code === "no_engine") return { words: "No engine is set for planning", title: payload?.detail ?? "", code };
  if (code === "engine_unusable") return { words: "The engine's answer could not be read. The program is unchanged. Try again.", title: payload?.detail ?? "", code };
  if (payload?.detail) return { words: payload.detail, title: failureTitle(cause), code };
  return { words: "The sentence did not reach the hub. The program is unchanged. Try again.", title: failureTitle(cause), code: "unreachable" };
}

export function ShapeBar({ program, pending, onAnswer, onOpenText }: {
  program: Program;
  /** LANG5: the text of the rows that wait in the well (a sentence's); the
   *  next sentence is shaped over it, so its rows add to them. */
  pending?: string | null;
  /** The hub answered rows (or landed them at YOLO). */
  onAnswer(answer: ShapeAnswer): void;
  /** No engine: the typed text is the other way to change it. */
  onOpenText(): void;
}) {
  const engine = useShapeEngine(program.id);
  const [sentence, setSentence] = useState("");
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [question, setQuestion] = useState<{ asked: string; first: string; spoken: boolean } | null>(null);
  const [nothing, setNothing] = useState(false);
  // LANG5: the sentence the mic heard (shown while the engine reads), and
  // the settle of the words into the well (Delight §9.7).
  const [heard, setHeard] = useState<string | null>(null);
  const [settle, setSettle] = useState(0);
  useEffect(() => {
    if (!settle) return;
    const timer = window.setTimeout(() => setSettle(0), 700);
    return () => window.clearTimeout(timer);
  }, [settle]);

  const shape = useCallback(async (again?: string, spoken = false) => {
    const said = (again ?? sentence).trim();
    if (!said || busy) return;
    const words = question && (!again || spoken) ? `${question.first} ${said}` : said;
    // The engine is read once per window; a press before that read lands reads it first.
    const known = engine === undefined ? await readShapeEngine(program.id).then((answer) => answer?.engine ?? null, () => undefined) : engine;
    if (known === null) {
      // The hub said no engine shapes on this desk: nothing is sent or guessed.
      setRefusal({ words: "No engine is set for planning", title: "No engine is set for planning. The program is unchanged. Choose one in Engines.", code: "no_engine" });
      return;
    }
    setBusy(true);
    setRefusal(null);
    setNothing(false);
    setHeard(spoken ? said : null);
    try {
      const answer = await shapeProgram(program.id, {
        sentence: words, apply: program.control === "yolo", ...(pending ? { pending } : {}),
      });
      if (answer.question && !answer.applied && !answer.changes.length) {
        setQuestion({ asked: answer.question, first: words, spoken });
        setSentence("");
        return;
      }
      setQuestion(null);
      if (!answer.applied && !answer.changes.length) {
        setNothing(true);
        return;
      }
      setSentence("");
      onAnswer(answer);
    } catch (cause) {
      setRefusal(refusalOf(cause));
    } finally {
      setBusy(false);
      setHeard(null);
    }
  }, [busy, engine, onAnswer, pending, program.control, program.id, question, sentence]);

  // The end of the capture: the words settle into the well and go at once.
  const dictated = (text: string) => {
    const said = text.trim();
    setSentence(said);
    setNothing(false);
    if (!said) return;
    setSettle((n) => n + 1);
    void shape(said, true);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void shape();
    }
  };

  return (
    <div className="pg-shape" data-testid="program-shape-bar" data-busy={busy ? "" : undefined}
      data-settle={settle ? "" : undefined}>
      <div className="pg-shape-row">
        <StringGadget label="Change the program" placeholder="Change the program" value={sentence}
          onChange={(next) => { setSentence(next); setNothing(false); }} onKeyDown={onKeyDown}
          onDictation={dictated}
          micLabel={question?.spoken ? "Speak your answer" : "Speak a change to the program"} />
        <Button dense variant="secondary" loading={busy} disabled={busy || !sentence.trim()} onClick={() => void shape()}
          data-testid="program-shape">Shape</Button>
      </div>
      {busy ? (
        <div className="pg-shape-line">
          <DotWord tone="info" live data-testid="program-shape-reading">
            {engine ? `Reading the program · ${engine}` : "Reading the program"}
          </DotWord>
          {heard ? <span className="pg-shape-heard" title={heard} data-testid="program-shape-heard">{`Heard: ${heard}`}</span> : null}
        </div>
      ) : refusal ? (
        <div className="pg-shape-line pg-shape-refusal" role="status" title={refusal.title || undefined} data-testid="program-shape-refusal">
          <span>{refusal.words}</span>
          {refusal.code === "no_engine" ? (
            <>
              <Button dense variant="ghost" onClick={() => openSurfaceOr("configure-runs-on", "/settings", "models")}
                data-testid="program-shape-engines">Open Engines</Button>
              <Button dense variant="ghost" onClick={onOpenText} data-testid="program-shape-text">Open text</Button>
            </>
          ) : (
            <Button dense variant="ghost" onClick={() => void shape(sentence)} disabled={!sentence.trim()}
              data-testid="program-shape-retry">Try again</Button>
          )}
        </div>
      ) : question ? (
        <div className="pg-shape-line pg-shape-question" role="status" data-testid="program-shape-question">{question.asked}</div>
      ) : nothing ? (
        <div className="pg-shape-line" role="status" data-testid="program-shape-nothing">Nothing to change · The program is unchanged</div>
      ) : null}
    </div>
  );
}

/** At YOLO: what the sentence landed (one Decided for you row), with
 *  Overturn while the steps it touched are still Planned or Ready. */
export function ShapedWell({ program, answer, onOverturned, onKeep }: {
  program: Program;
  answer: ShapeAnswer;
  onOverturned(next: Program | null): void;
  onKeep(): void;
}) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState<{ words: string; title?: string } | null>(null);
  const decision = answer.decision;
  const live = decision ? program.decided_for_you?.find((row) => String(row.id) === String(decision.id)) : undefined;
  const can = Boolean(decision) && (live ? live.overturnable : true);
  const rows: TextChange[] = answer.applied_rows;
  const undo = async () => {
    if (!decision) return;
    setBusy(true);
    setFailed(null);
    try {
      onOverturned(await overturn(program.id, String(decision.id)));
    } catch (cause) {
      const payload = cause instanceof ApiError ? (cause.payload as { detail?: string } | null) : null;
      setFailed({ words: payload?.detail ?? "The change was not put back. The program is as it is.", title: failureTitle(cause) });
    } finally {
      setBusy(false);
    }
  };
  return (
    <ChangeWell label="Shaped change" head={`Shaped: ${answer.say || answer.sentence}`} fact={`${engineFact(answer)} · applied`}
      failure={failed} data-testid="programs-shaped-well"
      verbs={(
        <>
          {can ? (
            <Button dense variant="secondary" loading={busy} disabled={busy} onClick={() => void undo()}
              title={live && !live.overturnable ? "A step it changed started" : undefined} data-testid="programs-shaped-overturn">
              Overturn
            </Button>
          ) : null}
          <Button dense variant="ghost" disabled={busy} onClick={onKeep} data-testid="programs-shaped-keep">Keep</Button>
        </>
      )}>
      {rows.map((row, index) => (
        <DiffRow key={row.id} index={index} op={row.op} where={row.where}
          field={row.op === "add" || row.op === "move" ? undefined : row.field}
          before={row.before || undefined} after={row.after || undefined} verdict="allowed"
          data-testid="programs-shaped-row" data-row={row.id} />
      ))}
    </ChangeWell>
  );
}
