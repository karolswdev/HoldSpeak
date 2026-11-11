// PARKED: the Needs you window uses the shared selection list and reader.
/** The Needs-you ledger (the bold language, 2026-11-08; canvas NB). The
 *  rows by weight: Must fix (a brass tick), Should fix (graphite), the rows
 *  with no weight (steel), Noted (idle). Each group's head is a small
 *  tracked label with its tick and its count; the row the first plate
 *  shows is not drawn again (`Must fix · 2 more`). A group with no row is
 *  not drawn. Promises kept on arrival lead, under their meeting. */
import { NeedsList } from "../surface/objects";
import { foldMatches, tierRank, type NeedFace } from "./needsFace";
import { MatchRows, NeedRow } from "./NeedRow";

export type LedgerWeight = "must" | "should" | "open" | "noted";

const LABELS: Record<LedgerWeight, string> = { must: "Must fix", should: "Should fix", open: "To do", noted: "Noted" };

export function ledgerWeight(face: Pick<NeedFace, "tier">): LedgerWeight {
  return face.tier ?? "open";
}

export type LedgerGroup = { weight: LedgerWeight; label: string; faces: NeedFace[] };

/** The groups in their order (must, should, no weight, noted), each in the
 *  hub's rank. `firstId` (the plate's row) leaves its group; its group's
 *  count then says `N more`. */
export function ledgerGroups(faces: readonly NeedFace[], firstId: string | null): LedgerGroup[] {
  const order: LedgerWeight[] = ["must", "should", "open", "noted"];
  const sorted = [...faces].sort((a, b) => tierRank(a) - tierRank(b));
  const first = firstId ? faces.find((face) => face.id === firstId) : undefined;
  return order.map((weight) => {
    const rows = sorted.filter((face) => ledgerWeight(face) === weight && face.id !== firstId);
    const more = first && ledgerWeight(first) === weight;
    return { weight, label: `${LABELS[weight]} · ${rows.length}${more ? " more" : ""}`, faces: rows };
  }).filter((group) => group.faces.length > 0);
}

function GroupHead({ weight, label }: { weight: LedgerWeight; label: string }) {
  return (
    <h3 className="needs-ledger-head" data-weight={weight}>
      <i className="needs-ledger-tick" aria-hidden="true" />
      {label}
    </h3>
  );
}

export function Ledger({ groups, arrivals, firstId, projects }: {
  groups: LedgerGroup[];
  /** Betterment D3: promises kept on arrival, under their meeting. */
  arrivals: Array<{ key: string; label: string; faces: NeedFace[] }>;
  /** The face's one lead verb (the first row when no plate holds it). */
  firstId: string | null;
  projects: boolean;
}) {
  if (!groups.length && !arrivals.length) return null;
  return (
    <div className="needs-ledger" data-testid="needs-ledger">
      {arrivals.map((group) => (
        <section key={group.key} className="needs-ledger-group needs-arrival" data-testid="needs-arrival" data-weight="new">
          <GroupHead weight="open" label={group.label} />
          <NeedsList label={group.label}>
            {group.faces.map((face) => (
              <NeedRow key={face.id} face={face} primary={face.id === firstId} projects={projects} plates={false} />
            ))}
          </NeedsList>
        </section>
      ))}
      {groups.map((group) => (
        <section key={group.weight} className="needs-ledger-group" data-weight={group.weight} data-testid="needs-ledger-group">
          <GroupHead weight={group.weight} label={group.label} />
          <NeedsList label={group.label}>
            {foldMatches(group.faces).map((entry) => entry.kind === "face" ? (
              <NeedRow key={entry.face.id} face={entry.face} primary={entry.face.id === firstId} projects={projects} plates={false} />
            ) : (
              <MatchRows key={entry.key} entry={entry} firstId={firstId} projects={projects} />
            ))}
          </NeedsList>
        </section>
      ))}
    </div>
  );
}
