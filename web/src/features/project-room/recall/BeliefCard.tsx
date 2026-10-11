/* BeliefCard — memory on the Desk (canvas section 2, option B, ratified
 * 2026-10-05): a belief memory holds, drawn as ONE MORE KIND of the recall
 * card (`.recall-card`, one object, three inks).
 *
 *   line     : the belief's text at the primary step.
 *   chips    : BELIEF · CURRENT | DISPUTED | SUPERSEDED (+ `SINCE 10-01`)
 *              · `3 SOURCES` (distinct sources) · `SEEN 10-01` · the Project button.
 *   EVIDENCE : the refs as tokens that open their windows; a ref that
 *              contradicts reads `AGAINST · MTG 09-29 · 10:05`.
 *   HISTORY  : unfolds; each old text struck through with its reason
 *              (`SUPERSEDED · FREEZE MOVED`).  Open by default on a current
 *              belief.
 *
 * A belief has no verb of its own: it is read, and its sources open.
 */
import { openRef } from "../../../desk/openObject";
import { Disclosure, RefTokens, countLabel, countToken } from "../../../desk/surface";
import { ProjectButton } from "../../../desk/surface/patterns";
import type { BeliefCardData } from "./model";
import { openProjectRoom } from "../../../desk/shell";

const STATE_TONE: Record<string, "ok" | "danger" | "warn"> = {
  current: "ok",
  disputed: "danger",
  superseded: "warn",
};

export function BeliefCard({
  belief,
  onOpenRef = openRef,
}: {
  belief: BeliefCardData;
  onOpenRef?: (ref: string) => void;
}) {
  // SOURCES counts distinct sources, never facts (one note with two facts
  // is 1 SOURCE).
  const sources = countToken(belief.source_count, "SOURCE");
  return (
    <article
      className="recall-card recall-belief"
      data-kind="belief"
      data-state={belief.state}
      data-recall-row
      data-testid="recall-belief"
      aria-label={`${belief.text}: the ${belief.state} belief`}
    >
      <div className="recall-card-line">
        <span className="surface-primary recall-card-title" data-testid="recall-belief-title">
          {belief.text}
        </span>
      </div>
      <div className="recall-card-chips">
        <span className="surface-token" data-chip>BELIEF</span>
        <span className="surface-token" data-chip data-tone={STATE_TONE[belief.state]} data-testid="recall-belief-state">
          {belief.state.toUpperCase()}
        </span>
        {belief.state === "superseded" && belief.since ? (
          <span className="surface-token recall-superseded-by" data-testid="recall-belief-since">
            SINCE {belief.since}
          </span>
        ) : null}
        {sources ? <span className="surface-token" data-chip>{sources}</span> : null}
        {belief.seen ? <span className="surface-token">SEEN {belief.seen}</span> : null}
        {belief.project ? (
          <ProjectButton
            name={belief.project.name}
            onOpen={() => openProjectRoom(belief.project!.id)}
            data-testid="recall-project"
          />
        ) : null}
      </div>
      {belief.evidence.length ? (
        <div className="recall-source" data-testid="recall-belief-evidence">
          <span className="surface-token">EVIDENCE</span>
          <RefTokens refs={belief.evidence} onOpen={onOpenRef} label="Evidence" />
        </div>
      ) : null}
      {belief.history.length ? (
        <Disclosure
          label={countLabel("HISTORY", belief.history.length)}
          variant="dense"
          defaultOpen={belief.state === "current"}
          ariaLabel={`History of the belief: ${belief.text}`}
        >
          <ol className="recall-belief-history" data-testid="recall-belief-history">
            {belief.history.map((row, index) => (
              <li key={`${row.at}:${index}`}>
                {row.at ? <span className="surface-token">{row.at}</span> : null}
                <s className="recall-belief-old" data-testid="recall-belief-old">{row.text}</s>
                {row.word ? (
                  <span className="surface-token" data-tone="warn">
                    {row.reason ? `${row.word} · ${row.reason.toUpperCase()}` : row.word}
                  </span>
                ) : null}
              </li>
            ))}
          </ol>
        </Disclosure>
      ) : null}
    </article>
  );
}
