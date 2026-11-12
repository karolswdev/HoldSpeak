// Parked 2026-11-11: this Room drawing is replaced by the shared list and inspector seats.
// @ts-nocheck
// The project's standing pages in History (the language, 2026-11-08): R1
// took This week off the Now face, so the pages it drew (Open, Risks,
// Changed) are one head row of History: "Pages", then a kit object row for
// each served page. A row opens its page in place (the kit StandingPage, each
// sentence with its source). No page served: no row.
import { useState } from "react";
import { ListRow, ListView, StandingPage } from "../../../desk/surface";
import { spriteUrl } from "../../../desk/sprites";
import { openRef } from "../../../desk/openObject";
import { builtToken, pageTitle, useStandingPagesRead } from "../../../desk/standingPages";

/** The pages History names, in this order, with their short word. */
export const HISTORY_PAGES = [
  { slug: "what-is-open", word: "Open" },
  { slug: "risks-and-disputes", word: "Risks" },
  { slug: "what-changed-this-week", word: "Changed" },
] as const;

export function HistoryPages({ projectId }: { projectId: string }) {
  const { pages } = useStandingPagesRead("project", projectId);
  const [open, setOpen] = useState<string | null>(null);
  const served = HISTORY_PAGES.flatMap(({ slug, word }) => {
    const page = pages.find((p) => p.slug === slug);
    return page && page.sentences.length ? [{ page, word }] : [];
  });
  if (!served.length) return null;
  return (
    <div className="room-history-pages" data-testid="room-history-pages">
      <span className="room-history-pages-label">Pages</span>
      <ListView label="Pages" className="room-history-pages-list">
        <ul className="kit-listrows">
          {served.map(({ page, word }) => {
            const shown = open === page.slug;
            return (
              <ListRow
                key={page.slug}
                data-testid="room-page-row"
                openTestId="room-page-open"
                glyph={spriteUrl("memory", page.slug, "rest", null, 20)}
                name={word}
                meta={page.sentences[0]?.text}
                age={builtToken(page.built_at).replace(/^BUILT\s*/, "").toLowerCase()}
                onOpen={() => setOpen(shown ? null : page.slug)}
                expanded={shown}
                openLabel={shown ? `Hide the page: ${word}` : `Open the page: ${word}`}
                fold={shown ? (
                  <StandingPage
                    title={pageTitle(page)}
                    sentences={page.sentences}
                    built={builtToken(page.built_at)}
                    stale={page.stale}
                    newSources={page.new_sources}
                    onOpenRef={openRef}
                  />
                ) : undefined}
              />
            );
          })}
        </ul>
      </ListView>
    </div>
  );
}
