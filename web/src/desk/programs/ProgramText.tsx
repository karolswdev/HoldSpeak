import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { wireWords } from "../surface/words";
import { programFailure as readableError } from "./liveModel";
import {
  CheckGadget,
  DotWord,
  InspectorFacts,
  InspectorQuestion,
  ListPane,
  ListView,
  PaneActions,
  PaneInspector,
  SurfaceState,
  TextPane,
  type TextPaneLine,
} from "../surface";
import { applyProgram, applyProgramText, readProgramText } from "./api";
import { answerBinding, bindingId, currentStep } from "./liveModel";
import type { Program, TextApplyAnswer } from "./types";

/** Lamps printed by the hub are annotations, never editable program text. */
export function textLines(text: string): TextPaneLine[] {
  return text.split("\n").map((raw) => {
    if (raw.trimStart().startsWith("#") || /^\s*\?\s/.test(raw))
      return { text: raw, readOnly: true };
    const match = /\s{2,}#(?:\s(.*))?$/.exec(raw);
    return match && !raw.trimStart().startsWith(">")
      ? { text: raw.slice(0, match.index), lamp: match[1] }
      : { text: raw };
  });
}
export const textOf = (lines: readonly TextPaneLine[]) =>
  lines.map((row) => row.text).join("\n");
export const PROGRAM_KEYWORDS = [
  "program",
  "goal",
  "in",
  "control",
  "check",
  "agent",
  "reviewer",
  "step",
  "brief",
  "owns",
  "after",
  "round",
  "night",
  "every step",
  "at the end",
  "review",
  "merge",
  "run",
  "expect",
  "for",
  "from",
];
export type ChangeProposal = {
  answer: TextApplyAnswer;
  text: string;
  base: string;
  target: string;
  binding: ReturnType<typeof answerBinding>;
};

export function ProgramText({
  program,
  onApplied,
  onError,
}: {
  program: Program;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const [base, setBase] = useState<string | null>(null),
    [lines, setLines] = useState<TextPaneLine[]>([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [proposal, setProposal] = useState<ChangeProposal | null>(null);
  const edited = useRef(false),
    reads = useRef(0);
  const read = async (force = false) => {
    const mine = ++reads.current;
    try {
      const answer = await readProgramText(program.id);
      if (mine !== reads.current || (edited.current && !force)) return;
      setBase(answer.text);
      setLines(textLines(answer.text));
      edited.current = false;
      setError("");
    } catch (cause) {
      setError(readableError(cause));
    }
  };
  useEffect(() => {
    if (!edited.current) void read();
  }, [program.id, program.revision]);
  const preview = async () => {
    if (!base || busy) return;
    setBusy(true);
    const text = textOf(lines),
      binding = answerBinding(program),
      target = bindingId(program, binding.step_id);
    try {
      const answer = await applyProgramText(program.id, {
        text,
        base,
        dry_run: true,
        binding,
      });
      setProposal({ answer, text, base, binding, target });
    } catch (cause) {
      onError(readableError(cause));
    } finally {
      setBusy(false);
    }
  };
  if (proposal)
    return (
      <TextChanges
        program={program}
        proposal={proposal}
        onCancel={() => setProposal(null)}
        onApplied={(next) => {
          setProposal(null);
          edited.current = false;
          if (next) {
            setBase(null);
            void read();
          }
          onApplied(next);
        }}
        onError={onError}
      />
    );
  if (base == null)
    return (
      <SurfaceState
        loading={!error}
        error={error || undefined}
        onRetry={() => void read()}
      />
    );
  return (
    <>
      <TextPane
        fill
        data-feedback-redact="true"
        label="Program text"
        data-testid="programs-text"
        lines={lines}
        keywords={PROGRAM_KEYWORDS}
        onChange={(next) => {
          setLines(next);
          edited.current = true;
        }}
      />
      <PaneActions>
        <Button variant="ghost" onClick={() => void read(true)}>
          Revert
        </Button>
        <Button
          variant="primary"
          loading={busy}
          disabled={!edited.current || busy}
          onClick={() => void preview()}
        >
          Apply…
        </Button>
      </PaneActions>
    </>
  );
}
export function TextChanges(props: Parameters<typeof ProposalReview>[0]) {
  return <ProposalReview key={`${props.proposal.answer.proposal_id}:${props.proposal.text}`} {...props} />;
}
function ProposalReview({
  program,
  proposal,
  onCancel,
  onApplied,
  onError,
  onSplit,
}: {
  onSplit?(place: number): Promise<void>;
  program: Program;
  proposal: ChangeProposal;
  onCancel(): void;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const alive = useRef(true);
  useEffect(
    () => () => {
      alive.current = false;
    },
    [],
  );
  const [picked, setPicked] = useState<string | null>(null),
    [allowed, setAllowed] = useState(new Set<string>()),
    [armed, setArmed] = useState(false),
    [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const now = bindingId(program, proposal.binding.step_id),
    stale = now !== proposal.target;
  const row = proposal.answer.changes.find((row) => row.id === picked);
  const pending = proposal.answer.changes.filter(
    (row) => row.verdict === "lowers" && !allowed.has(row.id),
  );
  const refused = proposal.answer.changes.some(
    (row) => row.verdict === "refused" || row.verdict === "conflict",
  );
  const apply = async () => {
    if (busy || stale) return;
    setBusy(true);
    setFailure("");
    try {
      const answer = await applyProgramText(program.id, {
        text: refused ? proposal.answer.allowed_text : proposal.text,
        base: proposal.base,
        dry_run: false,
        allow_lower: [...allowed],
        proposal_id: proposal.answer.proposal_id,
        binding: proposal.binding,
      });
      if (answer.applied) {
        applyProgram(answer.program ?? null);
        if (alive.current) {
          onApplied(answer.program ?? null);
          onError("");
        }
      } else if (alive.current) {
        setFailure(
          "The text was not applied · The program changed · Your edit is kept · Preview it again",
        );
        onError(
          answer.changes
            .filter(
              (row) => row.verdict === "refused" || row.verdict === "conflict",
            )
            .map((row) => row.reason)
            .join(" · ") || "The program did not change.",
        );
        setArmed(false);
      }
    } catch (cause) {
      if (!alive.current) return;
      setFailure(readableError(cause));
      onError(readableError(cause));
    } finally {
      if (alive.current) setBusy(false);
    }
  };
  return (
    <ListPane
      label="Selected text change"
      list={
        <ListView
          label="Text changes"
          headerless
          columns={[{ key: "name", word: "Change" }]}
          rows={proposal.answer.changes.map((row) => ({
            id: row.id,
            kind: "program",
            name: row.say,
            detail: row.reason || wireWords(row.verdict === "lowers" ? "Lowers review" : row.verdict),
          }))}
          selectedId={picked}
          onSelect={setPicked}
          verbs={[
            {
              id: "apply",
              label: "Apply",
              enabled: () =>
                !stale &&
                !pending.length &&
                Boolean(proposal.answer.changes.length),
              run: () => setArmed(true),
            },
            {
              id: "split",
              label: "Split large step",
              enabled: () =>
                Boolean(onSplit && row?.size?.code === "step_too_big"),
              run: () => {
                if (row?.size?.place) void onSplit?.(row.size.place);
              },
            },
            { enabled: () => true, id: "cancel", label: "Cancel", run: onCancel },
          ]}
          toolbar={{}}
        />
      }
    >
      {failure ? (
        <div role="status">
          <DotWord tone="fail">{failure}</DotWord>
        </div>
      ) : null}
      {stale ? (
        <InspectorFacts
          data-feedback-redact="true"
          name="Program changed"
          rows={[
            {
              label: "Text",
              value: "Your edit is kept. Cancel and preview it again.",
            },
          ]}
        />
      ) : armed ? (
        <InspectorQuestion
          actionId="apply-program-text"
          targetId={`${now}:${proposal.answer.proposal_id}:${proposal.text}`}
          question="Apply these changes?"
          keeps={["The ledger"]}
          cancel={() => setArmed(false)}
          verb={{ label: "Apply", run: () => void apply(), busy }}
        />
      ) : row ? (
        <PaneInspector label="Change" onClose={() => setPicked(null)}>
          <InspectorFacts
            data-feedback-redact="true"
            name="Change"
            rows={[
              { label: "Before", value: row.before },
              { label: "After", value: row.after },
              { label: "Reason", value: row.reason },
              { label: "Size", value: row.size?.words },
              ...(row.verdict === "lowers"
                ? [
                    {
                      label: "Allow",
                      value: (
                        <CheckGadget
                          label="Allow this change"
                          checked={allowed.has(row.id)}
                          onChange={(value) =>
                            setAllowed((before) => {
                              const next = new Set(before);
                              if (value) next.add(row.id);
                              else next.delete(row.id);
                              return next;
                            })
                          }
                        />
                      ),
                    },
                  ]
                : []),
            ]}
          />
        </PaneInspector>
      ) : null}
    </ListPane>
  );
}
