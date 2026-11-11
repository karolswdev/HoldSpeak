import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { programFailure as readableError } from "./liveModel";
import {
  InspectorForm,
  CycleGadget,
  ListPane,
  ListView,
  PadGadget,
  PaneInspector,
} from "../surface";
import { answerRound, decideRound, nextQuestion, openRounds } from "./api";
import { answerBinding, bindingId } from "./liveModel";
import { TextChanges, type ChangeProposal } from "./ProgramText";
import type { Program } from "./types";

/** Rounds keep their own question id on the wire. The answer's proposed
 * changes use the same text review and revision-bound Apply as typed edits. */
export function ProgramInterview({
  program,
  onApplied,
  onError,
  onClose,
}: {
  program: Program;
  onApplied(next: Program | null): void;
  onError(words: string): void;
  onClose?(): void;
}) {
  const rounds = program.rounds ?? [];
  const [picked, setPicked] = useState(
      rounds.find((row) => row.waiting)?.name ?? rounds[0]?.name ?? null,
    ),
    [said, setSaid] = useState(""),
    [option, setOption] = useState(""),
    [busy, setBusy] = useState(false),
    [failed, setFailed] = useState("");
  const [reading, setReading] = useState(true);
  const [proposal, setProposal] = useState<ChangeProposal | null>(null);
  const round = rounds.find((row) => row.name === picked),
    question = round?.questions.find((row) => row.id === round.waiting);
  const work = async (call: () => Promise<{ program: Program }>) => {
    if (busy) return;
    setBusy(true);
    setFailed("");
    try {
      const answer = await call();
      onApplied(answer.program);
    } catch (cause) {
      setFailed(readableError(cause));
      onError(readableError(cause));
    } finally {
      setBusy(false);
    }
  };
  const answer = async (skip = false) => {
    if (!round || !question || busy) return;
    setBusy(true);
    setFailed("");
    try {
      const next = await answerRound(program.id, round.name, {
        question_id: question.id,
        binding: answerBinding(program),
        ...(option ? { option } : { answer: said }),
        skip,
        apply: false,
      });
      onApplied(next.program);
      setSaid("");
      setOption("");
      if (next.changes?.length) {
        const binding = answerBinding(next.program);
        setProposal({
          answer: next,
          text: next.proposed_text,
          base: next.base,
          binding,
          target: bindingId(next.program),
        });
      }
    } catch (cause) {
      setFailed(readableError(cause));
      onError(readableError(cause));
    } finally {
      setBusy(false);
    }
  };
  const skipQuestion = {
    id: "skip-question",
    label: "Skip question",
    enabled: () => Boolean(question),
    run: () => void answer(true),
  };
  const skipRound = {
    id: "skip",
    label: "Skip round",
    enabled: () => Boolean(round),
    run: () => void work(() => decideRound(program.id, round!.name, "skip", answerBinding(program))),
  };
  if (proposal)
    return (
      <TextChanges
        program={program}
        proposal={proposal}
        onCancel={() => setProposal(null)}
        onApplied={(next) => {
          setProposal(null);
          onApplied(next);
        }}
        onError={onError}
      />
    );
  if (question && reading)
    return (
      <PaneInspector label={round!.name} testId="program-round-question">
        <InspectorForm
          rows={[
            {
              label: "Round",
              control: (
                <CycleGadget
                  label="Round"
                  value={picked || ""}
                  options={rounds.map((row) => ({
                    value: row.name,
                    label: row.name,
                  }))}
                  onChange={(id) => {
                    setPicked(id);
                    setSaid("");
                    setOption("");
                  }}
                />
              ),
            },
            { label: "Question", control: question!.text },
            { label: "Why", control: question!.why },
            {
              label: "Leave",
              control: (
                <>
                  {[skipQuestion, skipRound].map((verb) => (
                    <Button
                      key={verb.id}
                      variant="ghost"
                      disabled={busy || !verb.enabled()}
                      onClick={verb.run}
                    >
                      {verb.label}
                    </Button>
                  ))}{" "}
                </>
              ),
            },
            ...(question!.choices.length
              ? [
                  {
                    label: "Choose",
                    control: (
                      <CycleGadget
                        key={question!.id}
                        label="Offered answer"
                        value={option}
                        options={[
                          { value: "", label: "Your own answer" },
                          ...question!.choices.map((value) => ({
                            value,
                            label: value,
                          })),
                        ]}
                        onChange={setOption}
                      />
                    ),
                  },
                ]
              : []),
            {
              label: "Answer",
              control: (
                <PadGadget
                  key={question!.id}
                  label="Round answer"
                  value={said}
                  onChange={setSaid}
                />
              ),
            },
          ]}
          notice={failed || undefined}
          completion={{
            cancel: () => {
              setSaid("");
              setReading(false);
            },
            primary: {
              label: "Answer",
              busy,
              disabled: !said.trim() && !option,
              run: () => void answer(),
            },
          }}
        />
      </PaneInspector>
    );
  return (
    <ListPane
      label="Selected round"
      list={
        <ListView
          label="Rounds"
          headerless
          rows={rounds.map((row) => ({
            id: row.name,
            kind: "program",
            name: row.name,
            detail: `${row.answered} answered · ${row.state}`,
          }))}
          columns={[{ key: "name", word: "Round" }]}
          selectedId={picked}
          onSelect={(id) => {
            setPicked(id);
            setReading(true);
            setSaid("");
            setOption("");
          }}
          onOpen={() => setReading(true)}
          verbs={[
            {
              id: "read",
              label: "Read question",
              enabled: () => Boolean(question),
              run: () => setReading(true),
            },
            ...(onClose
              ? [{ id: "steps", label: "Back to steps", run: onClose }]
              : []),
            {
              id: "open",
              label: "Ask me first",
              run: () => void work(() => openRounds(program.id)),
            },
            {
              id: "next",
              label: "Next question",
              enabled: () => Boolean(round && !round.waiting),
              run: () => void work(() => nextQuestion(program.id, round!.name)),
            },
            skipQuestion,
            {
              id: "done",
              label: "Done with round",
              enabled: () => Boolean(round && !question),
              run: () =>
                void work(() => decideRound(program.id, round!.name, "done", answerBinding(program))),
            },
            skipRound,
            {
              id: "more",
              label: "Ask more",
              enabled: () => Boolean(round),
              run: () =>
                void work(() => decideRound(program.id, round!.name, "reopen", answerBinding(program))),
            },
          ]}
          toolbar={{}}
        />
      }
    ></ListPane>
  );
}
