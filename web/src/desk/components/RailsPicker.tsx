// HS-88-02 — "Ground on the rails": pick an open phase, story,
// evidence, or the roadmap from the belt's live projects and ride it
// into a run as a receipt (the hub reads the dw-named file). A sibling
// of GroundingSection, mounted beside it in the ask panel and the
// Phase-87 steer composer — one hydration, both surfaces.
// HS-111-05 — the rack grammar (audit §3.4): CheckGadget rows on
// full-width hover bands, titles ellipsized in minmax(0,1fr), the
// budget as tokens through the kit tones (no raw hexes).
import { useMemo, useState } from "react";
import { useMissionControl } from "../missioncontrol";
import { fetchRailsSizes, railsTokens, type RailsPick } from "../grounding";
import { CheckGadget, FoldGadget, LedMeter } from "../surface/gadgets";

const fmt = (n: number): string =>
  n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);

const tok = (chars: number): number =>
  chars <= 0 ? 0 : Math.max(1, Math.floor(chars / 4));

interface RailsRow {
  repo: string;
  project: string;
  kind: string;
  id: string;
  title: string;
}

/** The belt's live projects flattened into pickable rail objects:
 * the roadmap, the current phase, and its stories, per repo. */
function useRailsRows(): RailsRow[] {
  const repos = useMissionControl((s) => s.repos);
  return useMemo(() => {
    const rows: RailsRow[] = [];
    for (const repo of repos) {
      if (repo.status !== "live") continue;
      for (const p of repo.projects) {
        rows.push({
          repo: repo.name,
          project: p.slug,
          kind: "roadmap",
          id: p.slug,
          title: `${p.slug}: roadmap`,
        });
        const cur = p.currentPhase;
        if (cur) {
          rows.push({
            repo: repo.name,
            project: p.slug,
            kind: "phase",
            id: String(cur.number),
            title: `Phase ${cur.number}: ${cur.title}`,
          });
          for (const st of p.stories.filter((s) => s.phase === cur.number)) {
            rows.push({
              repo: repo.name,
              project: p.slug,
              kind: "story",
              id: st.storyId,
              title: `${st.storyId} ${st.title}`,
            });
          }
        }
      }
    }
    return rows;
  }, [repos]);
}

const key = (r: { kind: string; id: string; repo: string }) =>
  `${r.repo}:${r.kind}:${r.id}`;

export function RailsPicker(props: {
  picks: RailsPick[];
  onChange: (picks: RailsPick[]) => void;
  limitTokens: number;
  /** HS-111-05 — a host with a shared budget meter passes false. */
  meter?: boolean;
}) {
  const { picks, onChange, limitTokens, meter = true } = props;
  const rows = useRailsRows();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);

  const used = railsTokens(picks);
  const over = used > limitTokens;
  const frac = limitTokens > 0 ? Math.min(1, used / limitTokens) : 0;
  const tone = over || frac >= 0.85 ? "danger" : frac >= 0.6 ? "warn" : undefined;
  const isPicked = (r: RailsRow) => picks.some((p) => key(p) === key(r));

  const toggle = async (r: RailsRow) => {
    if (isPicked(r)) {
      onChange(picks.filter((p) => key(p) !== key(r)));
      return;
    }
    setLoading(key(r));
    const sizes = await fetchRailsSizes([
      { repo: r.repo, project: r.project, kind: r.kind, id: r.id },
    ]);
    setLoading(null);
    onChange([...picks, { ...r, chars: sizes[`${r.kind}:${r.id}`] || 0 }]);
  };

  if (rows.length === 0) return null; // no rails on this desk

  return (
    <div className={"desk-ground desk-rails" + (open ? " is-open" : "")}>
      <FoldGadget
        className="desk-ground-fold"
        glyph={
          <span className={"desk-ground-glyph" + (picks.length ? " is-on" : "")}>
            ▤
          </span>
        }
        title={
          picks.length === 0
            ? "Ground on the rails"
            : `Rails · ${picks.length}`
        }
        token={
          picks.length > 0 ? (
            <span className="surface-token" data-tone={tone}>
              {fmt(used)} / {fmt(limitTokens)} tok
            </span>
          ) : undefined
        }
        open={open}
        onToggle={setOpen}
      >
        {open && (
        <div className="desk-ground-body">
          {meter && picks.length > 0 && <LedMeter label="CTX" value={frac} />}
          {over && (
            <p className="desk-ground-refusal">
              ✕ PAST THE WINDOW · PICK FEWER RAIL OBJECTS
            </p>
          )}
          <ul className="desk-ground-list">
            {rows.map((r) => {
              const sel = isPicked(r);
              const priced = picks.find((p) => key(p) === key(r));
              return (
                <li
                  key={key(r)}
                  className={"desk-ground-row" + (sel ? " is-picked" : "")}
                >
                  <button
                    type="button"
                    className="desk-ground-line is-press"
                    onClick={(event) => {
                      if (
                        (event.target as HTMLElement).closest(".gadget-check")
                      )
                        return;
                      void toggle(r);
                    }}
                  >
                    <CheckGadget
                      label={r.title}
                      checked={sel}
                      onChange={() => void toggle(r)}
                    />
                    <span className="desk-rails-kind">{r.kind}</span>
                    <span className="desk-ground-name">{r.title}</span>
                    {loading === key(r) && (
                      <span className="desk-ground-loading">…</span>
                    )}
                    {priced && priced.chars > 0 && (
                      <span className="desk-ground-fig">
                        {fmt(tok(priced.chars))} tok
                      </span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
        )}
      </FoldGadget>
    </div>
  );
}
