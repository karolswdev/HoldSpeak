/** Betterment A5 — About: the one picker (PLAN §2: "About" is the same
 * picker in Ask, Thread and Automations).
 *
 * He types part of a name; the picker finds meetings, notes, drawers,
 * projects and people by name, plus the relative sets ("This week's
 * meetings"). The ranking is the palette's own (`rankRow`), so a name is
 * found here as it is found by Search. A press adds the pick; the typed
 * text stays (it is never deleted), so he can add the next one. Enter adds
 * the top match.
 *
 * The host owns what a pick means: the automation stores its ref as a
 * source; Ask reads it into the question's grounding. */
import "./about.css";
import { useMemo, useState, type KeyboardEvent } from "react";
import type { Items } from "../../api";
import { qualifiedRef } from "../../api";
import { rankRow } from "../../searchRank";
import { StringGadget } from "../../surface/gadgets";
import { Button } from "../../../components/signal/Signal";

export type AboutKind = "set" | "meeting" | "note" | "zone" | "project" | "person" | string;

export interface AboutCandidate {
  /** What is stored: `note:<id>`, `zone:<id>`, `person:<id>`, `meetings:this_week`. */
  ref: string;
  kind: AboutKind;
  /** The name he reads on the chip. */
  label: string;
  /** More words that find it (a drawer's own name, a meeting's people). */
  terms?: string;
  /** When it happened or last changed (ISO): a group lists newest first. */
  at?: string;
  /** Betterment Q6: offered before he types (each person, each project). */
  shortcut?: boolean;
}

/** The relative sets (the hub reads them when a run starts). */
export const ABOUT_SETS: AboutCandidate[] = [
  { ref: "meetings:this_week", kind: "set", label: "This week's meetings", terms: "meetings week recent" },
  { ref: "notes:this_week", kind: "set", label: "This week's notes", terms: "notes week recent" },
];

const KIND_WORD: Record<string, string> = {
  set: "Set",
  meeting: "Meeting",
  note: "Note",
  zone: "Drawer",
  project: "Project",
  person: "Person",
  artifact: "Result",
  decision: "Decision",
};

export function aboutKindWord(kind: string): string {
  return KIND_WORD[kind] ?? "Item";
}

/** Everything About can find on this desk, by name. */
export function aboutCandidates(
  items: Partial<Items>,
  people: Array<{ id: string; name: string }> = [],
): AboutCandidate[] {
  const out: AboutCandidate[] = [...ABOUT_SETS];
  for (const zone of items.directory ?? []) {
    if (!zone.name) continue;
    out.push({ ref: qualifiedRef("directory", zone.id), kind: "zone", label: `Notes in ${zone.name}`, terms: zone.name });
  }
  // Betterment Q10: a knowledge collection is a drawer, found by its name.
  for (const kb of items.kb ?? []) {
    if (!kb.name?.trim()) continue;
    out.push({ ref: qualifiedRef("kb", kb.id), kind: "zone", label: kb.name, terms: `${kb.name} drawer` });
  }
  for (const meeting of items.meeting ?? []) {
    // Betterment Q6: a meeting is found by the people in it, too ("Mira").
    const people = (meeting.attendees ?? []).filter((name) => typeof name === "string").join(" ");
    out.push({
      ref: qualifiedRef("meeting", meeting.id), kind: "meeting", label: meeting.title || "Meeting with no title",
      terms: people || undefined, at: meeting.startedAt || undefined,
    });
  }
  for (const note of items.note ?? []) {
    out.push({ ref: qualifiedRef("note", note.id), kind: "note", label: note.title || "Untitled note", at: note.createdAt || undefined });
  }
  for (const project of items.project ?? []) {
    out.push({ ref: qualifiedRef("project", project.id), kind: "project", label: project.name || "Project" });
  }
  for (const person of people) {
    if (person.name) out.push({ ref: `person:${person.id}`, kind: "person", label: person.name });
  }
  return out;
}

/** The matches for `query`: the best `limit` by the palette's ranking, then
 *  grouped by kind (the group of the best match first) and, inside a group,
 *  newest first (Betterment Q6). An empty query offers the shortcuts: the
 *  relative sets, and each candidate marked `shortcut`. */
export function aboutMatches(candidates: AboutCandidate[], query: string, limit = 8): AboutCandidate[] {
  const asked = query.trim().toLocaleLowerCase();
  if (!asked) return candidates.filter((c) => c.kind === "set" || c.shortcut).slice(0, Math.max(limit, 12));
  const best = candidates
    .map((candidate, index) => ({
      candidate,
      index,
      score: rankRow({ label: candidate.label, terms: candidate.terms }, asked, false),
    }))
    .filter((row) => row.score > 0)
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .slice(0, limit);
  const groups = new Map<string, typeof best>();
  for (const row of best) {
    const group = groups.get(row.candidate.kind);
    if (group) group.push(row);
    else groups.set(row.candidate.kind, [row]);
  }
  const newest = (a: (typeof best)[number], b: (typeof best)[number]) => {
    const at = String(b.candidate.at ?? "").localeCompare(String(a.candidate.at ?? ""));
    return at || b.score - a.score || a.index - b.index;
  };
  return [...groups.values()].flatMap((group) => [...group].sort(newest)).map((row) => row.candidate);
}

export function AboutPicker({
  candidates,
  picked,
  onPick,
  label = "Find by name",
  busy = false,
}: {
  candidates: AboutCandidate[];
  /** The refs already chosen (shown as added, not offered twice). */
  picked: readonly string[];
  onPick: (candidate: AboutCandidate) => void;
  label?: string;
  busy?: boolean;
}) {
  const [query, setQuery] = useState("");
  const matches = useMemo(() => aboutMatches(candidates, query), [candidates, query]);
  const chosen = new Set(picked);
  const top = matches.find((m) => !chosen.has(m.ref));

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== "Enter" || !top || busy) return;
    event.preventDefault();
    onPick(top);
  };

  return (
    <div className="about-picker" data-testid="about-picker">
      <StringGadget
        label={label}
        value={query}
        onChange={setQuery}
        onKeyDown={onKeyDown}
        placeholder="Type a name: a meeting, note, drawer, project or person"
        autoFocus
      />
      {matches.length ? (
        <ul className="about-matches" aria-label="Matches">
          {matches.map((match) => {
            const added = chosen.has(match.ref);
            return (
              <li key={match.ref} className="about-match">
                <Button
                  dense
                  variant="ghost"
                  className="about-match-press"
                  disabled={added || busy}
                  onClick={() => onPick(match)}
                  aria-label={added ? `${match.label} (added)` : `Add ${match.label}`}
                  data-testid="about-match"
                >
                  <span className="about-match-name">{match.label}</span>
                  <span className="about-match-kind">{added ? "Added" : aboutKindWord(match.kind)}</span>
                </Button>
              </li>
            );
          })}
        </ul>
      ) : query.trim() ? (
        <p className="about-none">Nothing on this desk has that name</p>
      ) : null}
    </div>
  );
}
