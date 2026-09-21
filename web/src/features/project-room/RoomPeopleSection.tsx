// HS-172-07 / HS-200-14: PEOPLE section in the Room.
//
// 172-07 drew the people a Room's Watches name, resolved through the
// ledger: monogram lead, display name as stored, `N PRS WAITING` /
// `N ASSIGNMENTS OVERDUE` tokens absent at zero, `Open` trailing.
//
// 200-14 makes the section a preparation face inside the same boundary:
//   * the caption is a typed partial: `PEOPLE 3` when every person the
//     Project names is linked, `PEOPLE 2 OF 3` when not, and the ledger's
//     mono head line names the gaps (`1 AMBIGUOUS · 1 NOT LINKED`,
//     `LOCKED`): never an empty section over a known gap (AC5);
//   * a linked person's row opens on their commitments (story 12's
//     records, `DUE`, the meeting and segment they came from, `Open
//     source`) and their observable facts, each with its Watch (AC2);
//   * an owner two people could be meant by is `OWNER · AMBIGUOUS · 2
//     MATCHES` with `Resolve`, which unfolds the candidates under the row
//     (no modal); one click links the alias through the ledger's own
//     write and NEVER attributes on its own (AC1);
//   * `People` on the section head opens PeopleCore scoped to this
//     Project and remembers the verb for the way back (AC4).
// Every verb is the library Button; no prose; no counters of zero; one
// verb per row (the way into the ledger sits on the head, once).
import { useCallback, useEffect, useState } from "react";
import {
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
} from "../../desk/surface";
import { Button } from "../../components/signal/Signal";
import { openPrimitive, openSurfaceOr } from "../../desk/shell";
import { onReturnToTask, rememberTaskFocus } from "../../desk/returnToTask";
import { countToken, countLabel } from "../../desk/surface/count";
import {
  fetchRoomPeoplePreparation,
  linkOwnerAlias,
  type RoomLinkedPerson,
  type RoomOmittedSource,
  type RoomPeoplePreparation,
  type RoomPersonCommitment,
  type RoomPersonFact,
  type RoomPersonItem,
  type RoomUnresolvedOwner,
} from "./api";

/* ── Monogram ── */

/**
 * Two-letter monogram from a display name.
 * Takes the first letter of the first two words.
 * Never derives a first name or pronoun from the display name.
 */
export function monogram(displayName: string): string {
  const words = displayName.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

/* ── Token builders (pure; unit-tested) ── */

export type PersonTokens = {
  prsWaiting: string | null;
  assignmentsOverdue: string | null;
};

/**
 * Build the caption tokens for a person row.
 * Absent at zero. Overdue in warning color.
 */
export function buildPersonTokens(person: RoomPersonItem): PersonTokens {
  return {
    prsWaiting: countToken(person.prs_waiting, "PR WAITING", "PRS WAITING"),
    assignmentsOverdue: countToken(
      person.assignments_overdue,
      "ASSIGNMENT OVERDUE",
      "ASSIGNMENTS OVERDUE",
    ),
  };
}

/** The section caption: `PEOPLE 3` when complete, `PEOPLE 2 OF 3` when
 *  not (the attention caption grammar, `attention.ts:422`), `PEOPLE`
 *  when nothing is counted. */
export function peopleCaption(prep: Pick<RoomPeoplePreparation, "expected" | "resolved">): string {
  if (prep.expected <= 0) return "PEOPLE";
  if (prep.resolved >= prep.expected) return countLabel("PEOPLE", prep.expected);
  return `PEOPLE ${prep.resolved} OF ${prep.expected}`;
}

/** The ledger's mono head line: the gaps, named once, absent at zero. */
export function peopleGapTokens(prep: Pick<RoomPeoplePreparation, "state" | "gaps">): string[] {
  if (prep.state === "locked") return ["LOCKED"];
  if (prep.state === "unconfigured") return ["NOT SET UP"];
  if (prep.state === "unavailable") return ["UNAVAILABLE"];
  const tokens: string[] = [];
  const ambiguous = countToken(prep.gaps.ambiguous, "AMBIGUOUS", "AMBIGUOUS");
  if (ambiguous) tokens.push(ambiguous);
  const notLinked = countToken(prep.gaps.not_linked, "NOT LINKED", "NOT LINKED");
  if (notLinked) tokens.push(notLinked);
  return tokens;
}

/** The owner-state token on an unresolved row. */
export function ownerToken(row: Pick<RoomUnresolvedOwner, "link" | "candidates">): string {
  if (row.link === "ambiguous") {
    const matches = countToken(row.candidates.length, "MATCH", "MATCHES");
    return matches ? `OWNER · AMBIGUOUS · ${matches}` : "OWNER · AMBIGUOUS";
  }
  if (row.link === "locked") return "OWNER · LOCKED";
  if (row.link === "unconfigured") return "OWNER · NOT SET UP";
  if (row.link === "unavailable") return "OWNER · UNAVAILABLE";
  return "OWNER · NOT LINKED";
}

/** The one head verb: the repair while the ledger is not ready, else
 *  the way into People. Never both: they open the same door. */
export function headVerbLabel(state: RoomPeoplePreparation["state"]): string {
  if (state === "locked") return "Unlock";
  if (state === "unconfigured") return "Set up People";
  return "People";
}

const FACT_NOUNS: Record<RoomPersonFact["kind"], [string, string]> = {
  prs_waiting: ["PR WAITING", "PRS WAITING"],
  assignments_open: ["ASSIGNMENT OPEN", "ASSIGNMENTS OPEN"],
  assignments_overdue: ["ASSIGNMENT OVERDUE", "ASSIGNMENTS OVERDUE"],
};

export function factToken(fact: RoomPersonFact): string | null {
  const [one, many] = FACT_NOUNS[fact.kind];
  return countToken(fact.count, one, many);
}

/** `MTG` for a meeting, the Watch's connector otherwise. */
function emblemFor(connector: string): string {
  if (connector === "gh") return "GH";
  if (connector === "jira") return "J";
  return connector.slice(0, 3).toUpperCase() || "SRC";
}

function dueToken(dueAt: string | null): string | null {
  if (!dueAt) return null;
  const day = dueAt.slice(0, 10);
  const today = new Date().toISOString().slice(0, 10);
  if (day === today) return "DUE TODAY";
  if (day < today) return "OVERDUE";
  return `DUE ${day.slice(5)}`;
}

/** HS-202-04 (F21, Constitution tenet 4) — the provenance LINE speaks
 *  whole words: `Meeting · <title> · Segment 4`. `MTG` and `SEG` were
 *  abbreviations no face ever defined, and HS-201-06 already paid the same
 *  debt one face over (`meetings/MeetingIntelRecovery.tsx:57-61`). The
 *  three-letter LEAD EMBLEM in the 52px ledger slot
 *  (`desk/surface/contract.md:265`) is a species contract with a fixed
 *  width and keeps its glyph — this is a full line, where the word fits. */
export function sourceToken(source: RoomPersonCommitment["source"]): string {
  const seg =
    source.segment_index != null ? ` · Segment ${source.segment_index + 1}` : "";
  return `Meeting · ${source.label}${seg}`;
}

/* ── Sub-ledger: a person's commitments and facts ── */

function PersonDetail({
  commitments,
  facts,
  omitted = [],
}: {
  commitments: RoomPersonCommitment[];
  facts: RoomPersonFact[];
  omitted?: RoomOmittedSource[];
}) {
  if (commitments.length === 0 && facts.length === 0 && omitted.length === 0) return null;
  return (
    <ul className="surface-ledger-rows room-people-detail">
      {commitments.map((c) => {
        const due = dueToken(c.due_at);
        return (
          <SurfaceLedgerRow
            key={c.id}
            lead="CMT"
            primary={<span className="surface-primary">{c.text}</span>}
            cells={
              <span className="room-people-cells">
                {due ? (
                  <span
                    className={`surface-token room-people-tok${due === "OVERDUE" || due === "DUE TODAY" ? " room-people-warn" : ""}`}
                  >
                    {due}
                  </span>
                ) : null}
                <span className="surface-token room-people-tok room-people-source" data-chip="">
                  {sourceToken(c.source)}
                </span>
              </span>
            }
            wrap
            expands={false}
            trailing={
              <Button
                dense
                variant="ghost"
                aria-label={`Open source: ${c.source.label}`}
                onClick={() => openPrimitive(`meeting:${c.source.meeting_id}`)}
                data-testid="room-people-open-source"
              >
                Open source
              </Button>
            }
            data-testid="room-people-commitment"
          />
        );
      })}
      {facts.map((f, i) => {
        const token = factToken(f);
        if (!token) return null;
        return (
          <SurfaceLedgerRow
            key={`${f.source.watch_id}-${f.kind}-${i}`}
            lead={emblemFor(f.source.connector_id)}
            primary={<span className="surface-primary">{f.source.label}</span>}
            cells={
              <span className="room-people-cells">
                <span
                  className={`surface-token room-people-tok${f.kind === "assignments_overdue" ? " room-people-warn" : ""}`}
                >
                  {token}
                </span>
              </span>
            }
            wrap
            expands={false}
            data-testid="room-people-fact"
          />
        );
      })}
      {omitted.map((o) => (
        <SurfaceLedgerRow
          key={`omitted-${o.watch_id}`}
          lead={emblemFor(o.connector_id)}
          primary={<span className="surface-primary">{o.label}</span>}
          cells={
            <span className="room-people-cells">
              <span className="surface-token room-people-tok room-people-warn" data-testid="room-people-omitted-token">
                {`${o.state.toUpperCase()} · OMITTED`}
              </span>
            </span>
          }
          wrap
          expands={false}
          data-testid="room-people-omitted"
        />
      ))}
    </ul>
  );
}

/* ── The resolve well: candidates under the row, no modal ── */

function ResolveWell({
  row,
  busy,
  onPick,
  onElsewhere,
}: {
  row: RoomUnresolvedOwner;
  busy: boolean;
  onPick: (relationshipId: string) => void;
  onElsewhere: (from: HTMLElement) => void;
}) {
  return (
    <div className="room-people-resolve" role="group" aria-label={`Resolve: ${row.owner}`} data-testid="room-people-resolve">
      {row.candidates.map((c) => (
        <Button
          key={c.relationship_id}
          dense
          disabled={busy}
          aria-label={`Link: ${c.display_name}`}
          onClick={() => onPick(c.relationship_id)}
          data-testid="room-people-candidate"
        >
          {c.display_name}
        </Button>
      ))}
      <Button
        dense
        variant="ghost"
        disabled={busy}
        aria-label="Someone else: open People"
        onClick={(e) => onElsewhere(e.currentTarget)}
        data-testid="room-people-elsewhere"
      >
        Someone else
      </Button>
    </div>
  );
}

/* ── Component ── */

export function RoomPeopleSection({
  projectId,
}: {
  projectId: string;
}) {
  const [prep, setPrep] = useState<RoomPeoplePreparation | null>(null);
  const [openOwner, setOpenOwner] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    return fetchRoomPeoplePreparation(projectId)
      .then(setPrep)
      .catch(() => setPrep({
        state: "unavailable", expected: 0, resolved: 0,
        gaps: { ambiguous: 0, not_linked: 0, unreadable: 0 }, people: [], unresolved: [],
      }));
  }, [projectId]);

  useEffect(() => {
    let cancelled = false;
    void fetchRoomPeoplePreparation(projectId)
      .then((next) => { if (!cancelled) setPrep(next); })
      .catch(() => {
        if (!cancelled) setPrep({
          state: "unavailable", expected: 0, resolved: 0,
          gaps: { ambiguous: 0, not_linked: 0, unreadable: 0 }, people: [], unresolved: [],
        });
      });
    return () => { cancelled = true; };
  }, [projectId]);

  // The way back from People: re-read on the return-to-task signal
  // (HS-200-41's one event), so a link made there shows here without a
  // reload.
  useEffect(() => onReturnToTask(() => { void load(); }), [load]);

  const openPeople = useCallback((from?: HTMLElement | null) => {
    rememberTaskFocus(from);
    openSurfaceOr("open-people", "/", `people:project:${projectId}`);
  }, [projectId]);

  const pick = useCallback(async (row: RoomUnresolvedOwner, relationshipId: string) => {
    setBusy(true);
    try {
      await linkOwnerAlias(relationshipId, row.owner);
      setOpenOwner(null);
      await load();
    } catch {
      // A clash (409, the holder named) or a locked store: the row stays
      // as it was; the next read names the state.
      await load();
    } finally {
      setBusy(false);
    }
  }, [load]);

  if (!prep) return null;
  // Nothing named, nothing to say: absent (UX-CANON A.8). A ledger state
  // is only a gap when someone is named.
  if (prep.expected === 0 && prep.people.length === 0) return null;

  const gapTokens = peopleGapTokens(prep);
  const verb = headVerbLabel(prep.state);

  return (
    <SurfaceSection
      label={peopleCaption(prep)}
      actions={
        <Button
          dense
          variant={prep.state === "ready" ? "ghost" : "secondary"}
          aria-label={prep.state === "ready" ? "People: this Project's people" : `${verb}: the People ledger`}
          onClick={(e) => openPeople(e.currentTarget)}
          data-testid="room-people-head-verb"
        >
          {verb}
        </Button>
      }
    >
      <SurfaceLedger
        count={gapTokens.length ? (
          <span data-testid="room-people-gaps">{gapTokens.join(" · ")}</span>
        ) : ""}
        cols="room"
      >
        <ul className="surface-ledger-rows">
          {prep.people.map((person: RoomLinkedPerson) => {
            // One object drawn once (D1, N2): the per-source fact rows below
            // carry each count WITH its Watch, so the row's own 172-07
            // tokens draw only for a payload that has no fact rows.
            const tokens = person.facts.length > 0
              ? { prsWaiting: null, assignmentsOverdue: null }
              : buildPersonTokens(person);
            const mono = monogram(person.display_name);
            const omitted = person.omitted_sources ?? [];
            const hasDetail = person.commitments.length > 0 || person.facts.length > 0 || omitted.length > 0;
            const openCount = countToken(person.commitments.length, "OPEN COMMITMENT", "OPEN COMMITMENTS");
            return (
              <SurfaceLedgerRow
                key={person.relationship_id}
                lead={mono}
                primary={
                  <span className="room-people-primary">
                    <span className="surface-primary">{person.display_name}</span>
                    {openCount ? (
                      <span className="surface-token room-people-tok">{openCount}</span>
                    ) : null}
                    {tokens.prsWaiting ? (
                      <span className="surface-token room-people-tok">
                        {tokens.prsWaiting}
                      </span>
                    ) : null}
                    {tokens.assignmentsOverdue ? (
                      <span className="surface-token room-people-tok room-people-overdue" data-tone="warn">
                        {tokens.assignmentsOverdue}
                      </span>
                    ) : null}
                  </span>
                }
                wrap
                open={hasDetail}
                expands={false}
                trailing={
                  <Button
                    dense
                    variant="ghost"
                    aria-label={`Open: ${person.display_name}`}
                    onClick={() => {
                      openSurfaceOr(
                        "open-people",
                        "/",
                        `people:${person.relationship_id}`,
                      );
                    }}
                    data-testid="room-people-open"
                  >
                    Open
                  </Button>
                }
                data-testid="room-people-row"
              >
                <PersonDetail commitments={person.commitments} facts={person.facts} omitted={omitted} />
              </SurfaceLedgerRow>
            );
          })}
          {prep.unresolved.map((row: RoomUnresolvedOwner) => {
            const isOpen = openOwner === row.owner;
            const token = ownerToken(row);
            const openCount = countToken(row.commitments.length, "OPEN COMMITMENT", "OPEN COMMITMENTS");
            const verbLabel = row.link === "ambiguous" ? "Resolve" : "Link";
            return (
              <SurfaceLedgerRow
                key={`owner-${row.owner}`}
                lead={monogram(row.owner)}
                primary={
                  <span className="room-people-primary">
                    <span className="surface-primary">{row.owner}</span>
                    <span
                      className={`surface-token room-people-tok ${row.link === "ambiguous" || row.link === "not_linked" ? "room-people-warn" : "room-people-fail"}`}
                      data-testid="room-people-owner-token"
                    >
                      {token}
                    </span>
                    {openCount ? (
                      <span className="surface-token room-people-tok">{openCount}</span>
                    ) : null}
                  </span>
                }
                wrap
                open={isOpen || row.commitments.length > 0}
                expands={false}
                trailing={
                  row.link !== "ambiguous" && row.link !== "not_linked" ? undefined : (
                    <Button
                      dense
                      variant="secondary"
                      aria-pressed={isOpen}
                      aria-label={`${verbLabel}: ${row.owner}`}
                      onClick={(e) => {
                        if (row.candidates.length === 0) {
                          openPeople(e.currentTarget);
                          return;
                        }
                        setOpenOwner(isOpen ? null : row.owner);
                      }}
                      data-testid="room-people-resolve-verb"
                    >
                      {verbLabel}
                    </Button>
                  )
                }
                data-testid="room-people-unresolved-row"
              >
                {isOpen && row.candidates.length > 0 ? (
                  <ResolveWell
                    row={row}
                    busy={busy}
                    onPick={(id) => void pick(row, id)}
                    onElsewhere={(from) => openPeople(from)}
                  />
                ) : null}
                <PersonDetail commitments={row.commitments} facts={[]} />
              </SurfaceLedgerRow>
            );
          })}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}
