// HS-88-02 — "Ground on the rails": pick an open phase, story,
// evidence, or the roadmap from the belt's live projects and ride it
// into a run as a receipt (the hub reads the dw-named file). A sibling
// of GroundingSection, mounted beside it in the ask panel and the
// Phase-87 steer composer — one hydration, both surfaces.
import { useMemo, useState } from "react";
import { useMissionControl } from "../missioncontrol";
import { fetchRailsSizes, railsTokens, type RailsPick } from "../grounding";

const fmt = (n: number): string => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n));

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
        rows.push({ repo: repo.name, project: p.slug, kind: "roadmap", id: p.slug, title: `${p.slug} — roadmap` });
        const cur = p.currentPhase;
        if (cur) {
          rows.push({
            repo: repo.name, project: p.slug, kind: "phase",
            id: String(cur.number), title: `Phase ${cur.number} — ${cur.title}`,
          });
          for (const st of p.stories.filter((s) => s.phase === cur.number)) {
            rows.push({
              repo: repo.name, project: p.slug, kind: "story",
              id: st.storyId, title: `${st.storyId} ${st.title}`,
            });
          }
        }
      }
    }
    return rows;
  }, [repos]);
}

const key = (r: { kind: string; id: string; repo: string }) => `${r.repo}:${r.kind}:${r.id}`;

export function RailsPicker(props: {
  picks: RailsPick[];
  onChange: (picks: RailsPick[]) => void;
  limitTokens: number;
}) {
  const { picks, onChange, limitTokens } = props;
  const rows = useRailsRows();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);

  const used = railsTokens(picks);
  const over = used > limitTokens;
  const tone = over ? "bad" : used / (limitTokens || 1) >= 0.6 ? "warn" : "ok";
  const isPicked = (r: RailsRow) => picks.some((p) => key(p) === key(r));

  const toggle = async (r: RailsRow) => {
    if (isPicked(r)) {
      onChange(picks.filter((p) => key(p) !== key(r)));
      return;
    }
    setLoading(key(r));
    const sizes = await fetchRailsSizes([{ repo: r.repo, project: r.project, kind: r.kind, id: r.id }]);
    setLoading(null);
    onChange([...picks, { ...r, chars: sizes[`${r.kind}:${r.id}`] || 0 }]);
  };

  if (rows.length === 0) return null; // no rails on this desk

  return (
    <div className={"desk-ground desk-rails" + (open ? " is-open" : "")}>
      <button type="button" className="desk-ground-head" onClick={() => setOpen((v) => !v)}>
        <span className={"desk-ground-glyph" + (picks.length ? " is-on" : "")} aria-hidden="true">▤</span>
        <span className="desk-ground-title">
          {picks.length === 0 ? "Ground on the rails" : `Rails · ${picks.length}`}
        </span>
        {picks.length > 0 && (
          <span className={"desk-ground-tokens is-" + tone}>{fmt(used)} / {fmt(limitTokens)} tok</span>
        )}
        <span className="desk-ground-chev" aria-hidden="true">{open ? "▴" : "▾"}</span>
      </button>

      {open && (
        <div className="desk-ground-body">
          {over && <p className="desk-run-warning">⚠ Past the window — pick fewer rail objects</p>}
          <ul className="desk-ground-list">
            {rows.map((r) => {
              const sel = isPicked(r);
              return (
                <li key={key(r)} className={"desk-ground-row" + (sel ? " is-picked" : "")}>
                  <button type="button" className="desk-ground-pick" onClick={() => void toggle(r)}>
                    <span className="desk-ground-check" aria-hidden="true">{sel ? "●" : "○"}</span>
                    <span className="desk-rails-kind">{r.kind}</span>
                    <span className="desk-ground-name">{r.title}</span>
                    {loading === key(r) && <span className="desk-ground-loading">…</span>}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
