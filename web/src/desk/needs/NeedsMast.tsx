/** The Needs-you mast (the bold language, 2026-11-08; canvas NB "the desk
 *  of today"). The Dock's lamp, the day and what must be fixed in the
 *  display face, one mono line of counts, and the verbs: Mine · People,
 *  Later (the rows for a later day) and, when there are any, the muted
 *  Projects. Under it the spine: brass is must fix, graphite should fix. */
import type { ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { Mast } from "../surface/patterns/Mast";
import { Spine, type SpineSegment } from "../surface/patterns/Spine";
import { SYSTEM_48 } from "../systemSprites";
import { needYouWords } from "../surface/count";
import type { NeedFace } from "./needsFace";
import { ShowMe } from "../walk/ShowMe";

/** Owner walk 2026-11-08: the list's scope. Mine is his own (everything a
 *  person does not owe him); People is what people owe him. */
export type NeedsScope = "mine" | "people";

export function inScope(face: Pick<NeedFace, "direction">, scope: NeedsScope): boolean {
  return scope === "people" ? face.direction === "theirs" : face.direction !== "theirs";
}

const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

/** The weights of the rows: how many must be fixed, should be, are noted. */
export type Weights = { must: number; should: number; noted: number };

export function weightsOf(faces: readonly Pick<NeedFace, "tier">[]): Weights {
  const out = { must: 0, should: 0, noted: 0 };
  for (const face of faces) if (face.tier) out[face.tier] += 1;
  return out;
}

/** `Sunday · 3 must fix`; with nothing to fix, the head (`Sunday · 53 need
 *  you`, `Sunday · Nothing needs you`). Never a zero. */
export function mastTitle(now: Date, must: number, head: string): string {
  return `${DAYS[now.getDay()]} · ${must > 0 ? `${must} must fix` : head}`;
}

/** The mono facts line: `53 need you · 12 should · 38 noted · checked 07:29`.
 *  The number the title says is not said again; a zero is not said. */
export function mastFacts({ count, must, should, noted, checked }: {
  count: number; must: number; should: number; noted: number; checked: string | null;
}): string {
  return [
    must > 0 && count > 0 ? needYouWords(count) : "",
    should > 0 ? `${should} should` : "",
    noted > 0 ? `${noted} noted` : "",
    checked ?? "",
  ].filter(Boolean).join(" · ");
}

/** The spine's parts: brass is the share that must be fixed, graphite the
 *  share that should be; the rest is idle. */
export function mastSpine(total: number, weights: Weights): SpineSegment[] {
  if (total <= 0) return [];
  const must = Math.min(weights.must, total);
  const should = Math.min(weights.should, total - must);
  return [
    { tone: "brass", share: must / total },
    { tone: "graphite", share: should / total },
    { tone: "idle", share: (total - must - should) / total },
  ];
}

export function NeedsMast({ now, head, count, weights, total, checked, scope, setScope, later, showLater, setShowLater, muted, showMuted, setShowMuted, offer }: {
  now: Date;
  /** `53 need you`, `Nothing needs you`: the head the status bar says. */
  head: string;
  /** The hub's one number (0 before the first read). */
  count: number;
  weights: Weights;
  /** The rows the spine measures. */
  total: number;
  checked: string | null;
  scope: NeedsScope;
  setScope(next: NeedsScope): void;
  /** The rows for a later day: Later shows them. */
  later: number;
  showLater: boolean;
  setShowLater(next: boolean): void;
  muted: number;
  showMuted: boolean;
  setShowMuted(next: boolean): void;
  /** No calendar and no next meeting: its word and Connect calendar. */
  offer: ReactNode;
}) {
  const segments = mastSpine(total, weights);
  return (
    <div className="needs-mast-band" data-testid="needs-toolbar">
      <Mast
        kind="needs"
        glyph={SYSTEM_48.dockIntelligence}
        title={mastTitle(now, weights.must, head)}
        facts={mastFacts({ count, ...weights, checked }) || undefined}
        className="needs-mast"
        data-testid="needs-mast"
      >
        {/* Owner walk 2026-11-08: ONE segmented control, Mine · People. */}
        <span className="needs-scope" role="group" aria-label="Whose" data-testid="needs-scope">
          <Button dense variant="secondary" className="needs-chip"
            aria-pressed={scope === "mine"} data-testid="needs-chip-mine" onClick={() => setScope("mine")}>Mine</Button>
          <Button dense variant="secondary" className="needs-chip"
            aria-pressed={scope === "people"} data-testid="needs-open-people" onClick={() => setScope("people")}>People</Button>
        </span>
        {later > 0 || showLater ? (
          <Button dense variant="secondary" className="needs-chip" aria-pressed={showLater} data-testid="needs-chip-later"
            title="The rows for a later day" onClick={() => setShowLater(!showLater)}>Later</Button>
        ) : null}
        {muted > 0 ? (
          <Button dense variant="ghost" className="needs-chip" aria-pressed={showMuted} data-testid="needs-chip-more"
            onClick={() => setShowMuted(!showMuted)}>{`Muted · ${muted}`}</Button>
        ) : null}
        {offer}
        <ShowMe app="chair:needs" />
      </Mast>
      {segments.length ? (
        <Spine className="needs-mast-spine" segments={segments} data-testid="needs-spine"
          label={[weights.must > 0 ? `${weights.must} must fix` : "", weights.should > 0 ? `${weights.should} should fix` : ""].filter(Boolean).join(", ") || undefined} />
      ) : null}
    </div>
  );
}
