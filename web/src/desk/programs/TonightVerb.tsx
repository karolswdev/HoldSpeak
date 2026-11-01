/* JRN2 (PROGRAM-JOURNEYS-2026-10-31, "the dreaming night"; LANG12 #1687):
 * the library Button "Tonight" on a Door task row and in a note line's
 * menu. A press adds the item to the night Program as a Planned step; the
 * row then says "Tonight · in <the night Program's title>". A refusal (no
 * night program, more than one) is the hub's own words, in place. */
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError } from "../../lib/api";
import { DotWord } from "../surface";
import { addToTonight, type TonightAnswer } from "./api";

export function tonightWords(answer: TonightAnswer): string {
  const title = answer.program?.title;
  return title ? `Tonight · in ${title}` : "Tonight";
}

export function tonightRefusal(cause: unknown): string {
  const payload = cause instanceof ApiError ? (cause.payload as { detail?: string; message?: string } | null) : null;
  return payload?.detail || payload?.message || "It was not added to tonight. Nothing changed. Try again.";
}

/** Add to tonight, one item. */
export function useTonight(body: { kind: "action" | "note"; item_id: string; line?: string }) {
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string>("");
  const [failed, setFailed] = useState<string>("");
  const press = async () => {
    setBusy(true);
    setFailed("");
    try {
      setDone(tonightWords(await addToTonight(body)));
    } catch (cause) {
      setFailed(tonightRefusal(cause));
    } finally {
      setBusy(false);
    }
  };
  return { busy, done, failed, press };
}

export function TonightVerb({ kind, itemId, line, name }: { kind: "action" | "note"; itemId: string; line?: string; name: string }) {
  const tonight = useTonight({ kind, item_id: itemId, ...(line ? { line } : {}) });
  if (tonight.done) return <DotWord tone="info" data-testid="tonight-done">{tonight.done}</DotWord>;
  return (
    <>
      <Button dense variant="ghost" loading={tonight.busy} disabled={tonight.busy} aria-label={`Tonight: ${name}`}
        onClick={() => void tonight.press()} data-testid="tonight-verb">Tonight</Button>
      {tonight.failed ? <DotWord tone="warn" title={tonight.failed} data-testid="tonight-failed">{tonight.failed}</DotWord> : null}
    </>
  );
}
