import { RoomList, type RoomEntry } from "./RoomList";
import { CycleGadget, PaneInspector, InspectorForm, InspectorFacts } from "../../desk/surface";
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
  const [pickedPerson, setPickedPerson] = useState<string | null>(null);
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

  const shown = attempt && attempt.projectId === projectId ? attempt : null;
  const person = prep?.people.find(row => row.relationship_id === pickedPerson);
  const current = wellRead?.key === wellKey && wellRead.status === "ready";
  const candidates = openRow?.candidates ?? [];
  const chosen = selected?.key === wellKey ? selected.id : "";
  const clear = current ? distinguishableCandidates(candidates, wellRead.byId) : new Set<string>();
  const chosenContext = wellRead?.byId[chosen];
  const label = chosenContext ? candidateLabel(chosenContext) : candidates.find(row => row.relationship_id === chosen)?.display_name || "";
  const blocked = Boolean(shown && ["pending", "uncertain", "missing", "forbidden"].includes(shown.status));
  const rows: RoomEntry[] = [
    ...(prep?.people ?? []).map(row => ({ id: row.relationship_id, name: row.display_name, kind: "person", kindWord: "Person", facts: [
      ...row.commitments.map(commitment => ({ key: commitment.id, label: "Owes", value: commitment.text + (commitment.due_at ? ` · ${commitment.due_at}` : "") })),
      ...row.facts.map((fact, i) => ({ key: `fact:${i}`, label: fact.source.label, value: factToken(fact) })),
      ...(row.omitted_sources ?? []).map((source, i) => ({ key: `omitted:${i}`, label: source.label, value: source.state })),
    ], open: () => openPerson(row.relationship_id) })),
    ...(prep?.unresolved ?? []).map(row => ({ id: `owner:${row.owner}`, name: row.owner, kind: "person", kindWord: "Owner", cells: { state: ownerToken(row) }, facts: row.commitments.map(commitment => ({ key: commitment.id, label: "Owes", value: commitment.text })), open: () => { setOpenOwner(row.owner); setOpenGen(value => value + 1); } })),
  ];
  return <RoomList label="People" rows={rows} selectedId={pickedPerson} onSelect={id => { setPickedPerson(id); setOpenOwner(id.startsWith("owner:") ? id.slice(6) : null); setOpenGen(value => value + 1); }}
    loading={!prep} error={prep?.state === "unavailable" ? "Could not read the people · Nothing changed · Try again" : undefined} retry={check} empty="No people linked"
    verbs={[
      { id: "people", label: prep?.state === "ready" ? "People" : headVerbLabel(prep?.state ?? "unavailable"), run: () => openPeople() },
      { id: "check", label: "Check", run: check },
      { id: "inspect", label: "Inspect", enabled: () => Boolean(chosen), run: () => { if (chosen) openPerson(chosen); } },
      ...(person?.commitments ?? []).map(commitment => ({ id: `source:${commitment.id}`, label: `Open source: ${commitment.source.label}`, run: () => openPrimitive(`meeting:${commitment.source.meeting_id}`) })),
    ]}>
    {openRow ? <PaneInspector label={`Link ${openRow.owner}`}><InspectorForm rows={[
      { label: "Person", control: <CycleGadget roster label="Person" value={chosen} options={[{ value: "", label: "Choose a person" }, ...candidates.map(candidate => ({ value: candidate.relationship_id, label: wellRead?.byId[candidate.relationship_id] ? candidateLabel(wellRead.byId[candidate.relationship_id]) : candidate.display_name }))]} onChange={id => setSelected({ key: wellKey, id })} /> },
      { label: "Applies to", control: `Every owner named "${openRow.owner}", in all projects` },
      { label: "State", control: !current ? wellRead?.status === "failed" ? "Could not read the candidates · Nothing changed · Try again" : "Reading candidates" : chosen && !clear.has(chosen) ? "Another match has the same details · Inspect the person" : "" },
      { label: "Result", control: shown ? attemptWords(shown) : "" },
    ]} completion={{ cancel: () => setOpenOwner(null), primary: { label: "Link", disabled: !chosen || !clear.has(chosen) || !current || blocked, busy: shown?.status === "pending", run: () => { void link(openRow, chosen, label); } } }} /></PaneInspector> : shown ? <InspectorFacts name="Link result" rows={[{ label: "Result", value: attemptWords(shown) }, { label: "Read", value: shown.refreshFailed ? "Could not read the Room again · Nothing changed · Try again" : "" }]} data-feedback-redact="true" /> : undefined}
  </RoomList>;
}
