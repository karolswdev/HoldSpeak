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
//     (no modal) and NEVER attributes on its own (AC1);
//   * HS-S41: a candidate press only SELECTS. The well reads the People
//     list (owner-only, in memory) to show kind and role beside each name,
//     says that the name links for every matching owner, and writes only on
//     a separate `Link`. Candidates with the same details keep `Link` off:
//     `Inspect` opens that exact person, and `Check` reads again;
//   * `People` on the section head opens PeopleCore scoped to this
//     Project and remembers the verb for the way back (AC4).
// Every verb is the library Button; no prose; no counters of zero; one
// verb per row (the way into the ledger sits on the head, once).
import { useRoomRead } from "./roomReads";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiFetch } from "../../lib/api";
import { openPerson } from "../../desk/openObject";
import { ActionNotice } from "../../desk/surface/patterns/ActionNotice";
import {
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
} from "../../desk/surface";
import { Button } from "../../components/signal/Signal";
import { openPrimitive, openSurfaceOr } from "../../desk/shell";
import { onReturnToTask, rememberTaskFocus } from "../../desk/returnToTask";
import { countToken, countLabel } from "../../desk/surface/count";
import { DotWord } from "../../desk/surface/kit";
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
import { Token } from "../../desk/surface/Token";
import { wireWords } from "../../desk/surface/words";

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

/** The owner state on an unresolved row, as words in sentence case
 *  (W6-H words: a state is a dot + word, never a mono caps chip). */
export function ownerToken(row: Pick<RoomUnresolvedOwner, "link" | "candidates">): string {
  if (row.link === "ambiguous") {
    const n = row.candidates.length;
    return n > 0 ? `Owner not clear · ${n} ${n === 1 ? "match" : "matches"}` : "Owner not clear";
  }
  if (row.link === "locked") return "Owner locked";
  if (row.link === "unconfigured") return "Owner not set up";
  if (row.link === "unavailable") return "Owner not available";
  return "Owner not linked";
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
                  <Token
                    className={`surface-token room-people-tok${due === "OVERDUE" ? " room-people-fail" : due === "DUE TODAY" ? " room-people-warn" : ""}`}
                  >
                    {due}
                  </Token>
                ) : null}
                <Token className="surface-token room-people-tok room-people-source" data-chip="">
                  {sourceToken(c.source)}
                </Token>
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
                <Token
                  className={`surface-token room-people-tok${f.kind === "assignments_overdue" ? " room-people-fail" : ""}`}
                >
                  {token}
                </Token>
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
              <Token className="surface-token room-people-tok room-people-warn" data-testid="room-people-omitted-token">
                {`${wireWords(o.state)} · OMITTED`}
              </Token>
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

/** HS-S41: what the owner-only People list says about one candidate. Held in
 *  memory for the open well only; never on the Room wire, a draft or a log. */
export type CandidateContext = { name: string; kind: string; role: string; aliases: string[] };

type PeopleListRow = {
  id?: unknown; display_name?: unknown; relationship_kind?: unknown;
  role_context?: unknown; owner_aliases?: unknown;
};

/** The words that tell one candidate from another: name, kind, role. */
export function candidateLabel(context: CandidateContext): string {
  return [context.name, wireWords(context.kind), context.role].filter(Boolean).join(" · ");
}

/** The candidates this read can tell apart: present in the current list,
 *  with a label no other candidate has. An id or list order is not proof. */
export function distinguishableCandidates(
  candidates: readonly { relationship_id: string }[],
  byId: Readonly<Record<string, CandidateContext>>,
): Set<string> {
  const labels = new Map<string, number>();
  for (const c of candidates) {
    const context = byId[c.relationship_id];
    if (!context) continue;
    const label = candidateLabel(context);
    labels.set(label, (labels.get(label) ?? 0) + 1);
  }
  const out = new Set<string>();
  for (const c of candidates) {
    const context = byId[c.relationship_id];
    if (context && labels.get(candidateLabel(context)) === 1) out.add(c.relationship_id);
  }
  return out;
}

export type LinkResult =
  | { status: "conflict"; holder: string }
  | { status: "reserved" | "missing" | "forbidden" | "uncertain" };

/** The alias POST's refusal, by its known class. A 503 or a lost answer can
 *  come after the encrypted write, so it is NOT a refusal: it is unknown. */
export function linkResult(error: unknown): LinkResult {
  if (!(error instanceof ApiError)) return { status: "uncertain" };
  const payload = (error.payload ?? {}) as { detail?: unknown };
  const detail = payload.detail;
  if (error.status === 409 && detail && typeof detail === "object"
    && (detail as { code?: unknown }).code === "owner_alias_taken") {
    const holder = (detail as { holder_name?: unknown }).holder_name;
    return { status: "conflict", holder: typeof holder === "string" ? holder.trim() : "" };
  }
  if (error.status === 422 && detail === "owner_alias_reserved") return { status: "reserved" };
  if (error.status === 404) return { status: "missing" };
  if (error.status === 403) return { status: "forbidden" };
  return { status: "uncertain" };
}

type WellRead = { key: string; status: "loading" | "ready" | "failed"; byId: Record<string, CandidateContext> };

type LinkAttempt = {
  seq: number;
  openGen: number;
  projectId: string;
  owner: string;
  relationshipId: string;
  personLabel: string;
  commitmentIds: string[];
  status: "pending" | "linked" | "current" | "conflict" | "reserved" | "missing" | "forbidden" | "uncertain";
  holder?: string;
  refreshFailed?: boolean;
};

function ResolveWell({
  row,
  read,
  selectedId,
  linkBlocked,
  linking,
  onSelect,
  onLink,
  onCancel,
  onCheck,
  onElsewhere,
}: {
  row: RoomUnresolvedOwner;
  read: WellRead | null;
  selectedId: string | null;
  linkBlocked: boolean;
  linking: boolean;
  onSelect: (relationshipId: string | null) => void;
  onLink: (relationshipId: string, personLabel: string) => void;
  onCancel: () => void;
  onCheck: () => void;
  onElsewhere: (from: HTMLElement) => void;
}) {
  // While Check reads again, the same well keeps its last context; Link
  // waits for the fresh answer.
  const ready = read?.status === "ready";
  const byId = read?.byId ?? {};
  const clear = distinguishableCandidates(row.candidates, byId);
  const selected = selectedId && byId[selectedId] ? byId[selectedId] : null;
  const selectedLabel = selected ? candidateLabel(selected) : "";
  return (
    <div className="room-people-resolve" role="group" aria-label={`Resolve: ${row.owner}`} data-testid="room-people-resolve">
      {row.candidates.map((c) => {
        const context = byId[c.relationship_id];
        const label = context ? candidateLabel(context) : c.display_name;
        const isSelected = selectedId === c.relationship_id;
        return (
          <Button
            key={c.relationship_id}
            dense
            variant={isSelected ? "secondary" : "ghost"}
            disabled={linking || !context}
            aria-pressed={isSelected}
            aria-label={`Select: ${label}`}
            onClick={() => onSelect(isSelected ? null : c.relationship_id)}
            data-testid="room-people-candidate"
          >
            {label}
          </Button>
        );
      })}
      <Button
        dense
        variant="ghost"
        disabled={linking}
        aria-label="Someone else: open People"
        onClick={(e) => onElsewhere(e.currentTarget)}
        data-testid="room-people-elsewhere"
      >
        Someone else
      </Button>
      <Button
        dense
        variant="ghost"
        loading={read?.status === "loading"}
        aria-label={`Check: ${row.owner}`}
        onClick={onCheck}
        data-testid="room-people-check"
      >
        Check
      </Button>
      {read?.status === "failed" ? (
        <span className="room-people-resolve-note" role="alert" data-testid="room-people-resolve-read-failed">
          Could not read People · Nothing changed · Check
        </span>
      ) : null}
      {selected && selectedId ? (
        <div className="room-people-resolve-confirm" data-testid="room-people-confirm"
          style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 6, flexBasis: "100%" }}>
          {clear.has(selectedId) ? (
            <span className="room-people-resolve-note" style={{ flexBasis: "100%" }} data-testid="room-people-confirm-scope">
              {`Link the name "${row.owner}" to ${selectedLabel}. Every owner named "${row.owner}", in all projects, then goes to this person.`}
            </span>
          ) : (
            <span className="room-people-resolve-note" style={{ flexBasis: "100%" }} data-testid="room-people-confirm-same">
              {`${selectedLabel}: another match has the same details. Open the person to make sure.`}
            </span>
          )}
          {clear.has(selectedId) ? (
            <Button
              dense
              variant="secondary"
              loading={linking}
              disabled={linkBlocked || linking || !ready}
              aria-label={`Link "${row.owner}" to ${selectedLabel}`}
              onClick={() => onLink(selectedId, selectedLabel)}
              data-testid="room-people-link"
            >
              Link
            </Button>
          ) : null}
          <Button
            dense
            variant="ghost"
            aria-label={`Inspect: ${selectedLabel}`}
            onClick={() => openPerson(selectedId)}
            data-testid="room-people-inspect"
          >
            Inspect
          </Button>
          <Button
            dense
            variant="ghost"
            disabled={linking}
            aria-label="Cancel"
            onClick={onCancel}
            data-testid="room-people-cancel"
          >
            Cancel
          </Button>
        </div>
      ) : null}
    </div>
  );
}

/** The one line a link attempt leaves, kept apart from the reads after it. */
function attemptWords(attempt: LinkAttempt): string {
  const name = `"${attempt.owner}"`;
  switch (attempt.status) {
    case "pending": return `Linking ${name}`;
    case "linked": return `Linked ${name} to ${attempt.personLabel}.`;
    case "current": return `${name} is linked to ${attempt.personLabel} now.`;
    case "conflict": return attempt.holder
      ? `${name} is already linked to ${attempt.holder}. Nothing changed.`
      : `${name} is already linked to another person. Nothing changed.`;
    case "reserved": return `${name} is a reserved name. You cannot link it.`;
    case "missing": return `This person is not in People now. Nothing changed.`;
    case "forbidden": return `Only the owner can link a name. Nothing changed.`;
    default: return `The link result for ${name} is not known. Check before you try again.`;
  }
}

/* ── Component ── */

export function RoomPeopleSection({
  projectId,
}: {
  projectId: string;
}) {
  const [prep, setPrep] = useState<RoomPeoplePreparation | null>(null);
  const [openOwner, setOpenOwner] = useState<string | null>(null);
  const [openGen, setOpenGen] = useState(0);
  const [wellRead, setWellRead] = useState<WellRead | null>(null);
  const [selected, setSelected] = useState<{ key: string; id: string } | null>(null);
  const [attempt, setAttempt] = useState<LinkAttempt | null>(null);
  const readSeq = useRef(0);
  const attemptSeq = useRef(0);
  const projectRef = useRef(projectId);
  projectRef.current = projectId;
  useRoomRead("people", prep !== null);

  /** The Room read. Resolves true on a fresh answer for THIS project.
   *  `keep`: a failed read after a write keeps the rows it had, so the
   *  write's receipt stays on the face beside the read failure. */
  const load = useCallback((keep = false): Promise<boolean> => {
    const asked = projectId;
    return fetchRoomPeoplePreparation(asked)
      .then((next) => {
        if (projectRef.current === asked) setPrep(next);
        return true;
      })
      .catch(() => {
        if (projectRef.current === asked) setPrep((current) => keep && current ? current : {
          state: "unavailable", expected: 0, resolved: 0,
          gaps: { ambiguous: 0, not_linked: 0, unreadable: 0 }, people: [], unresolved: [],
        });
        return false;
      });
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
    // HS-S41: another project retires the well, its private context and any
    // receipt; a late answer for the old project is dropped by its sequence.
    readSeq.current += 1;
    attemptSeq.current += 1;
    setOpenOwner(null);
    setWellRead(null);
    setSelected(null);
    setAttempt(null);
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

  const openRow = prep?.unresolved.find((row) => row.owner === openOwner && row.candidates.length > 0) ?? null;
  const wellKey = openRow
    ? `${projectId}\u0000${openRow.owner}\u0000${openRow.candidates.map((c) => c.relationship_id).join(",")}`
    : "";

  /** The owner-only People list, joined by the exact current candidate ids.
   *  Only name, kind, role and the owner names stay, in memory. */
  const readCandidates = useCallback((key: string, ids: readonly string[]) => {
    const seq = ++readSeq.current;
    setWellRead((current) => ({ key, status: "loading", byId: current?.key === key ? current.byId : {} }));
    void apiFetch<{ relationships?: PeopleListRow[] }>("/api/people/relationships")
      .then((body) => {
        if (seq !== readSeq.current) return;
        const wanted = new Set(ids);
        const byId: Record<string, CandidateContext> = {};
        for (const item of body.relationships ?? []) {
          const id = String(item.id ?? "");
          if (!wanted.has(id)) continue;
          byId[id] = {
            name: String(item.display_name ?? "").trim(),
            kind: String(item.relationship_kind ?? "").trim(),
            role: String(item.role_context ?? "").trim(),
            aliases: Array.isArray(item.owner_aliases) ? item.owner_aliases.map(String) : [],
          };
        }
        setWellRead({ key, status: "ready", byId });
        // Exact saved literal on the attempt's person: current evidence only.
        setAttempt((current) => current && current.status === "uncertain"
          && key.startsWith(`${current.projectId}\u0000${current.owner}\u0000`)
          && byId[current.relationshipId]?.aliases.includes(current.owner)
          ? { ...current, status: "current" } : current);
      })
      .catch(() => {
        if (seq !== readSeq.current) return;
        setWellRead({ key, status: "failed", byId: {} });
        setSelected(null);
      });
  }, []);

  const candidateIds = openRow ? openRow.candidates.map((c) => c.relationship_id) : [];
  const candidateIdsKey = candidateIds.join(",");
  useEffect(() => {
    if (!wellKey) {
      readSeq.current += 1;
      setWellRead(null);
      setSelected(null);
      return;
    }
    readCandidates(wellKey, candidateIdsKey.split(","));
  }, [wellKey, candidateIdsKey, readCandidates, openGen]);

  const check = useCallback(() => {
    void load(true);
    if (wellKey) readCandidates(wellKey, candidateIdsKey.split(","));
  }, [load, wellKey, candidateIdsKey, readCandidates]);

  const link = useCallback(async (row: RoomUnresolvedOwner, relationshipId: string, personLabel: string) => {
    const captured: LinkAttempt = {
      seq: ++attemptSeq.current,
      openGen,
      projectId,
      owner: row.owner,
      relationshipId,
      personLabel,
      commitmentIds: row.commitments.map((c) => c.id),
      status: "pending",
    };
    const same = (current: LinkAttempt | null) => Boolean(current && current.seq === captured.seq);
    setAttempt(captured);
    try {
      await linkOwnerAlias(captured.relationshipId, captured.owner);
    } catch (error) {
      const result = linkResult(error);
      setAttempt((current) => same(current) ? { ...captured, ...result } : current);
      if (result.status === "missing" || result.status === "forbidden") {
        readSeq.current += 1;
        setSelected(null);
      }
      return;
    }
    // The write is acknowledged; a failed read after it does not undo that.
    setAttempt((current) => same(current) ? { ...captured, status: "linked" } : current);
    setSelected(null);
    const fresh = await load(true);
    if (!fresh) setAttempt((current) => same(current) ? { ...current!, refreshFailed: true } : current);
  }, [load, openGen, projectId]);

  if (!prep) return null;
  // Nothing named, nothing to say: absent (UX-CANON A.8). A ledger state
  // is only a gap when someone is named.
  if (prep.expected === 0 && prep.people.length === 0) return null;

  const gapTokens = peopleGapTokens(prep);
  const verb = headVerbLabel(prep.state);
  const shown = attempt && attempt.projectId === projectId ? attempt : null;
  // Current attribution of the captured commitments, from THIS Room read.
  const attributed = shown && shown.status !== "pending"
    ? (prep.people.find((p) => p.relationship_id === shown.relationshipId)?.commitments ?? [])
      .filter((c) => shown.commitmentIds.includes(c.id)).length
    : 0;
  const attemptNotice = shown && shown.status !== "pending" ? (
    <div data-testid="room-people-link-result" data-status={shown.status}>
      <ActionNotice
        tone={shown.status === "linked" || shown.status === "current" ? (shown.refreshFailed ? "warn" : "ok") : "warn"}
        role={shown.status === "linked" || shown.status === "current" ? "status" : "alert"}
        action={shown.status === "uncertain" || shown.refreshFailed ? { label: "Check", onClick: check } : undefined}
      >
        {[
          attemptWords(shown),
          shown.refreshFailed ? "Could not read the Room again." : "",
          attributed ? `${(countToken(attributed, "COMMITMENT", "COMMITMENTS") ?? "").toLowerCase()} now with ${shown.personLabel}.` : "",
        ].filter(Boolean).join(" ")}
      </ActionNotice>
    </div>
  ) : null;

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
        {attemptNotice}
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
                      <Token className="surface-token room-people-tok">{openCount}</Token>
                    ) : null}
                    {tokens.prsWaiting ? (
                      <Token className="surface-token room-people-tok">
                        {tokens.prsWaiting}
                      </Token>
                    ) : null}
                    {tokens.assignmentsOverdue ? (
                      <Token className="surface-token room-people-tok room-people-overdue" data-tone="fail">
                        {tokens.assignmentsOverdue}
                      </Token>
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
                    <DotWord
                      tone={row.link === "ambiguous" || row.link === "not_linked" ? "warn" : "fail"}
                      data-testid="room-people-owner-token"
                    >
                      {token}
                    </DotWord>
                    {openCount ? (
                      <Token className="surface-token room-people-tok">{openCount}</Token>
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
                        setSelected(null);
                        setOpenGen((gen) => gen + 1);
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
                    read={wellRead && wellRead.key === wellKey ? wellRead : null}
                    selectedId={selected && selected.key === wellKey ? selected.id : null}
                    linking={Boolean(shown && shown.status === "pending" && shown.owner === row.owner)}
                    linkBlocked={Boolean(shown && shown.owner === row.owner && shown.openGen === openGen
                      && (shown.status === "pending" || shown.status === "uncertain"))}
                    onSelect={(id) => setSelected(id ? { key: wellKey, id } : null)}
                    onLink={(id, label) => void link(row, id, label)}
                    onCancel={() => setSelected(null)}
                    onCheck={check}
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
