/** Ask's local composition of the shared selection, question and reading pieces.
 * The older composer exports in askFace still serve Memory and the Room. */
import { useState, type ReactNode, type RefObject } from "react";
import { Button } from "../../components/signal/Signal";
import { ListPane, ListView, PaneActions, Popover, PreferencePane, StringGadget, DotWord, PaneGroup, faceTimeWords } from "../surface";
import { spriteUrl } from "../sprites";
import { agentWordsPlain } from "./AgentWords";
import { aboutMatches, type AboutCandidate } from "./about/AboutPicker";

export const ASK_SPRITE = spriteUrl("thread", "ask");
export interface AskReferenceRowData {
  ref: string; title: string; kind: string; meta?: string;
  lamp?: "ok" | "warn" | "info" | "idle"; onOpen?: () => void;
}

export function AskSendButton({ disabled, onClick }: { disabled: boolean; onClick(): void }) {
  return <Button dense variant="primary" disabled={disabled} onClick={onClick} aria-label="Ask">Ask</Button>;
}

type ScopeRow = { ref: string; title: string };
export function AskScope({ rows, candidates, onPick, onRemove, onOpenRow, control }: {
  control: { open: boolean; close(): void; anchor: RefObject<HTMLElement | null> };
  rows: readonly ScopeRow[]; candidates: readonly AboutCandidate[];
  onPick(row: AboutCandidate): void; onRemove(row: ScopeRow): void; onOpenRow?(row: ScopeRow): (() => void) | undefined;
}) {
  const [query, setQuery] = useState(""), [picked, setPicked] = useState<string | null>(null);
  const { anchor, open, close } = control;
  const align = (anchor.current?.getBoundingClientRect().left ?? 0) < window.innerWidth / 2 ? "start" : "end";
  const choices = [{ ref: "desk:whole", label: "My whole desk", kind: "set" } as AboutCandidate,
    ...rows.map(row => ({ ref: row.ref, label: row.title, kind: row.ref.split(":")[0] } as AboutCandidate)),
    ...(query.trim() ? aboutMatches([...candidates], query, 30) : candidates.filter(row => row.kind === "project" || row.kind === "person" || row.ref === "meetings:this_week")).filter(row => row.ref !== "desk:whole" && !rows.some(known => known.ref === row.ref))];
  const choose = (id: string) => {
    const choice = choices.find(row => row.ref === id);
    if (choice) onPick(choice);
    close(); setQuery("");
  };
  return <>
    <Popover align={align} anchor={anchor} open={open} onClose={close} ariaLabel="About">
      <PreferencePane label="About" testId="ask-scope-menu">
        <StringGadget label="Find a meeting, note, person" placeholder="Find a source" value={query} onChange={setQuery} />
        <ListPane label="About" list={<ListView label="About" ordered columns={[{ key: "name", word: "About" }]} selectedId={picked} onSelect={setPicked}
          rows={choices.map(row => ({ id: row.ref, kind: row.kind, name: row.label, detail: rows.some(known => known.ref === row.ref) ? "Chosen" : undefined }))}
          defaultVerb="choose" verbs={[
            { id: "choose", label: "Choose", run: row => { if (row) choose(row.id); } },
            { id: "remove", label: "Remove", enabled: row => Boolean(row && rows.some(known => known.ref === row.id)), run: row => { const known = rows.find(known => known.ref === row?.id); if (known) onRemove(known); } },
            { id: "open", label: "Open", enabled: row => Boolean(row && rows.some(known => known.ref === row.id && onOpenRow?.(known))), run: row => { const known = rows.find(known => known.ref === row?.id); if (known) onOpenRow?.(known)?.(); } },
          ]} />} />
      </PreferencePane>
    </Popover>
  </>;
}

/** Claim rows are a product projection; the engine's answer stays verbatim. */
function claimWords(claim: { text: string; ref?: string; title?: string }) {
  const id = claim.ref?.split(":").slice(1).join(":");
  return agentWordsPlain(claim.text, Infinity, false)
    .replace(/\b[\w-]+\b/g, word => word === id ? claim.title || "this record" : word)
    .replace(/\b\d{4}-\d{2}-\d{2}(?:T[0-9:.]+Z)?\b/g, stamp => faceTimeWords(stamp));
}

export function AskClaims({ claims, onOpen }: {
  claims: ReadonlyArray<{ text: string; ref?: string; title?: string; label: string }>;
  onOpen(ref: string): (() => void) | undefined;
}) {
  const [picked, setPicked] = useState<string | null>(null);
  return <div data-testid="ask-claims" data-feedback-redact="true"><ListView label="Claims and their records" ordered
    rows={claims.map((claim, index) => ({ id: String(index), kind: "note", name: claimWords(claim), detail: [claim.title, claim.label === "partial" ? "In part" : ""].filter(Boolean).join(" · ") }))}
    columns={[{ key: "name", word: "Claims and their records" }]} externalToolbar={!picked} selectedId={picked} onSelect={setPicked} defaultVerb="open"
    verbs={[{ id: "open", label: "Open record", enabled: row => Boolean(row && claims[Number(row.id)]?.ref && onOpen(claims[Number(row.id)].ref!)), run: row => { const ref = row && claims[Number(row.id)]?.ref; if (ref) onOpen(ref)?.(); } }]} /></div>;
}

export function askReasonLine(reason: string, fallback: string) {
  return ({ no_engine: "No engine answers Ask yet.", timed_out: "The engine did not answer in time.", did_not_answer: "The engine did not answer.", not_reachable: "The engine could not be reached." } as Record<string, string>)[reason] ?? fallback;
}
export function AskNotAnswered({ reason, words, verb }: { reason: string; words: string; verb?: ReactNode }) {
  return <div data-testid="ask-not-answered" data-reason={reason}><PaneActions><DotWord tone={reason === "stopped" ? "idle" : "fail"}>{words}</DotWord>{verb}</PaneActions></div>;
}

export function AskSources({ rows }: { rows: readonly AskReferenceRowData[] }) {
  const [picked, setPicked] = useState<string | null>(null);
  if (!rows.length) return null;
  return <PaneGroup label="" grow={false}><div data-testid="ask-looked-at" data-feedback-redact="true"><ListView label="Sources" ordered
    columns={[{ key: "name", word: "Sources" }, { key: "kind", word: "Kind", track: "110px" }]}
    rows={rows.map(row => ({ id: row.ref, kind: row.kind, name: row.title, detail: row.meta }))} selectedId={picked} onSelect={setPicked} externalToolbar={!picked}
    defaultVerb="open-source" verbs={[{ id: "open-source", label: "Open source", enabled: row => Boolean(row && rows.find(source => source.ref === row.id)?.onOpen), run: row => { if (row) rows.find(source => source.ref === row.id)?.onOpen?.(); } }]} /></div></PaneGroup>;
}
